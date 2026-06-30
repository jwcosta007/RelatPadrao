# Cadastro de Cliente — GCG

> ⚠️ **Campos marcados como `[A PREENCHER]` devem ser preenchidos antes de qualquer
> processamento de dados deste cliente.**

---

## 1. Identificação e configuração (`cad_cliente`)

| Grupo | Campo | Valor |
|---|---|---|
| Identificação | `codigo` | `GCG` |
| | `nome` | `[A PREENCHER]` |
| | `segmento_cliente` | `[A PREENCHER]` |
| | `status` | `Ativo` |
| Origem de dados | `origem_dados_realizado` | `[A PREENCHER]` |
| | `erp_nome` | `[A PREENCHER]` |
| | `path_lctos_tipo` | `[A PREENCHER]` |
| | `path_apoio` | `[A PREENCHER]` |
| Staging | `staging_mapa_fonte` | `[A PREENCHER]` |
| | `fingerprint_aplicavel` | `[A PREENCHER]` |
| | `conversao_defensiva_valor` | `[A PREENCHER]` |
| BU | `bu_aplicavel` | `Sim` |
| | `bu_origem` | `de_para_conta_bancaria` |
| | `bu_regra` | De-para conta bancária → BU via `cad_depara_bu`. Nomes CPF/CNPJ nas contas são ruins — renomear. |
| | `bu_valores_validos` | `[A PREENCHER]` |
| Colunas condicionais | `tem_data_competencia` | `[A PREENCHER]` |
| | `tem_data_vencimento` | `[A PREENCHER]` |
| | `tem_valor_original` | `[A PREENCHER]` |
| | `tem_documento` | `[A PREENCHER]` |
| | `tem_conta_bancaria` | `Sim` *(insumo de BU)* |
| Projeção | `mes_corte_realizado` | `[A PREENCHER]` |
| | `reforecast_vigente_ref` | `[A PREENCHER]` |
| MapaAloc | `mapaaloc_arquivo` | `[A PREENCHER]` *(ex: `GCG_MapaAloc.xlsx`, sem versão no nome)* |
| Moeda | `moeda` | `[A PREENCHER]` |
| Doc | `doc_especifico` | `GCG_Modelo_v1.md` *(defasado — ver §3)* |

---

## 2. Shape da `f_Base` — GCG

| Bloco | Qtd | Detalhe |
|---|---|---|
| Núcleo universal | 23 | Padrão AZ |
| Condicionais ligadas | `[A PREENCHER]` | Mínimo: `conta_bancaria` (insumo de BU) |
| KPIs vivos | `[A PREENCHER]` | Derivado do MapaAloc do GCG |
| **Total** | `[A PREENCHER]` | |

---

## 3. Bugs e divergências conhecidas (janela: 15–20 dias após AB)

| Item | Descrição | Estado |
|---|---|---|
| BUG-02 | `[A DOCUMENTAR]` | Aberto |
| BUG-03 | `[A DOCUMENTAR]` | Aberto |
| Divergências DRE | 5 divergências identificadas | A investigar |
| Documentação defasada | `GCG_Modelo_v1.md` cita 34 col / v6. Realidade: 37 col / v7 | Corrigir na janela GCG |

---

## 4. `f_bancos/` — saldos bancários

Pasta e arquivo já criados (referência de implementação para o padrão):

```
assets/dados/GCG - GCG Clinica/f_bancos/GCG_f_Bancos.xlsx
```

Colunas (contrato padrão — SRS §4.2): `data | nome_conta | BU | saldo`

**Estado atual:**
- Arquivo existe com dados de saldo
- Valores de BU na coluna `BU` devem corresponder aos `bu_validos` do `cad_cliente_GCG.json` (quando preenchido)
- O ETL lê automaticamente quando `f_bancos/` existe — nenhuma configuração necessária

---

## 5. Satélite `cad_depara_bu`

Necessário para derivação de BU via conta bancária. Estrutura: `conta_bancaria → bu`.

| `conta_bancaria` | `bu` |
|---|---|
| `[A PREENCHER]` | `[A PREENCHER]` |

---

*Versão 01 — 19/jun/2026*
*Preencher todos os campos [A PREENCHER] antes de processar dados do GCG.*
