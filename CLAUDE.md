# CLAUDE.md — RelatPadrao / AZ Resultados

## Identidade do projeto

Projeto de construção do **Modelo Padrão de Relatórios AZ Resultados** (ETL Python + workbook Excel).
Cliente ativo: **AB Aeterno**.

## Fontes de verdade

| Arquivo | Papel |
|---|---|
| `SDD/SRS_RegrasRelatPadrao.md` | **Regras universais** — fonte de verdade corrente |
| `assets/cad_clientes/cad_cliente_AB.md` | **Configuração AB Aeterno** — fonte de verdade do cliente |
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
├── tests/                      # Suite de testes automatizados (pytest)
│   ├── conftest.py             # Setup de path e fixtures compartilhadas
│   ├── test_etl.py             # Testes unitários das funções ETL
│   └── test_workbook.py        # Testes de integração no xlsx gerado
├── assets/                     # Recursos e dados de entrada do projeto
│   ├── logo/                   # Logotipo AZ (usado em todas as abas do workbook)
│   ├── cad_clientes/           # Cadastro de configuração por cliente
│   │   ├── cad_cliente_AB.md   # Documentação do cliente (humano)
│   │   ├── cad_cliente_AB.json # Contrato máquina do cliente (lido pelo ETL)
│   │   └── cad_cliente_*.md    # Demais clientes (ES, GCG, LA, OS)
│   └── Piloto/ABAeterno/       # Arquivos de dados do cliente AB
│       ├── f_Lctos_2023_2026_proj.xlsx
│       ├── AB_MapaAloc_v11 - Atual utilizado na AB.xlsx
│       └── ABRelatório_Financeiro_202604abr_V2.1.xlsx  # Referência — não replicar
├── relatorios/                 # Arquivos xlsx gerados pelo ETL (output)
├── _old/                       # Scripts auxiliares inativos (inspeção, patch, verify)
├── requirements.txt            # Dependências Python (pip install -r requirements.txt)
├── ROADMAP.md                  # Visão estratégica de médio e longo prazo
├── CHANGELOG.md                # Histórico de versões e bugs resolvidos
└── .claude/
    └── settings.local.json
```

## Cliente AB Aeterno — configuração rápida

> Fonte autoritativa: `assets/cad_clientes/cad_cliente_AB.md`

- **BUs:** `Ab Aeterno | Da Una Vita | Holding`
- **`mes_corte_realizado`:** `2026-05`
- **MapaAloc:** `AB_MapaAloc_v11` — 94 categorias
- **Eixos secundários:** nenhum — `d_Calendario` e `d_Feriados` **não se aplicam** ao AB
- **Arquivo de entrega:** `relatorios/{SIGLA}_RelatFinanceiro_{YYYYMMDDHHMM}.xlsx`

### Abas do relatório gerado

`DRE Gerencial` · `DFC` · `KPIs` · `f_Base` · `Lista` · `f_Erros` · `f_SaldoBancos` · `cad_cliente` · `check`

## Guardrails de implementação

> Resumo rápido — fonte autoritativa: `SDD/SRS_RegrasRelatPadrao.md` §6.

- **`_sem_mapa`:** linha fica na `f_Base` **e** vai para `f_Erros` — nunca excluir
- **`f_SaldoBancos`:** nunca sobrescrever dados reais; seed só na primeira carga
- **Fallback saldo ausente:** `saldo_inicial = 0` + registro em `f_Erros` — nunca `#N/D`
- **Corte Realizado×Projeção:** responsabilidade do SUMIFS — ETL não poda dados
- **Seletores:** sempre por Defined Name, nunca endereço fixo
- **KPIs:** leem `f_Base` direto — nunca o relatório-fim (DRE/DFC)
- **Erros técnicos:** vão **só** para `f_Erros`, não entram na `f_Base`

## Decisões de código travadas

- **`_suppress_formula_errors()` (`writer.py`) — DESATIVADA:** causou erro na abertura do arquivo Excel quando acionada; função existe no código mas não é chamada — não reativar sem teste.

## Pendências AB ativas

- `f_SaldoBancos`: seed aplicado (Holding PJ/PF, 31/12/2022, valor 0) — preencher com saldos reais para DFC funcional; James fecha em paralelo
- Diferença numérica fonte vs controle manual → fora de escopo; entregar com ressalva; James fecha em paralelo

## Roadmap

Ver `ROADMAP.md` na raiz do repositório.
