# CLAUDE.md — RelatPadrao / AZ Resultados

## Identidade do projeto

Projeto de construção do **Modelo Padrão de Relatórios AZ Resultados** (ETL Python + workbook Excel).
Cliente ativo: **AB Aeterno**.

## Fontes de verdade

| Arquivo | Papel |
|---|---|
| `SDD/RegrasRelatPadrao.md` | **Regras universais** — fonte de verdade corrente |
| `assets/cad_clientes/cad_cliente_ABv03.md` | **Configuração AB Aeterno** — fonte de verdade do cliente (v03) |
| `assets/cad_clientes/*.md` | Cadastro de cada cliente |
| `SDD/DesignDoc_Relatorio.md` | **Paleta de cores e hierarquia visual** — consultar antes de montar DRE/DFC no xlsx |

Os arquivos listados acima são as fontes correntes. Versões anteriores estão em `_old/` como histórico.

## Estrutura de pastas

```
RelatPadrao/
├── SDD/                        # Documentos de regras (fonte de verdade)
├── pipeline/                   # Módulos Python ativos do ETL
│   ├── etl_ab.py               # Orquestrador AB Aeterno
│   ├── loader.py               # Leitura de fontes (MapaAloc, f_Lctos, f_SaldoBancos)
│   ├── builder.py              # Geração de estrutura do workbook (DRE, DFC, KPIs, etc.)
│   └── writer.py               # Escrita/salvamento do workbook Excel
├── assets/                     # Recursos e dados de entrada do projeto
│   ├── logo/                   # Logotipo AZ (usado em todas as abas do workbook)
│   ├── cad_clientes/           # Cadastro de configuração por cliente
│   └── Piloto/ABAeterno/       # Arquivos de dados do cliente AB
│       ├── f_Lctos_2023_2026_proj.xlsx
│       ├── AB_MapaAloc_v11 - Atual utilizado na AB.xlsx
│       └── ABRelatório_Financeiro_202604abr_V2.1.xlsx  # Referência — não replicar
├── relatorios/                 # Arquivos xlsx gerados pelo ETL (output)
├── _old/                       # Scripts auxiliares inativos (inspeção, patch, verify)
└── .claude/
    └── settings.local.json
```

## Cliente AB Aeterno — configuração rápida

- **`f_Base`:** 34 colunas — `23 núcleo + 2 condicionais (conta_bancaria, fornecedor_cliente) + 9 KPIs`
- **BUs:** `Ab Aeterno | Da Una Vita | Holding` (vêm direto da fonte — `bu_origem = f_Lctos_direto`)
- **`mes_corte_realizado`:** `2026-05`
- **MapaAloc:** `AB_MapaAloc_v11` — 94 categorias, N3-único OK
- **Eixos secundários:** nenhum — `d_Calendario` e `d_Feriados` **não se aplicam** ao AB
- **Arquivo de entrega:** `relatorios/{SIGLA}_RelatFinanceiro_{YYYYMMDDHHMM}.xlsx` (ex: `AB_RelatFinanceiro_202606250054.xlsx`)

### Abas do relatório gerado

`DRE Gerencial` · `DFC` · `KPIs` · `f_Base` · `Lista` · `f_Erros` · `f_SaldoBancos` · `cad_cliente` · `check`

## Regras críticas de implementação

- **`_sem_mapa`:** linha fica na `f_Base` (com `dre_n3`/`dfc_n3` = NULL) **e** vai para `f_Erros` — nunca excluir
- **`f_SaldoBancos`:** preenchida manualmente pelo operador; ETL lê dados existentes (preserva), aplica seed na primeira carga (Holding PJ/PF, 31/12/2022) — nunca sobrescreve dados reais
- **Fallback saldo ausente:** `saldo_inicial = 0` + registro em `f_Erros` — nunca `#N/D`
- **Corte Realizado×Projeção:** responsabilidade do SUMIFS (`IF(mes<=sel_MesCorte,"Realizado",sel_Projecao)`) — ETL não poda
- **Intervalos nomeados:** seletores do workbook **sempre** por Defined Name, nunca endereço fixo
- **KPIs leem `f_Base` direto** — nunca o relatório-fim (DRE/DFC)
- **Erros técnicos** (BU fora do domínio, `tipo_registro` desconhecido, falha de conversão): vão **só** para `f_Erros`, não entram na `f_Base`

## Decisões de código travadas

- **`_suppress_formula_errors()` (`writer.py`) — DESATIVADA:** causou erro na abertura do arquivo Excel quando acionada; função existe no código mas não é chamada — não reativar sem teste.

## Pendências AB ativas

- `f_SaldoBancos`: seed aplicado (Holding PJ/PF, 31/12/2022, valor 0) — preencher com saldos reais para DFC funcional; James fecha em paralelo
- Diferença numérica fonte vs controle manual → fora de escopo; entregar com ressalva; James fecha em paralelo

## Roadmap

> Detalhamento completo em `SDD/RegrasRelatPadrao.md` §7.

### Próxima iteração (pós-piloto AB)

- **Aba `check`:** implementar fórmulas §12 (soma KPI vs cascata, `_sem_mapa = 0`, contador `f_Erros`, bate colisão R×P, bate DFC caixa). Design ainda em aberto (v20 §7.1).
- **Demais clientes (ES, GCG, LA, OS):** criar `etl_<codigo>.py` por cliente após validação AB. Cadastros em `assets/cad_clientes/` já existem.
- **`d_Calendario` / `d_Feriados`:** criar somente quando `tem_data_competencia = Sim` ou `tem_data_vencimento = Sim` no `cad_cliente`. AB não usa.

### Médio prazo

- **Frente Projeções/Forecast (§10):** aba O×R com seletores duplos, gráfico FP&A 3 séries, bate colisão na `check`. Design FECHADO em §10; implementação pendente.
- **Gerador de MapaAloc** + **Gerador de DRE/DFC** a partir do MapaAloc.

### Longo prazo / greenfield

- `id_lcto` persistente (chave natural/hash) → migração Python/PostgreSQL.
- Camada 0 plena, conector-por-ERP → backlog greenfield.
