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
│   ├── etl_ab.py               # Orquestrador — ponto de entrada AB Aeterno
│   ├── loader.py               # Leitura de fontes (MapaAloc, f_Lctos, f_SaldoBancos)
│   ├── builder.py              # Geração do workbook (DRE, DFC, KPIs, seletores)
│   └── writer.py               # Escrita e salvamento do arquivo Excel
├── assets/                     # Recursos e dados de entrada
│   ├── logo/                   # Logotipo AZ Resultados
│   ├── cad_clientes/           # Configuração por cliente (*.md)
│   └── Piloto/ABAeterno/       # Dados do cliente AB Aeterno (não versionados)
├── relatorios/                 # Output gerado pelo ETL (não versionado)
├── _old/                       # Scripts auxiliares inativos
└── CLAUDE.md                   # Instruções para o assistente de código
```

---

## Como executar

```bash
python pipeline/etl_ab.py
```

O arquivo de saída é gerado em `relatorios/` com o nome `{SIGLA}_RelatFinanceiro_{YYYYMMDDHHMM}.xlsx`.
Exemplo: `AB_RelatFinanceiro_202606250054.xlsx`.

---

## Configuração de cliente

Cada cliente tem um cadastro em `assets/cad_clientes/cad_cliente_<CODIGO>v<N>.md` com:
- BUs válidas, `mes_corte_realizado`, colunas condicionais ativas
- Referência ao arquivo MapaAloc e fonte de lançamentos

O ETL lê esses parâmetros como config hardcoded no `etl_<codigo>.py` correspondente.  
Detalhes do contrato de dados em `SDD/SRS_RegrasRelatPadrao.md`.

---

## Como adicionar um novo cliente

**1. Criar o cadastro do cliente**

Copie `assets/cad_clientes/cad_cliente_AB.md` como ponto de partida e salve como
`assets/cad_clientes/cad_cliente_<CODIGO>v01.md`. Preencha todos os campos da §1
(BUs, `mes_corte_realizado`, condicionais, MapaAloc, etc.).

**2. Preparar os dados de entrada**

Crie a pasta `assets/<NomeCliente>/` e coloque:
- Arquivo de lançamentos (`f_Lctos_*.xlsx`)
- Arquivo MapaAloc (`*_MapaAloc_*.xlsx`) — estrutura de 25 colunas conforme `SDD/SRS_RegrasRelatPadrao.md` §2

**3. Criar o orquestrador ETL**

Copie `pipeline/etl_ab.py` como `pipeline/etl_<codigo>.py` e ajuste:

| Seção | O que alterar |
|---|---|
| `PATHS` | `LCTOS_PATH`, `MAPA_PATH` apontando para a pasta do cliente |
| `BU_VALIDOS` | BUs do cliente conforme cadastro |
| `CAD_CONFIG` | Todos os campos do cad_cliente (codigo, nome, BUs, corte, etc.) |
| `DRE_CASCADE` | Cascata de KPIs do DRE — específica por cliente |
| `F_BASE_COLS` | Ajustar se o cliente tiver condicionais diferentes das do AB |
| `F_SALDO_SEED` | Seed de abertura do f_SaldoBancos (BU, conta, data, valor 0) |

**4. Executar e verificar**

```bash
python pipeline/etl_<codigo>.py
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
