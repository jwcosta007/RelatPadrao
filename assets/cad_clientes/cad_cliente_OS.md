# Cadastro de Cliente — OS (Santé)
*Versão 01 — 19/jun/2026*

> ⚠️ **Campos marcados como `[A PREENCHER]` devem ser preenchidos antes de qualquer
> processamento de dados deste cliente.**

---

## 1. Identificação e configuração (`cad_cliente`)

| Grupo | Campo | Valor |
|---|---|---|
| Identificação | `codigo` | `OS` |
| | `nome` | `[A PREENCHER]` *(Santé)* |
| | `segmento_cliente` | `[A PREENCHER]` |
| | `status` | `[A PREENCHER]` |
| Origem de dados | `origem_dados_realizado` | `[A PREENCHER]` |
| | `erp_nome` | `[A PREENCHER]` |
| | `path_lctos_tipo` | `[A PREENCHER]` |
| | `path_lctos` | `[A PREENCHER]` |
| | `path_apoio` | `[A PREENCHER]` |
| Staging | `staging_mapa_fonte` | `[A PREENCHER]` |
| | `fingerprint_aplicavel` | `[A PREENCHER]` |
| | `conversao_defensiva_valor` | `[A PREENCHER]` |
| BU | `bu_aplicavel` | `Sim` |
| | `bu_origem` | `grupo_categorias_mapaaloc` |
| | `bu_regra` | Cada BU tem grupo próprio de contas/categorias no MapaAloc. BU derivada da conta do lançamento via MapaAloc. |
| | `bu_valores_validos` | `[A PREENCHER]` |
| Colunas condicionais | `tem_data_competencia` | `[A PREENCHER]` |
| | `tem_data_vencimento` | `[A PREENCHER]` |
| | `tem_valor_original` | `[A PREENCHER]` |
| | `tem_documento` | `[A PREENCHER]` |
| | `tem_conta_bancaria` | `[A PREENCHER]` |
| Projeção | `mes_corte_realizado` | `[A PREENCHER]` |
| | `reforecast_vigente_ref` | `[A PREENCHER]` |
| MapaAloc | `mapaaloc_arquivo` | `[A PREENCHER]` |
| | `mapaaloc_versao` | `[A PREENCHER]` |
| Moeda | `moeda` | `[A PREENCHER]` |
| Doc | `doc_especifico` | `[A PREENCHER]` |

---

## 2. Shape da `f_Base` — OS

| Bloco | Qtd | Detalhe |
|---|---|---|
| Núcleo universal | 23 | Padrão AZ |
| Condicionais ligadas | `[A PREENCHER]` | |
| KPIs vivos | `[A PREENCHER]` | Derivado do MapaAloc da OS |
| **Total** | `[A PREENCHER]` | |

---

## 3. Pendências conhecidas

| Item | Descrição |
|---|---|
| Código ETL do padrão | Staging para OS pendente de implementação |
| MapaAloc | `[A CRIAR]` — seguir estrutura v13 (25 colunas, 5 blocos) |
| Arquivo de inspiração | `Modelo_Inspiracao_DRE_KPIs.xlsx` foi a origem do design padrão AZ. Não recarregar para novos clientes sem verificar o que é específico da OS. KPIs específicos (Ticket Médio, Qtde Contratos, Distratos) não devem ser portados sem confirmação da nova fonte. |

---

*Versão 01 — 19/jun/2026*
*Preencher todos os campos [A PREENCHER] antes de processar dados da OS.*
