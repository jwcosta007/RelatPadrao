# RelatPadrao — Modelo Padrão de Relatórios AZ Resultados

ETL Python que gera workbooks Excel padronizados (DRE Gerencial, DFC, KPIs) a partir de lançamentos financeiros e de um MapaAloc configurado por cliente.

---

## Pré-requisitos

- Python 3.10+
- Dependências:

```bash
pip install -r requirements.txt
```

---

## Estrutura do projeto

```
RelatPadrao/
├── SDD/                        # Especificação e design (fonte de verdade)
│   ├── SRS_RegrasRelatPadrao.md    # Regras universais — ler antes de implementar
│   └── DesignDoc_Relatorio.md   # Paleta de cores e hierarquia visual
├── pipeline/                   # Módulos Python do ETL
│   ├── etl.py                  # Entry point: python etl.py <CODIGO>
│   ├── staging.py              # Staging universal (validação, JOIN MapaAloc, enriquecimento)
│   ├── loader.py               # Leitura de MapaAloc e f_SaldoBancos
│   ├── builder.py              # Geração do workbook (DRE, DFC, KPIs, seletores)
│   ├── writer.py               # Escrita e salvamento do arquivo Excel
│   └── extractors/             # Extratores por cliente/formato de origem
│       └── extractor_ab.py     # Lê e normaliza dados AB Aeterno (Excel)
├── assets/                     # Recursos e dados de entrada
│   ├── logo/                   # Logotipo AZ Resultados
│   ├── cad_clientes/           # Configuração por cliente (*.md)
│   └── dados/                      # Dados de entrada por cliente (não versionados)
│       ├── AB - AB Aeterno/AB_MapaAloc.xlsx
│       ├── AB - AB Aeterno/f_Lctos/
│       └── GCG - GCG Clinica/      (estrutura idêntica)
├── relatorios/                 # Output gerado pelo ETL (não versionado)
├── _old/                       # Scripts auxiliares inativos
└── CLAUDE.md                   # Instruções para o assistente de código
```

---

## Como executar

```bash
python pipeline/etl.py AB
```

O arquivo de saída é gerado em `relatorios/` com o nome `{SIGLA}_RelatFinanceiro_{YYYYMMDDHHMM}.xlsx`.
Exemplo: `AB_RelatFinanceiro_202606250054.xlsx`.

## Como rodar os testes

```bash
python -m pytest tests/ -v
```

- `tests/test_staging.py` — 28 testes unitários (não requerem dados reais)
- `tests/test_workbook.py` — 13 testes de integração (requerem xlsx em `relatorios/`)

---

## Configuração de cliente

Cada cliente tem um cadastro em `assets/cad_clientes/cad_cliente_<CODIGO>v<N>.md` com:
- BUs válidas, `mes_corte_realizado`, colunas condicionais ativas
- Referência ao arquivo MapaAloc e fonte de lançamentos

O ETL lê esses parâmetros do `cad_cliente_<CODIGO>.json` em runtime.
Detalhes do contrato de dados em `SDD/SRS_RegrasRelatPadrao.md`.

---

## Como adicionar um novo cliente

**1. Criar o cadastro do cliente**

Copie `assets/cad_clientes/cad_cliente_AB.md` como ponto de partida e salve como
`assets/cad_clientes/cad_cliente_<CODIGO>.md`. Preencha todos os campos da §1
(BUs, `mes_corte_realizado`, condicionais, MapaAloc, etc.).

Crie também `assets/cad_clientes/cad_cliente_<CODIGO>.json` — contrato máquina lido
pelo ETL em runtime. Use `cad_cliente_AB.json` como modelo. Chaves obrigatórias:

```json
{
  "codigo": "XX", "nome": "Nome do Cliente", "segmento_cliente": "...", "status": "Ativo",
  "origem_dados_realizado": "...",
  "bu_origem": "f_Lctos_direto",
  "bu_validos": ["BU 1", "BU 2"],
  "tipo_reg_validos": ["Realizado", "Orçado", "Reforecast"],
  "mapa_fonte": { "Realizado": "Dados Oficiais", "Orçado": "Orçamento", "Reforecast": "Reforecast" },
  "tem_conta_bancaria": false, "tem_fornecedor_cliente": false,
  "mes_corte_realizado": "AAAA-MM",
  "mapaaloc_arquivo": "XX_MapaAloc.xlsx", "moeda": "BRL",
  "saldo_seed": [{ "data": "AAAA-MM-DD", "BU": "<BU>", "nome_conta": "<conta>", "valor": 0 }],
  "dre_cascade": [
    { "n1_names": ["N1_A", "N1_B"], "kpi_label": "NOME KPI", "is_roxo": false },
    { "n1_names": ["N1_C"], "kpi_label": "RESULTADO INVESTIDORES", "is_roxo": true }
  ]
}
```

> Paths não entram no JSON — o ETL os deriva por convenção: `assets/dados/{SIGLA} - {Nome}/{SIGLA}_MapaAloc.xlsx` e `assets/dados/{SIGLA} - {Nome}/f_Lctos/`. Ver SRS §4.4.

**2. Preparar os dados de entrada**

Crie a pasta `assets/dados/{SIGLA} - {Nome}/` e coloque:
- `{SIGLA}_MapaAloc.xlsx` na raiz da pasta (sem versão no nome — SRS §4.4)
- Arquivo(s) de lançamentos na subpasta `f_Lctos/` — estrutura de 25 colunas conforme `SDD/SRS_RegrasRelatPadrao.md` §2

**3. Criar o extrator do cliente**

Crie `pipeline/extractors/extractor_<codigo>.py` com a função:

```python
def load(folder: Path, cfg: dict) -> tuple[pd.DataFrame, list[dict]]:
    # lê todos os arquivos em folder (f_Lctos/), concatena e retorna:
    #   - DataFrame com colunas: data_caixa, historico, categoria, valor, bu,
    #     tipo_registro + condicionais ativas (conta_bancaria, etc.)
    #   - lista de erros de leitura (formato f_Erros) para arquivos não legíveis
```

Use `extractor_ab.py` como referência. Toda lógica específica do formato da fonte fica aqui.
Arquivos não legíveis geram entrada em `f_Erros` sem travar o processo.

**4. Executar e verificar**

```bash
python pipeline/etl.py <CODIGO>
```

Verificar no relatório gerado (`relatorios/<CODIGO>_RelatFinanceiro_*.xlsx`):
- `f_Erros` vazia (0 ocorrências)
- `_sem_mapa = 0` (todas as categorias mapeadas)
- Abas DRE e DFC populadas com hierarquia correta

---

## Abas geradas

| Aba | Conteúdo |
|---|---|
| `DRE Gerencial` | Demonstração de Resultado com hierarquia N1/N2/N3 e KPIs |
| `DFC` | Demonstração de Fluxo de Caixa — Resumo + Detalhe |
| `KPIs` | Receita Líquida com gráfico de colunas |
| `f_Base` | Tabela de lançamentos enriquecida (34 colunas AB) |
| `Lista` | Fonte das validações de dados dos seletores |
| `f_Erros` | Erros técnicos e lançamentos sem mapa |
| `f_SaldoBancos` | Saldos de abertura (preenchimento manual) |
| `cad_cliente` | Configuração do cliente |
| `check` | Validações de integridade (pendente implementação) |

---

## Notas importantes

- **`f_SaldoBancos`** é preenchida manualmente — o ETL preserva dados existentes e aplica seed apenas na primeira carga.
- **`_sem_mapa`**: lançamentos sem correspondência no MapaAloc entram na `f_Base` e em `f_Erros` — nunca são descartados.
- O corte Realizado×Projeção é responsabilidade dos SUMIFS do workbook, não do ETL.
