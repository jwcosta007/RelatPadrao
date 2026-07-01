# Cadastro de Cliente — GCG Clínica

> Fonte de verdade das configurações e histórico da GCG Clínica no Modelo Padrão AZ Resultados.
> Regras universais em `SDD/SRS_RegrasRelatPadrao.md`.

---

## 1. Identificação e configuração (`cad_cliente`)

| Grupo | Campo | Valor |
|---|---|---|
| Identificação | `codigo` | `GCG` |
| | `nome` | `GCG Clínica` |
| | `segmento_cliente` | `Estetica` |
| | `status` | `Ativo` |
| Origem de dados | `origem_dados_realizado` | `Arquivo Empresa` |
| | `erp_nome` | `Conta Azul` |
| | `path_lctos_tipo` | `xls` *(extensão nominal; na prática XLSX — usar `openpyxl`)* |
| | `path_lctos` | `assets/dados/GCG - GCG Clinica/f_Lctos/` *(derivado por convenção — SRS §4.4)* |
| | `path_mapa` | `assets/dados/GCG - GCG Clinica/GCG_MapaAloc.xlsx` *(derivado por convenção — SRS §4.4)* |
| | `path_apoio` | *(null)* |
| Staging | `staging_mapa_fonte` | `Situação=Quitado → tipo_registro=Realizado → "Dados Oficiais"` / `Situação=Em aberto → tipo_registro=Projetado → "Projeção"` / `Situação=Atrasado → tipo_registro=Atrasado → "Atraso"` / `(futuro) Orçado → "Orçamento"` / `(futuro) Reforecast → "Reforecast"` |
| | `fingerprint_aplicavel` | `Não` |
| | `conversao_defensiva_valor` | `Sim` |
| BU | `bu_aplicavel` | `Sim` |
| | `bu_origem` | `de_para_conta_bancaria` |
| | `bu_regra` | De-para conta bancária → BU via tabela §6. "CPF" = movimentos PF do dentista (carnê leão, base caixa); "CNPJ" = entidade PJ (lucro presumido). Labels intencionais — não renomear. |
| | `bu_valores_validos` | `CPF \| CNPJ` |
| Colunas condicionais | `tem_data_competencia` | `Sim` |
| | `tem_data_vencimento` | `Sim` |
| | `tem_valor_original` | `Sim` |
| | `tem_documento` | `Não` *(Nota fiscal 0% preenchida na amostra — 2853 linhas contas_a_pagar + 2041 contas_a_receber)* |
| | `tem_conta_bancaria` | `Sim` *(insumo de BU — obrigatório; linha com `valor` E `conta_bancaria` ambos vazios → erro técnico, ver §4)* |
| | `tem_fornecedor_cliente` | `Sim` *(Nome do fornecedor / Nome do cliente)* |
| Projeção | `mes_corte_realizado` | `2026-05` *(formato `AAAA-MM`)* |
| | `reforecast_vigente_ref` | *(null — sem reforecast vigente)* |
| MapaAloc | `mapaaloc_arquivo` | `GCG_MapaAloc.xlsx` |
| Moeda | `moeda` | `BRL` |
| Doc | `doc_especifico` | *(este arquivo)* |

---

## 2. Shape da `f_Base` — GCG

| Bloco | Qtd | Detalhe |
|---|---|---|
| Núcleo universal | 23 | Padrão AZ (ver `SDD/SRS_RegrasRelatPadrao.md` §1.2) |
| Condicionais ligadas | 5 | `conta_bancaria`, `fornecedor_cliente`, `data_competencia`, `data_vencimento`, `valor_original` |
| KPIs vivos | 7 | Ver §2.1 |
| **Total** | **35** | |

### 2.1 KPIs vivos (≥1 "Sim" no MapaAloc e em `_KPI_COLS_ALL`)

`kpi_ebitda` · `kpi_mc` · `kpi_cv` · `kpi_cf` · `kpi_fcf_firma` · `kpi_fcf_equity` · `kpi_provisao`

### 2.2 Ordem das 35 colunas na `f_Base`

Gerada por `staging.get_f_base_cols()`: núcleo universal → condicionais ligadas → KPIs vivos.

```
# Núcleo universal (23) — SRS §1.2
tipo_registro, data_caixa, historico, categoria, valor, bu,
fonte, sinal, id_lcto,
mes_caixa, ano, trimestre, semestre, mes_num,
dre_n1, dre_n2, dre_n3, dre_ordem,
dfc_n1, dfc_n2, dfc_n3, dfc_ordem,
_sem_mapa,

# Condicionais ligadas (5) — ordem de _COND_FLAGS em staging.py
conta_bancaria, fornecedor_cliente,
data_competencia, data_vencimento, valor_original,

# KPIs vivos (7) — ordem de _KPI_COLS_ALL em staging.py
kpi_ebitda, kpi_mc, kpi_cv, kpi_cf, kpi_fcf_firma,
kpi_fcf_equity, kpi_provisao
```

> **Nota `kpi_cmv`:** 4 "Sim" no MapaAloc, mas ainda não em `_KPI_COLS_ALL` (staging.py) nem em `MAPA_COLS` (loader.py). Ativar quando GCG entrar em produção — P8 de §9.

---

## 3. Cascata DRE

```
Receita Líquida
→ RECEITA LÍQUIDA
+ Custos, Despesas Comerciais
→ MARGEM DE CONTRIBUIÇÃO
+ Despesas
→ EBITDA
+ Investimentos, Resultado Financeiro, Resultado Não Operacional
→ LUCRO LÍQUIDO
+ Societário
→ RESULTADO INVESTIDORES  (roxo — KPI principal)
```

GCG não tem N1 "Impostos sobre Resultado" (que é exceção do AB).

---

## 4. Fluxo de dados

```
Origem: Conta Azul — dois exports por período
    ├── visao_contas_a_pagar  (saídas)
    └── visao_contas_a_receber (entradas)
    │
    ▼
Camada pré-staging: extractor_gcg.py
    ├── lê ambos os arquivos (openpyxl — extensão .xls, conteúdo XLSX)
    ├── Situação=Quitado    → tipo_registro=Realizado; data_caixa = Data do último pagamento; valor = Valor total pago da parcela (pagar) / Valor total recebido da parcela (receber) — inclui juros/multa realizados
    ├── Situação=Em aberto  → tipo_registro=Projetado; data_caixa = Data de vencimento (a vencer — dado real do ERP, não estimativa; entra no seletor de projeção, SRS §10.1/§10.3); valor = Valor total da parcela em aberto — inclui juros/multa previstos
    ├── Situação=Atrasado   → tipo_registro=Atrasado; data_caixa = Data de vencimento (vencido, não pago; nunca entra em DRE/DFC/KPI — só rastreabilidade na f_Base, SRS §10.1); valor = Valor total da parcela em aberto
    ├── Situação=Perdido/Desconsiderado → excluir (cancelamento intencional)
    ├── valor E conta_bancaria ambos vazios (lançamento incompleto no Conta Azul) → erro técnico (f_Erros, exclui da f_Base) — validado: 6 casos na amostra, todos Situação=Atrasado
    ├── categoria = Categoria 1
    ├── historico = Descrição — Observações (concatenado só quando Observações existir; senão historico = Descrição). Observações preenchida em 59,6% (pagar) / 77,9% (receber) da amostra — conteúdo complementar, não redundante
    ├── fornecedor_cliente = Nome do fornecedor (contas_a_pagar) / Nome do cliente (contas_a_receber)
    └── BU derivada via de-para conta bancária (tabela §6); contas split (notação `A / B`) → erro técnico, nunca inferir primeira/última
    │
    ▼
Staging (Python — etl.py GCG → staging.py):
    ├── f_Lctos × GCG_MapaAloc (LEFT JOIN por categoria) → enriquece com DRE/DFC/KPIs/sinal
    ├── _sem_mapa: linha fica na f_Base E vai para f_Erros (nunca excluir)
    └── f_Base (35 colunas)
```

---

## 5. BUs reais

| BU | Papel |
|---|---|
| `CPF` | Movimentos da PF do dentista (carnê leão, apuração base caixa) |
| `CNPJ` | Entidade PJ (lucro presumido) |
| `Todas` | Agregador do seletor (não é BU real) |

---

## 6. De-para Conta bancária → BU

Usado pelo `extractor_gcg.py` para derivar a BU a partir da conta bancária do lançamento.

| Conta bancária (Conta Azul) | BU |
|---|---|
| `Itaú - AG 3820 CC 43029-0` | CPF |
| `Itaú - CDB` | CPF |
| `BTG - Camilla` | CPF |
| `BB - AG 0525 CC 35440-6` | CNPJ |
| `BB - Aplicação Fundo BB RF LP SELIC` | CNPJ |
| `BB - ELO` | CPF |
| `Caixa Econômica` | CNPJ |
| `Infinite Pay` | CNPJ |
| `Inter - Ag 0001 C/C 10845153-4` | CNPJ |
| `Saúde Service` | CNPJ |
| `Stone` | CNPJ |
| `Recebimentos \| Camilla Garritano` | CNPJ |
| `Recepção (Caixinha)` | CPF |
| `Ajustes de efeito zero (justificar)` | CNPJ *(conta virtual — ver nota abaixo)* |

> **Contas split (notação `A / B`):** ex. `BB - AG 0525 CC 35440-6 / Inter - Ag 0001 C/C 10845153-4`, `Infinite Pay / Itaú - AG 3820 CC 43029-0` — **decisão travada:** gerar erro técnico, nunca inferir primeira/última conta do split.

> **`Ajustes de efeito zero (justificar)`:** conta virtual do Conta Azul usada para registrar movimentos que não passam pelas contas bancárias reais (ex.: PIX recebido direto na conta pessoal de um sócio, reconhecido como receita da clínica + distribuição de lucro). Deve **fechar em zero mensalmente**; validado com caso real da base (recebimento em 11/nov, distribuição formalizada só em 18/dez — gap de ~1 mês). O bate mensal é intencional: serve para **detectar esse tipo de defasagem** e disparar ajuste manual. Ver pendência P11 (§9) — teste a implementar na aba `check`.

---

## 7. `f_bancos/` — saldos bancários

```
assets/dados/GCG - GCG Clinica/f_bancos/GCG_f_Bancos.xlsx
```

Colunas (contrato padrão — SRS §4.2): `data | nome_conta | BU | saldo`

Estado atual: arquivo com dados de saldo set/2025–abr/2026. BUs `CPF` e `CNPJ` já preenchidas conforme §5.

---

## 8. MapaAloc — estado atual

| Item | Valor |
|---|---|
| Arquivo | `GCG_MapaAloc.xlsx` |
| Total categorias | 166 |
| Colunas | 26 (5 blocos: Metadados, DRE, DFC, Controle, KPIs) |
| N3-único DRE | 0 violações ✅ |
| N3-único DFC | 0 violações ✅ |

---

## 9. Pendências

| # | Pendência | Responsável |
|---|---|---|
| P7 | Definir categorias para `kpi_receita_liquida` e `kpi_lucro_liquido` no MapaAloc | James |
| P8 | Ativar `kpi_cmv` — adicionar a `_KPI_COLS_ALL` (staging.py) e `MAPA_COLS` (loader.py) | AZ |
| P9 | Contas split com `/` — regra definida (erro técnico, §6); implementar no extractor | AZ |
| P10 | Implementar `extractor_gcg.py` (Conta Azul XLS) | AZ |
| P11 | Aba `check` (GCG): bate mensal da conta virtual `Ajustes de efeito zero` (BU CNPJ) deve fechar em zero — `SUMIFS(f_Base[valor], f_Base[conta_bancaria], "Ajustes de efeito zero (justificar)", f_Base[mes_caixa], <mês>)`. Aguarda design geral da aba `check` (SRS §7.1, ROADMAP) | AZ |

---

## 10. Divergências conhecidas

| Item | Descrição | Estado |
|---|---|---|
| Divergências DRE | 5 divergências vs controle manual do cliente | A investigar na janela GCG |

---

*Versão 04 — 01/jul/2026*
*Regras universais em `SDD/SRS_RegrasRelatPadrao.md`.*
