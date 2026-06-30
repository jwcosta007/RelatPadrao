# Resposta à Avaliação Deepseek — RelatPadrao / AZ Resultados

> Documento produzido após ciclo de implementação iniciado em 25/jun/2026 e encerrado em 30/jun/2026.
> Referência: `SDD/Avaliação Deepseek.md`.

---

## 1. O que foi implementado

### ✅ Resolvidos da lista de sugestões

| Sugestão original | Status | Notas |
|---|---|---|
| Remover `_suppress_formula_errors` (código morto) | ✅ Removido | `writer.py` ficou com 3 funções simples |
| Substituir / documentar `patch_kpi_chart` | ✅ Extraído para `charts.py` | Ver §2 — ZIP patch mantido intencionalmente |
| Melhorar tratamento de exceções I/O | ✅ Implementado | `loader.load_mapaaloc`, `writer.save`, `charts._patch_zip` e `extractor_ab.load` com catches específicos |
| Validar colunas esperadas no extrator | ✅ Implementado | `extractor_ab.py` valida `_OUT_COLS` após renomeação; erro vai para `f_Erros` |
| Substituir `print` por `logging` | ✅ Implementado | `etl.py` e `loader.py`; `basicConfig` em `main()`, `format="%(message)s"`, `stream=sys.stdout` — output visual idêntico ao anterior |
| Validação de schema JSON (pydantic) | ✅ Implementado | `_CadClienteConfig` + `_DreCascadeEntry` substituem `_REQUIRED_KEYS` + `_validate_cfg()` manual; mensagens de erro apontam o campo exato (ex: `dre_cascade → 0 → n1_names: field required`) |

### Outros ajustes não listados na avaliação

- **Arquitetura de dados por convenção:** eliminamos `path_mapa` e `path_lctos` do JSON. O ETL deriva os caminhos a partir de `codigo` + `nome` — `assets/dados/{SIGLA} - {Nome}/{SIGLA}_MapaAloc.xlsx` e `f_Lctos/`. Zero configuração redundante.
- **Versionamento de arquivos:** todos os nomes ativos removidos de versão (`AB_MapaAloc_v11.xlsx` → `AB_MapaAloc.xlsx`; documentos `.md` idem). Git é o histórico; versões antigas vão para `_old/`.
- **Verificação N3-único antes da carga:** `staging.check_mapa_n3_unico()` bloqueia a execução se `dre_n3` ou `dfc_n3` não forem únicos no MapaAloc. ETL para com erro claro.
- **Limpeza geral de referências:** CLAUDE.md, README.md, SRS, `cad_cliente_*.md` auditados e atualizados para refletir a estrutura real.

---

## 2. O que não concordamos (e por quê)

### 2.1 ZIP patch em `charts.py` — mantido, não substituído

A avaliação sugeriu substituir `patch_kpi_chart` pela API openpyxl. Avaliamos ponto a ponto:

| Customização necessária | Suporte openpyxl |
|---|---|
| Tipografia de rótulos de dados (bold, 9pt) | `DataLabelList.txPr` existe mas não serializa corretamente |
| Tipografia do eixo X (bold 8pt) | Não exposta via API |
| `lang="pt-BR"` nos elementos `<a:r>` | Não exposta |
| Fundo transparente da área de plotagem | Parcial, inconsistente |
| Borda externa do gráfico (cor + peso) | Suporte parcial |

Decisão: **ZIP patch é a abordagem correta** — é determinístico, testado e não depende de comportamento interno do openpyxl. O risco apontado (fragilidade) foi mitigado com:
- Extração para `charts.py` (módulo dedicado)
- `_patch_zip()` agora faz raise após cleanup do `.tmp`
- Comentário no módulo documenta o padrão para futuros gráficos
- Todos os futuros `chart{n}.xml` usarão o mesmo padrão

### 2.2 Factories e injeção de dependência para o builder

A avaliação citou "injeção de dependências implícita" como dificultador de testes unitários do builder. Não implementamos factories por razões práticas:

- O projeto tem um desenvolvedor executando o ETL mensalmente
- Os testes de integração (`test_workbook.py`) cobrem o workbook gerado diretamente — mais próximo do real do que mocks
- O overhead de factories seria maior que o benefício para o escopo atual
- Quando o `builder.py` for dividido (roadmap §1), os módulos resultantes serão naturalmente mais testáveis sem necessidade de factories

### 2.3 `extra="allow"` no schema pydantic

A avaliação não cobriu esse ponto, mas vale registrar: usamos `extra="allow"` nos modelos pydantic para que campos opcionais do JSON (`saldo_seed`, `reforecast_vigente_ref`, `moeda`, etc.) não quebrem a validação. O modelo valida o que é obrigatório e deixa o resto fluir como `cfg["key"]` no código existente — sem reescrita da camada de consumo.

---

## 3. O que ficou no roadmap

| # | Prioridade | Pendência | Origem |
|---|---|---|---|
| 1 | Alta | Dividir `builder.py` (~1084 linhas) em módulos menores + `styles.py` | Deepseek §1 + §7 |
| 2 | Média | Refatorar `_write_items` — cadeia `if t ==` → dicionário de handlers | Deepseek §2 + §7 |
| 3 | Baixa | Type hints completas com `pandas-stubs` | Deepseek §2 + §7 |

Itens de negócio que ficaram no roadmap (fora do escopo da avaliação Deepseek):
- Aba `check` com fórmulas de validação cruzada (Realizado×Projeção, f_Erros, saldo DFC)
- Implantação GCG Clínica (`extractor_gcg.py` + `cad_cliente_GCG.json`)
- Frente Projeções/Forecast (§10 do SRS)

---

## 4. Estrutura atual de pastas

```
RelatPadrao/
├── SDD/
│   ├── SRS_RegrasRelatPadrao.md       # Regras universais — fonte de verdade
│   ├── DesignDoc_Relatorio.md         # Paleta de cores e hierarquia visual
│   ├── Avaliação Deepseek.md          # Avaliação original
│   └── Resposta_ao_Deepseek.md        # Este documento
│
├── pipeline/
│   ├── etl.py                         # Entry point: python etl.py <CODIGO>
│   ├── staging.py                     # Validação, JOIN MapaAloc, enriquecimento
│   ├── loader.py                      # Leitura de MapaAloc e f_SaldoBancos
│   ├── builder.py                     # Geração do workbook (DRE, DFC, KPIs...)  ← dividir
│   ├── charts.py                      # Criação (openpyxl) + patch XML pós-save  ← novo
│   ├── writer.py                      # Escrita e salvamento do workbook
│   └── extractors/
│       └── extractor_ab.py            # Lê e normaliza lançamentos AB Aeterno
│
├── tests/
│   ├── conftest.py
│   ├── test_staging.py                # 28 testes unitários
│   └── test_workbook.py               # 13 testes de integração
│
├── assets/
│   ├── logo/5.png
│   ├── cad_clientes/
│   │   ├── cad_cliente_AB.json        # Contrato máquina (lido pelo ETL)
│   │   ├── cad_cliente_AB.md          # Documentação do cliente
│   │   └── cad_cliente_{GCG,ES,LA,OS}.md
│   └── dados/
│       ├── AB - AB Aeterno/
│       │   ├── AB_MapaAloc.xlsx       # Sem versão no nome (git é o histórico)
│       │   └── f_Lctos/               # Drop zone de arquivos mensais
│       └── GCG - GCG Clinica/         # (estrutura idêntica, em implantação)
│
├── relatorios/                        # Output do ETL (não versionado)
├── _old/                              # Scripts e docs inativos (histórico)
├── CLAUDE.md                          # Instruções para o assistente de desenvolvimento
├── ROADMAP.md                         # Visão estratégica
├── CHANGELOG.md                       # Histórico de versões e bugs
└── requirements.txt                   # pandas, openpyxl, pydantic, pytest...
```

---

## 5. Mudanças de filosofia ocorridas neste ciclo

### 5.1 Convenção sobre configuração

Antes: o JSON de cada cliente precisava de `path_mapa` e `path_lctos` explícitos.
Depois: o ETL deriva os caminhos — `assets/dados/{SIGLA} - {Nome}/` é a convenção. Menos campo para errar, onboarding mais direto.

### 5.2 Git como único controle de versão

Antes: arquivos levavam versão no nome (`AB_MapaAloc_v11.xlsx`, `SRS_RegrasRelatPadrao_v20.md`).
Depois: nomes sem versão. `_old/` guarda snapshots históricos quando necessário. A convenção se aplica a dados, documentos e código igualmente.

### 5.3 Tratamento de exceções cirúrgico, não defensivo

Optamos por catches apenas nos dois pontos de falha previsíveis e não-bug (`loader.load_mapaaloc` e `writer.save`). Nenhum handler global. Erros de código (imports, lógica) devem produzir traceback completo — o desenvolvedor é quem roda o ETL e precisa dessas informações.

### 5.4 Gráficos como módulo próprio

O padrão `charts.py` (two-step: openpyxl API para registrar âncora + ZIP patch para tipografia final) foi estabelecido antes de termos mais de um gráfico. A intenção é que todos os futuros gráficos do relatório sigam o mesmo padrão: `build_<nome>(ws, ...)` + entrada em `patch_charts()`.

---

## 6. Observações adicionais

- **Suite de testes:** a avaliação referenciava 34 testes. Ao final deste ciclo: **41 testes** (28 unitários + 13 integração), todos passando.
- **builder.py:** a avaliação apontou ~650 linhas. Ao final do ciclo: **~1084 linhas** — cresceu porque DRE, DFC, KPIs e seletores foram finalizados. A divisão em módulos menores está no roadmap como item #1 (alta prioridade) e será o primeiro trabalho da próxima sessão.
- **`charts.py` é novo:** não existia na avaliação original. Foi criado neste ciclo para abrigar toda a lógica de gráficos extraída de `writer.py` e `builder.py`.
- **Pydantic com `extra="allow"`:** cobre 100% dos campos obrigatórios e deixa os opcionais fluir sem alteração no código de consumo — evolução incremental sem reescrita.
- **`Avaliação Deepseek.md`:** o arquivo ficou não-rastreado durante o ciclo e foi perdido temporariamente; restaurado de backup. A partir deste documento fica registrado o estado da avaliação + resposta de forma permanente no repositório.
