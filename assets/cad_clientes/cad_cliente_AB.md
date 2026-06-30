# Cadastro de Cliente — AB Aeterno
*Versão 03 — 22/jun/2026*

> Fonte de verdade das configurações e histórico da AB Aeterno no Modelo Padrão AZ Resultados.
> Complementa `RegrasRelatPadrao_v14b.md` com valores concretos do cliente.
>
> **O que o v03 muda em relação ao v02b:**
> - Cabeçalho: versão e data atualizados
> - §1: `staging_mapa_fonte` inclui mapeamento `Reforecast → "Reforecast"` (provisionado — Reforecast previsto ≈ set/2026; sem arquivo vigente)
> - §1: `reforecast_vigente_ref` atualizado para refletir previsão ≈ set/2026
> - Referências a `RegrasRelatPadrao_v14b` atualizadas para `RegrasRelatPadrao_v17` em todo o documento
>
> **O que o v02b muda em relação ao v02:**
> - §1: nota de formato fixo `AAAA-MM` em `mes_corte_realizado` (alimenta `sel_MesCorte` via DATE — ver v17 §10.2.2)
> - §7: redação do fallback de `f_SaldoBancos` alinhada ao v17 §4.2 (gatilho = mês de abertura ausente)
> - Rodapé: referência de regras atualizada para `RegrasRelatPadrao_v17.md`
>
> **O que o v02 mudou em relação ao v01:**
> - §1: `tem_fornecedor_cliente = Sim` adicionado ao grupo Colunas condicionais
> - §2: condicionais ligadas 1 → 2; total f_Base 33 → 34 colunas
> - §3: fluxo de staging atualizado — `_sem_mapa = TRUE` vai para `f_Base` + `f_Erros` (comportamento inclusivo)

---

## 1. Identificação e configuração (`cad_cliente`)

| Grupo | Campo | Valor |
|---|---|---|
| Identificação | `codigo` | `AB` |
| | `nome` | `AB Aeterno` |
| | `segmento_cliente` | `Servicos` |
| | `status` | `Ativo` |
| Origem de dados | `origem_dados_realizado` | `Arquivo Empresa` |
| | `erp_nome` | *(null — sem ERP)* |
| | `path_lctos_tipo` | `xlsx` |
| | `path_lctos` | `assets/dados/AB - AB Aeterno/ABAeterno/f_Lctos_2023_2026_proj.xlsx` |
| | `path_apoio` | *(null)* |
| Staging | `staging_mapa_fonte` | `tipo_registro=Realizado → "Dados Oficiais"` / `tipo_registro=Orçado → "Orçamento"` / `tipo_registro=Reforecast → "Reforecast"` *(provisionado — Reforecast previsto ≈ set/2026; sem arquivo vigente)* |
| | `fingerprint_aplicavel` | `Não` |
| | `conversao_defensiva_valor` | `Sim` |
| BU | `bu_aplicavel` | `Sim` |
| | `bu_origem` | `f_Lctos_direto` |
| | `bu_regra` | BU já marcada na fonte (campo `bu`). Valores: Ab Aeterno, Da Una Vita, Holding |
| | `bu_valores_validos` | `Ab Aeterno \| Da Una Vita \| Holding` |
| Colunas condicionais | `tem_data_competencia` | `Não` |
| | `tem_data_vencimento` | `Não` |
| | `tem_valor_original` | `Não` |
| | `tem_documento` | `Não` |
| | `tem_conta_bancaria` | `Sim` |
| | `tem_fornecedor_cliente` | `Sim` |
| Projeção | `mes_corte_realizado` | `2026-05` *(formato fixo `AAAA-MM`, mês com 2 dígitos — alimenta `sel_MesCorte` via DATE, v20 §10.2.2)* |
| | `reforecast_vigente_ref` | *(null — sem reforecast vigente; previsto ≈ set/2026)* |
| MapaAloc | `mapaaloc_arquivo` | `AB_MapaAloc_v11 - Atual utilizado na AB.xlsx` |
| | `mapaaloc_versao` | `v11` |
| Moeda | `moeda` | `BRL` |
| Doc | `doc_especifico` | *(este arquivo)* |

---

## 2. Shape da `f_Base` — AB

| Bloco | Qtd | Detalhe |
|---|---|---|
| Núcleo universal | 23 | Padrão AZ (ver `SDD/SRS_RegrasRelatPadrao.md` §1.2) |
| Condicionais ligadas | 2 | `conta_bancaria`, `fornecedor_cliente` |
| KPIs vivos | 9 | Ver §2.1 abaixo |
| **Total** | **34** | |

### 2.1 KPIs vivos (≥1 "Sim" no MapaAloc v11)

`kpi_ebitda` · `kpi_mc` · `kpi_cv` · `kpi_cf` · `kpi_fcf_firma` · `kpi_fcf_equity` ·
`kpi_provisao` · `kpi_receita_liquida` · `kpi_lucro_liquido`

### 2.2 Ordem das 34 colunas na `f_Base`

```
tipo_registro, data_caixa, historico, categoria, valor, bu,
fornecedor_cliente, fonte, sinal, id_lcto,
mes_caixa, ano, trimestre, semestre, mes_num,
dre_n1, dre_n2, dre_n3, dre_ordem,
dfc_n1, dfc_n2, dfc_n3, dfc_ordem,
_sem_mapa, conta_bancaria,
kpi_ebitda, kpi_mc, kpi_cv, kpi_cf, kpi_fcf_firma,
kpi_fcf_equity, kpi_provisao, kpi_receita_liquida, kpi_lucro_liquido
```

> `d_Calendario` e `d_Feriados` **não se aplicam** ao AB: ambos os eixos secundários
> (`tem_data_competencia` e `tem_data_vencimento`) estão desligados. As 5 colunas de tempo
> são materializadas diretamente no ETL a partir de `data_caixa`. Ver §6.3 do v20.

---

## 3. Fluxo de dados

```
Origem: Excel do cliente (Arquivo Empresa)
    │
    ▼
Camada pré-staging: leitura do Excel → f_Lctos_2023_2026_proj.xlsx
    │   (arquivo intermediário padronizado — 10 colunas incluindo fornecedor_cliente)
    ▼
Staging (Python — etl.py AB → staging.py):
    ├── f_Lctos × MapaAloc (LEFT JOIN por categoria) → enriquece com DRE/DFC/KPIs/sinal
    ├── Define fonte: Realizado → "Dados Oficiais" | Orçado → "Orçamento"
    ├── Gera id_lcto sequencial (intra-carga)
    ├── Deriva eixo caixa: ano, trimestre, semestre, mes_num (mes_caixa já existe na fonte)
    ├── _sem_mapa = TRUE (dre_n1 IS NULL após JOIN):
    │       → linha FICA na f_Base com dre_n3/dfc_n3 = NULL
    │       → linha TAMBÉM registrada em f_Erros (motivo: "Sem mapeamento no MapaAloc")
    │       → SUMIFS do DRE/DFC não somam linhas com NULL (filtram por N3 específico)
    └── f_Base (34 colunas)
```

**AB não tem arquivos distintos por tipo de lançamento** — tudo vem de um único arquivo.
O staging distingue `fonte` pelo valor de `tipo_registro`.

---

## 4. BUs reais

| BU | Papel |
|---|---|
| `Ab Aeterno` | Unidade operacional principal |
| `Da Una Vita` | Unidade operacional secundária |
| `Holding` | Holding / financeiro / sócios |
| `Todas` | Agregador do seletor (não é BU real) |

`conta_bancaria` é metadado da transação — não é usada para derivar BU (bu_origem = f_Lctos_direto).

---

## 5. Cascata DRE e exceção `Impostos sobre Resultado`

O arquivo `assets/cad_clientes/cad_cliente_AB.json` é o **contrato máquina** do cliente —
carregado em runtime pelo `pipeline/etl.py`. Contém:

| Chave | Conteúdo |
|---|---|
| `codigo` / `nome` / `segmento_cliente` / `status` | Identificação do cliente |
| `origem_dados_realizado` | Tipo de integração da fonte |
| `path_lctos` | Caminho relativo à raiz do projeto para o arquivo de lançamentos |
| `path_mapa` | Caminho relativo à raiz do projeto para o MapaAloc |
| `staging_mapa_fonte` | Descrição legível do mapeamento arquivo → `fonte` |
| `conversao_defensiva_valor` | `"Sim"` / `"Não"` — converte texto formatado para número |
| `bu_origem` | Como a BU é derivada (`f_Lctos_direto`, `de_para_conta_bancaria`, etc.) |
| `bu_validos` | BUs aceitas pelo ETL na validação de erros técnicos |
| `tipo_reg_validos` | Valores aceitos de `tipo_registro` |
| `mapa_fonte` | Mapeamento `tipo_registro → fonte` (campo `fonte` na f_Base) |
| `tem_*` | Flags booleanas das colunas condicionais (`tem_conta_bancaria`, etc.) |
| `mes_corte_realizado` | Mês de corte Realizado×Projeção (formato `AAAA-MM`) |
| `reforecast_vigente_ref` | Etiqueta de auditoria do reforecast ativo (`null` se inexistente) |
| `mapaaloc_arquivo` / `mapaaloc_versao` | Identificação do MapaAloc em uso |
| `moeda` | Moeda do cliente (`"BRL"`) |
| `saldo_seed` | Saldo inicial de `f_SaldoBancos` — zeros provisórios (preencher com saldos reais) |
| `dre_cascade` | Cascata de KPIs do DRE (ver abaixo) |

### Exceção — `Impostos sobre Resultado` é N1 próprio

Na cascata padrão AZ, `Impostos sobre Resultado` seria N1 dentro de `Resultado Financeiro`
ou similar. Para AB, é um **N1 independente** na cascata, posicionado após
`Resultado Não Operacional` e antes de `Lucro Líquido`.

Cascata DRE AB:
Receita Bruta → Deduções → **RECEITA LÍQUIDA** → Custos → Despesas Comerciais →
**MARGEM DE CONTRIBUIÇÃO** → Despesas (Pessoal / Prediais / Administrativas) → **EBITDA** →
Investimentos → Resultado Financeiro → Resultado Não Operacional →
**IMPOSTOS SOBRE RESULTADO** ← *N1 próprio (exceção AB)* →
**LUCRO LÍQUIDO** → Societário → **RESULTADO INVESTIDORES**

### Checklist de governance (fechamento mensal)

A exceção foi confirmada na estrutura do `Mapa` interno do arquivo-piloto, **não** no
`AB_MapaAloc_v11` externo (fonte de verdade). A cada fechamento mensal, verificar no
`AB_MapaAloc_v11` canônico que `Impostos sobre Resultado` mantém:
- `dre_n1 = "Impostos sobre Resultado"` (N1 próprio)
- Posição após `Resultado Não Operacional` e antes de `Lucro Líquido`
- 0 violações de N3-único em DRE e DFC

---

## 6. MapaAloc — estado atual

| Item | Valor |
|---|---|
| Arquivo | `AB_MapaAloc_v11 - Atual utilizado na AB.xlsx` |
| Total categorias | 94 |
| N3-único DRE | 50 distintos / 0 violações |
| N3-único DFC | 24 distintos / 0 violações |
| Categorias _sem_mapa | 0 (todas as categorias do f_Lctos encontradas no MapaAloc) |

Categorias especiais confirmadas no MapaAloc v11:
- **Efeito Zero** (10 categorias): transferências entre contas/empresas, fatura cartão, reembolsos, aplicações financeiras
- **SEM_DFC** (2 categorias): `Custo - Provisões RH`, `Provisões RH`

---

## 7. Pendências do cliente

| Pendência | Impacto | Estado |
|---|---|---|
| `f_SaldoBancos` | CAIXA Início do DFC = 0 enquanto faltar o saldo de abertura | Gap ativo — aba criada vazia no workbook. Fallback v20 §4.2: se faltar o mês de abertura (`1º mês do DFC − 1`), `saldo_inicial = 0` + aviso em `f_Erros` ("Saldo de abertura ausente para AAAA-MM"). DFC permanece funcional; **não** usar `#N/D`. |
| Diferença numérica | Total da fonte ≠ controle manual do cliente | Fora de escopo do relatório. Entregar com ressalva explícita. Dado de origem — James fecha em paralelo. |

---

## 8. Histórico do piloto (ABRelatório_Financeiro_202604abr_V2.1.xlsx — analisado em jun/2026)

Abas do arquivo piloto:
- `DRE Gerencial` — estrutura com dados (cascata completa, SUMIFS sobre BaseRelatorios)
- `DFC` — esqueleto de linhas pronto, sem fórmulas/dados
- `BaseRelatorios` — fato 55 colunas (substituída pela `f_Base` de 34 colunas)
- `f_BaseRelat` — staging 16 colunas (staging migrado para Python)
- `Lctos` — cópia da fonte crua (não replicar no arquivo fim)
- `d_Calendario` — 18 colunas, 2193 linhas (não replicar — AB não usa eixos secundários)
- `d_Feriados` — 57 linhas (não replicar — depende de d_Calendario)
- `Mapa` — MapaAloc interno (substituído pelo arquivo externo)
- `Lista` — seletores (BU, mês, trimestre, semestre, ano, tipo)

Abas que **não devem** existir no arquivo novo:
`BaseRelatorios` (55 col — substituída), `f_BaseRelat` (staging no Python), `Lctos` (fonte crua),
`Mapa` (arquivo externo), `d_Calendario` (não aplicável ao AB), `d_Feriados` (não aplicável ao AB).

Abas do arquivo gerado (`AB_RelatFinanceiro_YYYYMMDDHHMM.xlsx`):
`cad_cliente` · `f_Base` · `f_SaldoBancos` · `DRE Gerencial` · `DFC` · `Lista` · `check` · `f_Erros`

Diferenças estruturais relevantes do piloto vs arquivo novo:
- Campo "Tipo" (Realizado|Orçado) → renomeado "Projeção" (Orçado|Reforecast); Realizado é automático via mes_corte
- `BaseRelatorios` (55 col) → `f_Base` (34 col); staging removido do Excel para Python

---

*Versão 03 — 22/jun/2026*
*Fonte de verdade de configuração AB Aeterno. Regras universais em `SDD/SRS_RegrasRelatPadrao.md`.*
*Preencher `f_SaldoBancos` (mês de abertura) antes de considerar o DFC completo.*
