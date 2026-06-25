# RelatPadrao — Modelo Padrão de Relatórios AZ Resultados

ETL Python que gera workbooks Excel padronizados (DRE Gerencial, DFC, KPIs) a partir de lançamentos financeiros e de um MapaAloc configurado por cliente.

---

## Pré-requisitos

- Python 3.10+
- Dependências:

```bash
pip install pandas openpyxl python-dateutil Pillow
```

---

## Estrutura do projeto

```
RelatPadrao/
├── SDD/                        # Especificação e design (fonte de verdade)
│   ├── RegrasRelatPadrao_v20.md    # Regras universais — ler antes de implementar
│   └── DesignDoc_Relatorio_v5.md   # Paleta de cores e hierarquia visual
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

O arquivo de saída é gerado em `relatorios/AB_Relatorio_v1.xlsx`.

---

## Configuração de cliente

Cada cliente tem um cadastro em `assets/cad_clientes/cad_cliente_<CODIGO>v<N>.md` com:
- BUs válidas, `mes_corte_realizado`, colunas condicionais ativas
- Referência ao arquivo MapaAloc e fonte de lançamentos

O ETL lê esses parâmetros como config hardcoded no `etl_<codigo>.py` correspondente.  
Detalhes do contrato de dados em `SDD/RegrasRelatPadrao_v20.md`.

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
