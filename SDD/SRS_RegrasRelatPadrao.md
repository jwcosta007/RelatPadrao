# Regras Modelo Padrão AZ Resultados
*Versão 20 — 23/jun/2026*

> **Pendências a validar antes de documentar (v20 → v21):**
> - §11.8 DRE: `DRE_CASCADE` (quais N1 precedem cada KPI) é config de cliente — definir
>   onde vive (etl por cliente, `cad_cliente`, ou seção dedicada)
> - §11.7/§11.8: N3 deduplicado pelo builder — múltiplas categorias com mesmo N3 colapsam
>   em uma linha; SUMIFS agrega todas. Confirmar se é regra universal ou exceção do builder
> - §11.9 DFC: seletores do DFC são visuais; named ranges apontam para `'DRE Gerencial'` —
>   documentar como comportamento intencional ou revisar design
>
> Histórico de versões anteriores em `CHANGELOG.md`.

---

## 0. Precedência e estado da documentação *(ler primeiro)*

**Este documento é a fonte de verdade corrente do projeto.** Sobrepõe os demais `.md` em qualquer conflito.

| Arquivo | Papel | Estado |
|---|---|---|
| `SRS_RegrasRelatPadrao.md` | **Fonte de verdade corrente** | Este documento |
| `RegrasRelatPadrao_v14.0.md` / `v13.md` | Substituídos | Remover após validação do v14b |
| `AZ_Modelo_Padrao_v7.md` | **Histórico — NÃO UTILIZAR** | ⚠️ Estrutura antiga (`fonte_erp`/`segmento` no MapaAloc, customs, contagem antiga). Conflita com v14b. Consultar apenas para arqueologia; **nunca** implementar a partir dele. |
| `AZ_Proposta_Arquitetura_Greenfield_v1.md` | Backlog migração Python | Não é fonte de verdade; decisões aplicáveis absorvidas aqui |
| `Modelo_MapaAloc_v2_.xlsx` | Template MapaAloc | Estado atual, não alvo. Pendente atualização para estrutura v14b (25 col / 5 blocos, ver §7.2) |
| `cad_cliente/*.md` | **Cadastro por cliente** | Fonte de verdade de configuração e histórico de cada cliente |

> ⚠️ **Documentos de cliente `*_Modelo_v1.md` (`AB_Modelo_v1.md`, `GCG_Modelo_v1.md`) são
> HISTÓRICOS.** Foram substituídos pelos `cad_cliente/*.md`. Contêm referências defasadas
> (ex.: `GCG_Modelo_v1.md` cita "34 colunas / v6"; `AB_Modelo_v1.md` cita "37 colunas / v7").
> Não implementar a partir deles. Ver §13.5 para o inventário completo de referências a
> rebaixar/corrigir na próxima geração de docs.

---

## 1. CONTRATO DE COLUNAS DA `f_Base` — FECHADO

> **Status: FECHADO.** Fórmulas podem ser escritas contra este contrato.
> A frente de projeções não altera o contrato de colunas — `tipo_registro` já é coluna do
> núcleo; ganhar um 3º valor aceito ("Reforecast") é mudança de **domínio**, não de **shape**.

### 1.1 Princípio estrutural — contrato PARAMETRIZADO

A `f_Base` **não é uma lista fixa universal**. É um **núcleo universal** + **colunas
condicionais** ligadas/desligadas pela **Camada 0** (`cad_cliente`). Como o relatório usa
**Tabela do Excel com referência por nome** (`f_Base[[coluna]]`), a **posição da coluna é
irrelevante** — ligar/desligar coluna **não quebra fórmula**, desde que nenhuma fórmula
referencie coluna desligada.

### 1.2 Núcleo universal (todo cliente AZ tem) — 23 colunas

| Bloco | Colunas | Qtd |
|---|---|---|
| Transacional | `tipo_registro`, `data_caixa`, `historico`, `categoria`, `valor`, `bu`, `fonte`, `sinal`, `id_lcto` | 9 |
| Eixo caixa (derivado) | `mes_caixa`, `ano`, `trimestre`, `semestre`, `mes_num` | 5 |
| DRE | `dre_n1`, `dre_n2`, `dre_n3`, `dre_ordem` | 4 |
| DFC | `dfc_n1`, `dfc_n2`, `dfc_n3`, `dfc_ordem` | 4 |
| Controle | `_sem_mapa` | 1 |

### 1.3 Colunas CONDICIONAIS (ligadas/desligadas na Camada 0)

| Coluna | Flag em `cad_cliente` | Quando ligar |
|---|---|---|
| `data_competencia` | `tem_data_competencia` | Clientes com regime de competência |
| `data_vencimento` | `tem_data_vencimento` | Clientes com controle de vencimento |
| `valor_original` | `tem_valor_original` | Clientes com distinção faturado × recebido |
| `documento` | `tem_documento` | Clientes com nº de NF ou documento rastreável na fonte |
| `conta_bancaria` | `tem_conta_bancaria` | Clientes onde conta bancária é insumo de BU ou rastreabilidade |
| `fornecedor_cliente` | `tem_fornecedor_cliente` | Clientes com dado de fornecedor/cliente disponível na fonte |

### 1.4 KPIs — derivados do MapaAloc (NÃO declarados na Camada 0)

Regra: **uma flag KPI existe na `f_Base` se, e somente se, tiver ≥1 "Sim" no MapaAloc do
cliente.** O staging lê o MapaAloc e materializa só as flags vivas.

### 1.5 Fórmula de contagem da `f_Base` por cliente

```
f_Base = 23 (núcleo) + condicionais_ligadas + kpi_vivos
```

O número resultante é registrado em `cad_cliente/*.md` para cada cliente.

### 1.6 Regra de DATA — eixo primário materializado; secundários cruzam sob demanda

- **`data_caixa` (eixo primário):** derivados `mes_caixa`/`ano`/`trimestre`/`semestre`/`mes_num`
  **materializados na `f_Base`** → SUMIFS direto, rápido mesmo com 31k+ linhas.
- **`data_competencia` / `data_vencimento` (eixos secundários):** só a data bruta na fato
  (quando ligadas). Derivados obtidos via JOIN com `d_Calendario` sob demanda.
- Em cliente com competência ≠ caixa, mês/trim/sem de competência **podem divergir** dos de
  caixa — por isso vêm do calendário, não materializados.

> **`d_Calendario` e `d_Feriados` são opcionais:** criadas somente quando ≥1 eixo secundário
> está ativo (`tem_data_competencia = Sim` ou `tem_data_vencimento = Sim`). Quando ambos
> desligados, as 5 colunas de tempo são materializadas diretamente no ETL a partir de
> `data_caixa` — sem JOIN de calendário e sem as abas no workbook. Ver §6.3.

### 1.7 Campo `fonte` na `f_Base` — origem e fronteira

`fonte` identifica **a origem de cada lançamento individualmente** para rastreabilidade e
pesquisa de diferenças — **não** é filtro de relatório e **não** se mistura com `tipo_registro`.

**Fronteira travada:**
- **`tipo_registro`** = filtro de DRE, DFC, KPI e O×R. Valores: `Realizado` / `Orçado` / `Reforecast`
- **`fonte`** = rastreabilidade por lançamento. Valores típicos: `"Dados Oficiais"` /
  `"Orçamento"` / `"Gerencial"` / `"Manual"` / outros conforme o cliente

**Origem do `fonte`:** definido pelo **staging**, com base no mapeamento arquivo/pasta → fonte
declarado em `cad_cliente.staging_mapa_fonte`. **Não vem do MapaAloc** (`fonte_erp` removido).

Exemplo de mapeamento (ver `cad_cliente_AB.md`):

| Arquivo/Pasta | `tipo_registro` | `fonte` resultante |
|---|---|---|
| f_Lctos (Arquivo Empresa) | `Realizado` | `"Dados Oficiais"` |
| f_Lctos (Arquivo Empresa) | `Orçado` | `"Orçamento"` |

### 1.8 Campo `_sem_mapa` — critério definitivo

`_sem_mapa = TRUE` quando **`dre_n1 IS NULL`** após o LEFT JOIN do staging com o MapaAloc.
Ocorre quando a `categoria` do lançamento não tem entrada no MapaAloc.

Critério à prova de falso positivo: toda linha válida do MapaAloc tem `dre_n1` preenchido
(incluindo `Efeito Zero` e `SEM_DFC`). A condição `dre_n1 IS NULL` ocorre **se e somente se**
a categoria não foi encontrada no JOIN.

### 1.9 Onde as condicionais são listadas — `cad_cliente`

Aba `cad_cliente` no workbook, 1 linha/cliente. Grupo dedicado "Colunas condicionais":
`tem_data_competencia`, `tem_data_vencimento`, `tem_valor_original`, `tem_documento`,
`tem_conta_bancaria`, `tem_fornecedor_cliente`. KPIs e `dfc_*` **não** entram aqui
(derivam do MapaAloc / são universais).

### 1.10 Convenção de sinal em `f_Lctos` — contrato obrigatório

Valores devem chegar à `f_Base` com sinal econômico:

| Categoria | Sinal |
|---|---|
| Receitas | positivo |
| Despesas e custos | negativo |

Esta convenção é pré-requisito para que subtotais N2/N1 e KPIs sejam calculados por
SUM simples no workbook, sem multiplicador de sinal nas fórmulas (§11.11).

**O ETL não inverte sinais** — a responsabilidade é da fonte. Verificar no `cad_cliente`
se a fonte respeita esta convenção; se não respeitar, aplicar conversão no `loader.py`.

---

## 2. CONTRATO DO MapaAloc — FECHADO

> **Status: FECHADO.**

### 2.1 Estrutura — 25 colunas, 5 blocos

| Bloco | Colunas | Qtd |
|---|---|---|
| 1 — Metadados | `categoria`, `sinal`, `ativo`, `observacao` | 4 |
| 2 — DRE | `dre_n1`, `dre_n2`, `dre_n3`, `dre_ordem` | 4 |
| 3 — DFC | `dfc_n1`, `dfc_n2`, `dfc_n3`, `dfc_ordem` | 4 |
| 4 — Controle | `data_criacao`, `data_alteracao`, `responsavel`, `validado` | 4 |
| 5 — KPIs | `kpi_ebitda`, `kpi_mc`, `kpi_cv`, `kpi_cf`, `kpi_fcf_firma`, `kpi_fcf_equity`, `kpi_provisao`, `kpi_receita_liquida`, `kpi_lucro_liquido` | 9 |

**Cabeçalho duplo:** linha 1 = títulos de bloco (merge); linha 2 = nomes de coluna.
Staging usa `Table.Skip(Aba,1)` → `Table.PromoteHeaders` (M) ou equivalente Python.

**Colunas removidas do padrão (não adicionar):**
- `fonte_erp` → fonte vem do staging (§1.7)
- `segmento` → atributo do cad_cliente (§3.1)
- `custom1_*`, `custom2_*` → removidos; não reintroduzir
- `kpi_cmv` (quando 100% "Não") → remover do MapaAloc quando sem nenhum Sim

### 2.2 Regras de integridade

- **`categoria`-único *(erro crítico)*:** cada valor de `categoria` deve aparecer em **no
  máximo uma linha ativa** (`ativo = "Sim"`) no MapaAloc. Categoria duplicada impede JOIN
  correto e causaria multiplicação de linhas em `f_Base`.
  **Comportamento em caso de violação:**
  - ETL interrompe o processamento de lançamentos
  - Workbook gerado com `f_Base` vazia (apenas cabeçalho)
  - `f_Erros` recebe uma ocorrência por `categoria` duplicada:
    `"Categoria duplicada no MapaAloc: {categoria} — {n} ocorrências. Corrigir MapaAloc e recarregar."`
  - Demais abas estruturais geradas normalmente; DRE/DFC exibem zeros

- **N3-único:** cada `dre_n3` e cada `dfc_n3` resolve para exatamente um par (n1, n2).
  Verificar antes de qualquer carga — SUMIFS por N3 soma indevido sem unicidade.
- **`ativo = "Sim"`** em toda linha viva. Linhas com `ativo = "Não"` são ignoradas.
- **`dre_ordem` e `dfc_ordem`:** número único por categoria. Mesma lógica para ambos —
  determina sequência de exibição e drill-down.
- **`kpi_*`:** `"Sim"` ou `"Não"`. KPI com 100% "Não" deve ser removido da coluna.

### 2.3 Efeito Zero e SEM_DFC

Dois N1 especiais existem no MapaAloc para categorias sem efeito em relatório-fim:

| N1 | N3 típico | Regra |
|---|---|---|
| `Efeito Zero` | Transferência entre Contas / Transferência entre Empresas | **Excluído de DRE e DFC.** Categorias de anulação mútua (transferências, quitações de cartão, reembolsos internos). Usado apenas para reconciliação de contas bancárias quando necessário. |
| `SEM_DFC` | SEM_DFC | Categoria com impacto no DRE mas **sem efeito no DFC** (ex.: provisões RH). O staging exclui essas linhas do cálculo do fluxo de caixa. |

### 2.4 `dfc_ordem` — faixas por grupo DFC

Mesma lógica do `dre_ordem`: número único por categoria dentro do grupo, faixas
não-conflitantes entre grupos. Não há sobreposição entre faixas.

| Grupo DFC | Faixa |
|---|---|
| Ativ. Operacionais — Entradas | 10–99 |
| Ativ. Operacionais — Saídas: Cancelamentos | 100–109 |
| Ativ. Operacionais — Saídas: Impostos s/Vendas | 110–119 |
| Ativ. Operacionais — Saídas: Outros Custos | 120–129 |
| Ativ. Operacionais — Saídas: Despesas Comerciais | 130–139 |
| Ativ. Operacionais — Saídas: Pessoal | 140–199 |
| Ativ. Operacionais — Saídas: Despesas Prediais | 200–219 |
| Ativ. Operacionais — Saídas: Despesas Administrativas | 220–249 |
| Ativ. Operacionais — Saídas: Impostos s/Resultado | 250–259 |
| Atividades Não Operacionais | 300–319 |
| Atividades de Investimento | 400–419 |
| Atividades de Financiamento | 500–529 |
| SEM_DFC | 9900–9909 |
| Efeito Zero | 9910–9919 |

---

## 3. Camada 0 — Cadastro de Clientes

A Camada 0 **define o shape da fato**. Cada cliente tem 1 linha na aba `cad_cliente` do
workbook e um arquivo de referência em `cad_cliente/*.md`.

### 3.1 `cad_cliente` — estrutura de campos

| Grupo | Campos |
|---|---|
| Identificação | `codigo`, `nome`, `segmento_cliente`, `status` |
| Origem de dados | `origem_dados_realizado` ("Arquivo Empresa" / "Extrato Bancário" / nome do ERP), `erp_nome`, `path_lctos_tipo`, `path_lctos`, `path_apoio` |
| Staging | `staging_mapa_fonte` (arquivo/pasta → valor de `fonte`), `fingerprint_aplicavel`, `conversao_defensiva_valor` |
| BU | `bu_aplicavel`, `bu_origem`, `bu_regra` (texto livre), `bu_valores_validos` (lista — duplo-check) |
| Colunas condicionais | `tem_data_competencia`, `tem_data_vencimento`, `tem_valor_original`, `tem_documento`, `tem_conta_bancaria`, `tem_fornecedor_cliente` |
| Projeção | `mes_corte_realizado` (AAAA-MM — último mês de Realizado fechado), `reforecast_vigente_ref` |
| MapaAloc | `mapaaloc_arquivo`, `mapaaloc_versao` |
| Moeda | `moeda` |
| Doc | `doc_especifico` |

Satélites 1:N: `cad_depara_bu` (chave→BU, para clientes com mapeamento conta→BU) ·
`cad_excecoes_dre` (exceções de classificação por cliente).

**Campo `origem_dados_realizado`:** informa ao desenvolvedor qual tipo de integração é
necessária entre o dado bruto e a `f_Base`. Pode ter 1 ou mais etapas intermediárias.
Não se confunde com `fonte` da `f_Base` (que é por lançamento, §1.7).

### 3.2 BU — "fórmula mágica" por cliente

`segmento` e `moeda` são atributos do `cad_cliente` (não da fato). A BU **sempre chega
resolvida na coluna `bu` da `f_Base`**; o que varia por cliente é o passo do staging:

| `bu_origem` | Regra | Exemplo |
|---|---|---|
| `f_Lctos_direto` | BU já marcada na fonte (campo `bu` do arquivo de entrada) | AB |
| `de_para_conta_bancaria` | De-para conta→BU via `cad_depara_bu` | GCG |
| `grupo_categorias_mapaaloc` | BU derivada do grupo de categorias no MapaAloc | Santé/OS |

Ver `cad_cliente/*.md` para valores reais por cliente.

---

## 4. Artefatos de controle — `f_Erros`, `f_SaldoBancos`, aba check

### 4.1 `f_Erros` + sinalização na check

O staging distingue dois tipos de ocorrências anômalas com destinos diferentes:

**Erros técnicos** (dado inválido, BU fora do domínio declarado, `tipo_registro` desconhecido,
falha de conversão de valor): **NÃO entram na `f_Base`**. Vão exclusivamente para `f_Erros`
com o motivo correspondente.

**Lacunas de classificação (`_sem_mapa = TRUE`)**: a `categoria` do lançamento não encontrou
correspondência no MapaAloc (LEFT JOIN sem match → `dre_n1 IS NULL`). O dado é válido; o
plano de contas está incompleto. Essas linhas **ficam na `f_Base`** (com `dre_n3`, `dfc_n3`
= NULL) **e também são registradas em `f_Erros`** para análise e correção.

> Por que `_sem_mapa` permanece na `f_Base`: SUMIFS do DRE/DFC filtram por N3 específico —
> linhas com `dre_n3 = NULL` nunca somam em nenhum relatório-fim. Nenhum valor é perdido
> silenciosamente; o operador é alertado pela aba check; ao corrigir o MapaAloc e reexecutar
> o ETL, as linhas reintegram automaticamente os totais.

A **aba check** exibe em **vermelho** (formatação condicional) o nº de linhas em `f_Erros`
e o nº de linhas `_sem_mapa` quando > 0. Sem alerta de tela — simplifica o ETL.

### 4.2 `f_SaldoBancos`

Granularidade: `data | BU | nome_conta | valor`. Saldo é **estoque**, não fluxo → tabela
própria, não entra na `f_Base`. Alimenta CAIXA Início/Fim do DFC e o bate de saldo.
Mínimo: total do mês.

**Origem:** a aba `f_SaldoBancos` é criada **uma única vez** no workbook (como tabela
ListObject vazia) durante a montagem inicial do Excel. É preenchida **manualmente pelo
operador** ao longo do tempo conforme os dados de saldo são disponibilizados. **O ETL de
lançamentos não gera, não lê e não sobrescreve esta aba.**

**Fallback — saldo de abertura ausente:** o saldo inicial do DFC é o saldo de fechamento do
**mês imediatamente anterior ao 1º mês exibido** (mês-âncora de abertura = `1º mês do DFC − 1`).
Se `f_SaldoBancos` **não contiver registro para esse mês de abertura**, aplica-se:

- `saldo_inicial = 0` (mantido — **não usar `#N/D`**, que propaga erro e quebra as somas de
  fluxo a jusante; um DFC funcional com aviso é melhor que um DFC quebrado).
- Registrar em `f_Erros` uma ocorrência:
  `"Saldo de abertura ausente em f_SaldoBancos para AAAA-MM — operador deve preencher/atualizar"`.
- A check sinaliza via contador de `f_Erros > 0` em vermelho (§4.3 item 4).

O DFC permanece funcional com CAIXA Início = 0 até o operador preencher o mês de abertura.
**Canal de alerta = exclusivamente `f_Erros` + check.** Sem sinalização adicional na linha do
DFC e sem alerta de tela — mantém o ETL simples. O ETL de lançamentos **não gera, não lê
para cálculo e não sobrescreve** `f_SaldoBancos`.

### 4.3 Aba check — esqueleto inicial (evolutivo)

1. Soma por `kpi_*` = soma da cascata N3 correspondente (**bate reverso**)
2. `bu` distintos na `f_Base` = `bu_valores_validos` da Camada 0 (**duplo-check de BU**)
3. `_sem_mapa` = 0 (toda categoria classificada)
4. Contador de linhas em `f_Erros` (vermelho se > 0)
5. **Bate de colisão Realizado×Projeção:** para cada `mes_caixa`, garantir que o conjunto
   consumido pelos relatórios-fim nunca contém `Realizado` e uma projeção somando no mesmo mês.
   Contador "meses em colisão > 0 → vermelho". **Exceção:** gráfico de validação FP&A (§10.6)
   — isento (3 séries coexistem de propósito).
6. **Próxima evolução:** Bate Saldo DFC × `f_SaldoBancos`

---

## 5. KPIs lendo a base, NUNCA o relatório-fim

**Relatórios-fim (DRE, DFC, O×R) nunca são fonte de outro artefato.** Toda tabela de KPI
e toda checagem lê a **`f_Base` (dado puro)**. Motivo: DRE/DFC têm seletores de data
independentes; um KPI que lesse o DRE ficaria refém do estado dos seletores → quebra silenciosa.

Papel das flags de subtotal (`kpi_receita_liquida`, `kpi_lucro_liquido`, `kpi_ebitda`…):
**não preenchem o DRE** (o DRE soma a cascata por N3). Servem para **tabelas-base de gráficos
de KPI** (SUMIFS direto na `f_Base`) e para o **bate reverso** da aba check.

O gráfico de validação de forecast (§10.6) é uma aplicação direta deste princípio:
3 séries lendo a `f_Base`, nunca o DRE/DFC.

---

## 6. Decisões TRAVADAS

### 6.1 N3-único vale para DRE e DFC

Cada N3 (em `dre_n3` e `dfc_n3`) resolve para exatamente um par (n1, n2). Verificar no
MapaAloc antes de qualquer carga.

### 6.2 Contrato `f_Base` = núcleo universal + condicionais via Camada 0 (§1)

Shape parametrizado. Posição irrelevante (Tabela por nome). Fórmula: `23 + condicionais_ligadas + kpi_vivos`.

### 6.3 Regra de data: eixo caixa materializado; secundários via `d_Calendario` quando ativos (§1.6)

`d_Calendario` e `d_Feriados` são criadas **somente se o cliente tiver ≥1 eixo secundário
ativo** (`tem_data_competencia = Sim` ou `tem_data_vencimento = Sim`). Quando ambos
desligados, as 5 colunas de tempo (`mes_caixa`, `ano`, `trimestre`, `semestre`, `mes_num`)
são materializadas diretamente no ETL a partir de `data_caixa` — sem JOIN de calendário e
sem as abas no workbook.

### 6.4 `fonte` — campo do staging, não do MapaAloc

`fonte` é atributo de rastreabilidade por lançamento, definido pelo staging com base no
mapeamento arquivo/pasta → fonte declarado em `cad_cliente.staging_mapa_fonte`. Valores:
`"Dados Oficiais"` / `"Orçamento"` / `"Gerencial"` / `"Manual"`. `fonte_erp` removido do MapaAloc.

### 6.5 Colunas removidas do padrão (não reintroduzir)

`custom1_*`, `custom2_*`, `kpi_cmv` (quando 100% "Não"), `fonte_erp` (migrado para staging),
`segmento` (migrado para cad_cliente), 3× `_comp` (derivados de competência via `d_Calendario`).

### 6.6 `_sem_mapa` — critério definitivo

`_sem_mapa = TRUE` quando `dre_n1 IS NULL` após LEFT JOIN staging × MapaAloc.
Toda linha válida do MapaAloc tem `dre_n1` preenchido → critério sem falso positivo.

### 6.7 `id_lcto` = único INTRA-CARGA; sem persistência entre cargas

Gerado pelo staging na carga. Persistência real (chave natural/hash) → roadmap Python.

### 6.8 `_sem_mapa` — comportamento inclusivo; erros técnicos → só `f_Erros` (§4.1)

Linhas `_sem_mapa = TRUE` ficam na `f_Base` (com `dre_n3`/`dfc_n3` = NULL) **e** são
registradas em `f_Erros`. Erros técnicos (dado inválido, BU fora de domínio, etc.) vão
**somente** para `f_Erros` — não entram na `f_Base`.

### 6.9 `f_SaldoBancos` = data|BU|nome_conta|valor; fallback = saldo 0; aba manual (§4.2)

### 6.10 Invariante do gerador de DRE/DFC: só referenciar colunas existentes no shape do cliente

O gerador nunca emite referência a coluna desligada.

---

## 7. Pendências e roadmap

### 7.1 Decisões em aberto

- **Aba `Lista` (seletores) vs Camada 0:** seletor de BU passa a derivar de
  `cad_cliente.bu_valores_validos` (fechando duplo-check) ou fica aba independente?
- **Seletor flexível de período da aba O×R** (Trim/Sem/Ano via validação de dados,
  espelhando seletor do DRE). Ver §10.9.
- **Rótulo "gap-to-target"** do bloco Trim/Sem/Ano na aba O×R — confirmar redação que
  comunica "meta", não "desempenho". Ver §10.9.
- **Aba `check` — design das fórmulas de validação (§12):** quais sinalizações implementar
  primeiro; onde vive o limiar de alerta (código Python ou cad_cliente). Aba criada vazia;
  não bloqueia entrega AB.

### 7.1.1 Decisões fechadas (registradas aqui para histórico)

- **`cad_cliente_<CODIGO>.json` — contrato máquina do cliente** *(fechado 25/jun/2026)*
  Config operacional lida pelo `etl_*.py` via `json.load()`. Chaves obrigatórias:
  `bu_validos`, `tipo_reg_validos`, `mapa_fonte`, `mes_corte_realizado`, `saldo_seed`,
  `dre_cascade`. Padrão escolhido antecipa migração para interface web — JSON é formato
  nativo de API. Exemplo: `cad_cliente_AB.json`. Ver `cad_cliente_AB.md` §5.

- **`MONTH(1&sel_Periodo)` → `MATCH(sel_Periodo,lista_periodo,0)`** *(fechado 25/jun/2026)*
  Fórmula de conversão nome-de-mês→número era locale-dependente (falha silenciosa em
  Excel EN-US). Substituída por `MATCH` contra `lista_periodo` (posições 1–12 = meses
  1–12) — locale-independent. Ver §11.11.

- **`requirements.txt` — versões com `>=` em vez de `==`** *(fechado 25/jun/2026)*
  A skill `azr-code` exige pinning exato (`==`). Decisão consciente de manter `>=` neste
  projeto ETL: escopo limitado, dependências estáveis, atualização de patches de segurança
  sem edição manual. Reavaliar para `==` ao migrar para produção web multi-tenant.

- **Commits em português descritivo** *(fechado 25/jun/2026)*
  A skill `azr-code` exige Conventional Commits em inglês (`feat(scope): description`).
  Mantido PT-BR neste projeto: histórico já iniciado em português, contexto solo BR,
  sem CI que valide o formato. Adotar Conventional Commits em inglês nos próximos
  projetos com pipeline AZ formal (`Tasks_v[n].md`).

### 7.2 Dívida de documentação

- `AZ_Modelo_Padrao_v7 → v8`: `segmento`/`moeda` → cad_cliente; `f_Base`; contrato
  parametrizado; `fonte` (origem staging); `_sem_mapa` (dre_n1 IS NULL); `tipo_registro`
  3-valores + corte de projeção (§10).
- `Modelo_MapaAloc_v2_.xlsx` → atualizar template para estrutura v14 (25 colunas, 5 blocos,
  incluindo `tem_fornecedor_cliente` no cad_cliente).
- Remover `RegrasRelatPadrao_v13.md` após validação.

### 7.3 Roadmap

Ver `ROADMAP.md` na raiz do repositório.

---

## 8. Decisões de design herdadas — registro para não regredir

| Decisão | Motivo registrado |
|---|---|
| N3 = chave; N1/N2 = subtotal somado | Normaliza inconsistência da inspiração; viabiliza geração programática |
| N3-único regra do MapaAloc + checagem | Sem unicidade, SUMIFS por N3 soma indevido |
| `segmento` e `moeda` → cad_cliente | Não são dado transacional; constantes de cliente |
| `valor_original` condicional por cliente | Preserva distinção faturado × recebido; fallback `IF(original=null;caixa;original)` só onde a coluna existe |
| Nome canônico `f_Base` | Convenção `f_`; concisão em fórmula |
| OFFSET→SUMIFS por data; `"ND"`→`""` | Performance (não-volátil) e consistência com regra de ouro |
| Gerador como norte de design | Toda decisão compatível com geração automática; conflitos sinalizados (§6.10) |

### 8.1 Histórico de bugs já vencidos

Ver `CHANGELOG.md`.

---

## 9. Princípios de design extraídos da referência de inspiração

- **Esqueleto do DRE** (cascata padrão): ROB → Deduções → Rec. Líquida → Custos →
  Desp. Comerciais → **MC** → Despesas → **EBITDA** → Investimentos → Result. Financeiro →
  Result. Não Op. → **Lucro Líquido** → Societário → Result. Investidores.
  Clientes podem ter exceções na cascata — documentar em `cad_cliente/*.md`.
- **Mecanismo de flexibilidade** (seletores): BU, mês-âncora, projeção, últimos N meses,
  ano comparativo A×B, período comparativo (mês/trim/sem). Poder vem do par **seletor +
  fórmula `SEARCH("Trim"/"Sem")`**. "Stringly-typed": documentar contrato dos rótulos;
  a ordem do IF importa (testar "Trim" antes de "Sem").
- **Reparos antes de replicar:** `OFFSET` volátil → `SUMIFS` por data; `"ND"` → `""`.
- **KPIs universais:** Gastos vs Vendas, EBITDA, %EBITDA, Check EBITDA, Real vs Budget.
- **KPIs específicos de cliente de origem:** não portar para outro cliente sem confirmação
  da nova fonte de dado.

---

## 10. Projeções — Forecast e Reforecast *(design FECHADO; implementação pendente por cliente)*

> **Problema de origem:** a base soma tudo; quando um mês previsto como "Orçado" vira
> "Realizado", há risco de dupla contagem. Solução: corte determinístico por período via
> `mes_corte_realizado` na Camada 0 — determinístico e auditável (não usar `HOJE()`).

### 10.1 `tipo_registro` — 3 valores aceitos

`Realizado` / `Orçado` / `Reforecast`. Filtro de relatório — não se mistura com `fonte` (§1.7).
Nenhuma coluna nova na `f_Base` — é ampliação de domínio do campo existente.

### 10.2 Corte determinístico Realizado × Projeção *(via Camada 0)*

- `mes_corte_realizado` em `cad_cliente` = último mês de Realizado fechado/completo.
- **Regra universal aos relatórios-fim** (DRE, DFC, KPI, aba O×R):
  - `mes_caixa ≤ mes_corte_realizado` → consome **`tipo_registro = "Realizado"`**
  - `mes_caixa > mes_corte_realizado` → consome a **projeção escolhida no seletor de topo**
    (`Orçado` ou `Reforecast`)
- **Não há desempate linha a linha** — é corte por faixa de período. A exclusão mútua é
  garantida por **IF no critério do SUMIFS** (ver §11.3 para fórmula exata).

#### 10.2.1 Coexistência na `f_Base` — ETL não filtra *(decisão travada)*

Realizado e projeção **podem coexistir na `f_Base` no mesmo mês**. O staging **não** remove
Realizado com `data_caixa > mes_corte` nem projeção de meses já fechados. **Toda a exclusão
mútua é responsabilidade do SUMIFS** (IF de corte, §11.3).

- **Por quê:** simplifica o ETL — não precisa conhecer `mes_corte` nem podar a fonte; o
  arquivo do cliente pode conter Realizado adiantado e Orçado do mesmo mês sem conflito.
- **Custo aceito:** o **bate de colisão (§4.3 item 5) deixa de ser rede de segurança e passa
  a ser controle essencial.** Como o dado bruto contém ambos, qualquer célula de valor que
  **esqueça o IF de corte** somará Realizado + Projeção do mesmo mês — e o número parecerá
  plausível. O bate de colisão é o que detecta isso. Ver §10.10.

#### 10.2.2 Contrato de tipo das datas *(à prova de coerção implícita)*

A comparação do corte é sempre **`DATE × DATE`**. O rótulo texto **nunca** entra direto no SUMIFS.

| Campo | Tipo | Forma canônica |
|---|---|---|
| `data_caixa` (f_Base) | `DATE` | dia real do lançamento |
| `mes_caixa` (f_Base) | `DATE` | **1º dia do mês** — `DATE(ano, mês, 1)` |
| `mes_corte_realizado` (cad_cliente) | texto `"AAAA-MM"` | rótulo legível; **não vai ao SUMIFS** |
| `sel_MesCorte` (célula auxiliar do workbook) | `DATE` | `DATE(VALUE(LEFT(rótulo,4)), VALUE(MID(rótulo,6,2)), 1)` |

> A conversão texto→DATE ocorre **uma única vez**, na célula auxiliar `sel_MesCorte`. Todas as
> fórmulas referenciam essa célula (via nome, §11.4), nunca o texto cru `"2026-05"`. Comparar
> texto `"2026-05"` com `mes_caixa` (DATE) tem coerção ambígua no Excel e **pode falhar sem
> erro visível** — proibido.

### 10.3 Seletor de projeção no topo dos relatórios-fim

DRE, DFC e KPIs têm seletor com valores **`Orçado` / `Reforecast`**. **Seleção única** —
não soma as duas projeções. O seletor não inclui `Realizado`: Realizado é consumido
automaticamente para meses fechados via corte de §10.2. Fonte clássica de dupla contagem
se mal-amarrado.

### 10.4 Reforecast — controle manual, máx. 1 revisão ativa

Arquivo de reforecast vigente na pasta = sempre o atual (controle manual). A `f_Base` mantém
apenas: `Realizado + Orçado original + último Reforecast aprovado`. `reforecast_vigente_ref`
em `cad_cliente` = etiqueta de auditoria (não é automação de trilha).

### 10.5 Aba Orçado×Realizado — seletores duplos de cabeçalho

Dois seletores independentes: **esquerdo** (`Realizado` / `Orçado`) × **direito**
(`Orçado` / `Reforecast`). Permite comparar qualquer um vs qualquer um.
- Variação ▲%/▲R$ dinâmica — `esquerda − direita` genérico.
- Combinação degenerada (ex.: Orçado×Orçado → 0%): aceita; responsabilidade do operador.
- Os 3 blocos (Mês / YTD / Trim-Sem-Ano) compartilham o mesmo par de seletores (globais).
- A aba respeita o corte `mes_corte_realizado`: série Realizado termina, não zera.

### 10.6 KPI de validação FP&A — gráfico de 3 séries

Gráfico de linha: `Realizado`, `Orçado`, `Reforecast` sobre um indicador de DRE (ex.: Receita
Bruta). Lê **`f_Base` direto** — nunca o DRE/DFC. Finalidade: aferir viés do orçamento.
Série Realizado termina no corte → **`NA()`** nos futuros (nunca zero). Isento do bate de
colisão da check (§4.3) — 3 séries coexistem de propósito.

### 10.7 Variação % — divisor absoluto; zero → vazio

▲% usa **valor absoluto no divisor** → evita sinal invertido em linhas naturalmente negativas
(Custos, Deduções). Divisor = 0 → ▲% tratada como vazio (não `#DIV/0!`).

### 10.8 Sinalização melhor/pior — seta cruzando a natureza da linha

Seta ↑/↓ (verde/vermelho) indicando melhor/pior, não o sinal cru do número. Cruza com
`sinal` do MapaAloc: Receita subindo = melhor (↑ verde); Custo subindo = pior (↓ vermelho).
Implementação: formatação condicional por ícone + coluna auxiliar com o `sinal`.

### 10.9 Definições de período YTD / Trim-Sem-Ano

- **YTD:** Real e Orçado ambos até o mês escolhido — janela simétrica. Comparação justa.
- **Trim/Sem/Ano:** gap-to-target — Real acumulado **parcial** vs Orçado do **período cheio**.
  Assimetria proposital: mostra "quanto falta para bater a meta". O ▲ lê-se como % da meta
  atingida, **não** como variação de desempenho. Rótulo deve comunicar "meta".
  Seletor flexível de período: pendente (§7.1).

### 10.10 Advertência de implementação *(obrigatória)*

> Ao construir DRE/DFC/KPI/aba O×R com projeção: **verificar que TODAS as travas/IFs de
> exclusão mútua (§10.2) foram criadas** — em cada bloco, cada coluna de variação e cada
> SUMIFS. Quanto mais colunas comparativas, mais pontos onde a colisão Realizado×Projeção
> pode escapar com cara de número correto. O bate de colisão da check (§4.3) é a rede de
> segurança, não substitui a revisão das fórmulas.

### 10.11 Resumo das 14 decisões fechadas desta frente

| # | Decisão | Ref |
|---|---|---|
| 1 | `tipo_registro` = Realizado / Orçado / Reforecast | §10.1 |
| 2 | `mes_corte_realizado` + `reforecast_vigente_ref` no `cad_cliente` | §3.1, §10.2, §10.4 |
| 3 | Corte determinístico por faixa de período (IF no SUMIFS) — DRE, DFC, KPI, O×R | §10.2, §11.3 |
| 4 | Seletor de projeção único (Orçado/Reforecast) no topo de DRE/DFC/KPI | §10.3 |
| 5 | Aba O×R com 2 seletores independentes (esq × dir) | §10.5 |
| 6 | Variação ▲%/▲R$ dinâmica seguindo os 2 seletores | §10.5 |
| 7 | ▲% divisor absoluto; zero → vazio | §10.7 |
| 8 | Seta melhor/pior cruzando `sinal` do MapaAloc | §10.8 |
| 9 | YTD simétrico (Real e Orçado até o mês-corte) | §10.9 |
| 10 | Trim/Sem/Ano = gap-to-target, rótulo "meta" | §10.9 |
| 11 | KPI validação FP&A = 3 séries, `NA()` no futuro, isento do bate | §10.6 |
| 12 | Reforecast manual, máx. 1 revisão ativa | §10.4 |
| 13 | Bate de colisão Realizado×Projeção na check (exceto gráfico) | §4.3 |
| 14 | Advertência: verificar todas as travas/IFs | §10.10 |

**Pendências de detalhe:** seletor flexível de período da O×R; redação final do rótulo
gap-to-target. Ambas em §7.1.


---

## 11. Estrutura operacional do workbook de relatório

> Esta seção documenta **como** as regras de §10 se materializam no workbook Excel.
> Serve de referência para quem constrói ou audita o arquivo de entrega.

### 11.1 Janela de 13 meses

O relatório exibe sempre os 13 meses anteriores (inclusive) ao **mês-âncora** definido pelo
operador. Não há seletor de data-início.

Fórmulas de cabeçalho (linha 7 do DRE/DFC):

```
AA7 = $C$5              ← mês-âncora (seletor do operador — tipo DATE)
Y7  = EDATE(AA7,-1)     ← M-1
W7  = EDATE(Y7,-1)      ← M-2
...
C7  = EDATE(E7,-1)      ← M-12 (13º mês, o mais antigo exibido)
```

Colunas ímpares (C, E, G … AA) = valor. Colunas pares (D, F, H … AB) = % AV (% da Receita Bruta).

### 11.2 Seletor de projeção

O campo de seletor de tipo nos relatórios-fim tem valores **`Orçado` / `Reforecast`** —
não `Realizado / Orçado`. Realizado é consumido automaticamente para meses ≤ `mes_corte_realizado`
via corte embutido no SUMIFS (§11.3). O operador não precisa trocar o seletor ao virar o mês.


### 11.3 SUMIFS com corte determinístico embutido

Fórmula-padrão para cada célula de valor mensal (linha N3 folha do DRE/DFC):

```excel
=SUMIFS(f_Base[valor],
  f_Base[mes_caixa],        col_mes,
  f_Base[dre_n3],           n3_ref,
  f_Base[bu],               IF(sel_BU="Todas","*",sel_BU),
  f_Base[tipo_registro],    IF(col_mes<=sel_MesCorte,"Realizado",sel_Projecao))
```

| Variável | Referência (nome) | Descrição |
|---|---|---|
| `col_mes` | `C$7` | Cabeçalho de mês da coluna atual (DATE, 1º dia) |
| `n3_ref` | `$B9` | Chave N3 da linha atual |
| `sel_BU` | `sel_BU` (`C4`) | Seletor de BU |
| `sel_MesCorte` | `sel_MesCorte` (célula auxiliar DATE) | Último mês Realizado, derivado de `cad_cliente[mes_corte_realizado]` via conversão texto→DATE (§10.2.2) |
| `sel_Projecao` | `sel_Projecao` (`F5`) | Seletor de projeção (`Orçado` ou `Reforecast`) |

O IF `col_mes <= sel_MesCorte` é o **único** ponto de controle do corte — deve estar presente
em **toda** célula de valor nos blocos mensais, acumulado e rolling. **Exceção: blocos Ano A/B
(AJ/AK)** — usam `sel_TipoA`/`sel_TipoB` (§11.4) em vez do corte automático; ver §11.11.
Como o dado
bruto pode conter Realizado e Projeção no mesmo mês (§10.2.1), a ausência do IF em qualquer
célula gera dupla contagem silenciosa. Ver §10.10 e o bate de colisão §4.3 item 5.

### 11.4 Estrutura de colunas do DRE/DFC

Layout padronizado do **DRE Gerencial** *(DFC tem estrutura diferente — ver §11.9.3)*:

| Bloco | Colunas | Conteúdo |
|---|---|---|
| Rótulos | A, B | Nível hierárquico e chave de linha (N3 / N2 / N1) |
| 13 meses | C, E, G, I, K, M, O, Q, S, U, W, Y, AA | Valor mensal |
| % AV | D, F, H, J, L, N, P, R, T, V, X, Z, AB | % AV |
| Acumulado | AD, AE | Soma dos 13 meses + % AV |
| Rolling N | AG, AH | Soma dos últimos N meses (N = AG7) + % AV |
| Ano A | AJ | Total Ano A (SUMIFS por `ano` = AJ6, período = AJ7) |
| Ano B | AK | Total Ano B (SUMIFS por `ano` = AK6, período = AK7) |
| Variação | AL, AM | ▲% e ▲R$ (Ano A vs Ano B) |

**Seletores aplicam-se ao DRE Gerencial.** O DFC não possui seletores interativos próprios — usa os named ranges do DRE via fórmulas (ver §11.9.3).

**Seletores** (células cor creme `FFF9F5CE`) e **rótulos** (sem preenchimento):

| Célula seletor | Rótulo | Conteúdo | Fonte de lista | Default ETL |
|---|---|---|---|---|
| `C4:G4` (mesclado) | B4 = `"Unidade"` | BU | `lista_bu` | `"Todas"` |
| `C5` | B5 = `"Mês/Ano"` | Mês-âncora (DATE — 1º dia do mês) | `lista_ancora` | 1º dia de `mes_corte_realizado` |
| `F5:G5` (mesclado) | E5 = `"Projeção"` | Projeção (`Orçado` / `Reforecast`) | `lista_projecao` | `"Orçado"` |
| `AG7` | — | N meses do bloco rolling | `lista_rolling_n` | `6` (fmt `"00"` → exibe `06`) |
| `AJ5`, `AK5` | — | Tipo de dado Ano A / Ano B | `lista_tipo_registro` | `"Realizado"` |
| `AJ6` | — | Ano A | `lista_anos` | `ano(mes_corte_realizado) − 1` |
| `AK6` | — | Ano B | `lista_anos` | `ano(mes_corte_realizado)` |
| `AJ7`, `AK7` | — | Período dentro do ano | `lista_periodo` | `mês(mes_corte_realizado)` em PT-BR |

> **Rótulos** (B4, B5, E5): células estáticas sem preenchimento. Bordas e estilos conforme `DesignDoc_Relatorio.md` §Seletores.
> **Defaults ETL:** gravados na primeira carga. O operador pode alterar; o ETL não sobrescreve seletores em cargas subsequentes.

#### 11.4.1 Intervalos nomeados OBRIGATÓRIOS *(Defined Names — não endereços fixos)*

Os seletores **devem** ser intervalos nomeados. Endereço fixo (`$C$4`) quebra se o operador
inserir linha/coluna acima/à esquerda; o nome acompanha a célula. **Todas** as fórmulas de
§11.3 e §11.5 referenciam os nomes, nunca os endereços.

| Nome obrigatório | Célula-âncora | Conteúdo |
|---|---|---|
| `sel_BU` | `C4` | Seletor de BU |
| `sel_Ancora` | `C5` | Mês-âncora (DATE) |
| `sel_Projecao` | `F5:G5` (mesclado — âncora `F5`) | `Orçado` / `Reforecast` |
| `sel_RollingN` | `AG7` | N do bloco rolling |
| `sel_MesCorte` | célula auxiliar | `DATE` derivado de `cad_cliente[mes_corte_realizado]` (§10.2.2) |
| `sel_TipoA` / `sel_TipoB` | `AJ5` / `AK5` | Tipo de dado (`Realizado` / `Orçado` / `Reforecast`) |
| `sel_AnoA` / `sel_AnoB` | `AJ6` / `AK6` | Anos comparativos |
| `sel_PeriodoA` / `sel_PeriodoB` | `AJ7` / `AK7` | Período dentro do ano |

A coluna "célula-âncora" indica apenas onde o nome nasce no layout-padrão; a fórmula nunca
usa o endereço.

### 11.7 Aba `Lista` — estrutura e população pelo ETL

A aba `Lista` é a única fonte de todas as validações de dados (comboboxes) do workbook.
O ETL escreve essa aba integralmente a cada carga — nenhum campo é manual.

| Col | Nome do intervalo | Conteúdo | Classificação | Regra ETL |
|---|---|---|---|---|
| A | `lista_periodo` | `janeiro`…`dezembro` + `1º Trim`…`4º Trim` + `1º Sem`/`2º Sem` | Universal fixo | 18 valores; igual para todos os clientes. |
| B | `lista_rolling_n` | `2`–`12` | Universal fixo | 11 valores (mínimo 2); igual para todos os clientes. |
| C | `lista_projecao` | `Orçado` / `Reforecast` | Universal fixo | 2 valores; igual para todos os clientes. |
| D | `lista_tipo_registro` | `Realizado` / `Orçado` / `Reforecast` | Universal fixo | 3 valores; alimenta `sel_TipoA`/`sel_TipoB` (AJ5/AK5); igual para todos os clientes. |
| E | `lista_ancora` | Meses disponíveis (DATE, 1º dia) | Universal dinâmico | Início: `primeira_data_f_Base + 12 meses`. Fim: `dez` do último ano com `Orçado`; fallback `dez` do último ano com `Realizado`. Sequência contínua, sem gaps. |
| F | `lista_anos` | Anos disponíveis | Universal dinâmico | Início: primeiro ano da `f_Base`. Fim: mesma lógica de `lista_ancora`. |
| G | `lista_bu` | BUs do cliente + `"Todas"` | Cliente | Lido de `cad_cliente.bu_valores_validos`; `"Todas"` sempre ao final. |

**Intervalos nomeados:** o ETL cria/atualiza um `DefinedName` por coluna após cada escrita, com o range exato das linhas populadas. A `formula1` das validações de dados referencia o nome — nunca endereço fixo.

**`cad_cliente` — Defined Name:** neste momento apenas `mes_corte_realizado` recebe nome
(`cad_mes_corte`), pois é o único campo lido por fórmula no workbook (via `sel_MesCorte`
em §10.2.2). Os demais campos são informacionais.

**Seletores alimentados** (referência cruzada com §11.4):
`sel_Ancora` ← `lista_ancora` · `sel_PeriodoA/B` ← `lista_periodo` · `sel_RollingN` ← `lista_rolling_n` ·
`sel_AnoA/B` ← `lista_anos` · `sel_BU` ← `lista_bu` · `sel_Projecao` ← `lista_projecao` ·
`sel_TipoA/B` ← `lista_tipo_registro`

---

### 11.6 Paleta de cores — padrão universal AZ Resultados

Ler `SDD/DesignDoc_Relatorio.md`. O padrão definido nesse documento vale para todos os
clientes. Qualquer desvio deve ser declarado explicitamente em `cad_cliente/*.md` do cliente
em questão.

---

### 11.5 Lógica de período flexível (bloco Ano)

O SUMIFS do bloco Ano detecta o tipo de período pelo rótulo textual via `SEARCH`:

```excel
IF(ISNUMBER(SEARCH("Trim", periodo)),
   f_Base[trimestre],
   IF(ISNUMBER(SEARCH("Sem", periodo)),
      f_Base[semestre],
      f_Base[mes_num]))
```

Testando "Trim" antes de "Sem" — a **ordem dos IF importa** (§9, princípio "stringly-typed").
Valor numérico correspondente:

```excel
IF(ISNUMBER(SEARCH("Trim", periodo)), VALUE(LEFT(periodo,1)),
   IF(ISNUMBER(SEARCH("Sem",  periodo)), VALUE(LEFT(periodo,1)),
      MONTH(1 & periodo)))
```

Exemplo: `"1º Trim"` → trimestre=1; `"2º Sem"` → semestre=2; `"junho"` → mes_num=6.

---

### 11.8 DRE Gerencial — estrutura de linhas

| Elemento | Regra |
|---|---|
| Coluna A | Sempre vazia — estética e facilidade de impressão |
| Coluna B | Rótulos dos níveis. Recuo nativo Excel (`Alignment(indent=N)`) — nunca espaços no texto, pois `$B` é referenciado pelos SUMIFS |
| Recuo N1 | `indent=0` |
| Recuo N2 | `indent=2` |
| Recuo N3 | `indent=4` |
| Linha separadora | Meia altura (50% do padrão N3) antes de cada N1 e antes de cada KPI. **Exceção:** sem separador antes do 1º N1 |
| N2 | Sempre presente, mesmo quando há apenas 1 N3 abaixo |
| Ordem dentro de N1 | N2a → N3s de N2a → N2b → N3s de N2b → ... |
| Agrupamento N3 | `outline_level = 1` — o usuário oculta/expande via botão do Excel |
| RESULTADO INVESTIDORES | Linha roxo-logo ao final; sem separador especial antes |

#### 11.8.1 Receita Bruta — N2 promovido a primeira linha *(regra universal AZ)*

`dre_n1 = "Receita Líquida"` **não gera linha de cabeçalho** no DRE. Em seu lugar,
`dre_n2 = "Receita Bruta"` ocupa a primeira linha com **estilo N1** (cyan-pastel, indent=0).
Deduções mantém estilo N2 (azul-gelo) normal.

| Linha | Estilo | Fórmula | Obs |
|---|---|---|---|
| Receita Bruta | N1 (cyan-pastel) | SUM(N3 filhos) | Primeira linha; sem separador antes |
| N3 itens | N3 (sem fundo) | SUMIFS | outline_level=1 |
| *(meia linha)* | sep | — | Entre últimos N3s de Receita Bruta e demais N2 |
| Demais N2 (nomes variam por cliente) | N2 (azul-gelo) | SUM(N3 filhos) | Estilo N2 normal |
| N3 itens | N3 (sem fundo) | SUMIFS | |
| *(meia linha)* | sep | — | Antes do KPI |
| RECEITA LÍQUIDA | KPI (azul-petróleo) | SUM(Receita Bruta, demais N2) | |

**%AV:** todas as colunas de análise vertical dividem pela linha Receita Bruta
(`DATA_ROW` — primeira linha de dados do DRE).

**Contrato obrigatório do MapaAloc** — validado pelo builder a cada carga:
- O primeiro `dre_n1` (menor `dre_ordem`) DEVE ser `"Receita Líquida"`
- O primeiro `dre_n2` dentro de `"Receita Líquida"` (menor `dre_ordem`) DEVE ser `"Receita Bruta"`
- Violação gera `ValueError` e interrompe a geração do DRE

---

### 11.9 DFC — estrutura de linhas

O DFC é composto por duas seções na mesma aba, separadas por uma meia linha.

**Seção Resumo (topo):**

| Linha | Cor | Conteúdo |
|---|---|---|
| Atividades Operacionais | sem fundo | Total da atividade (SUMIFS por N1 DFC) |
| Atividades Não Operacionais | sem fundo | idem |
| Atividades de Investimento | sem fundo | idem |
| Atividades de Financiamento | sem fundo | idem |
| CAIXA - INÍCIO DO MÊS | cyan-pastel | Lê `f_SaldoBancos` |
| CAIXA - FIM DO MÊS | cyan-pastel | CAIXA INÍCIO + FLUXO DE CAIXA |
| FLUXO DE CAIXA | azul-petróleo | Σ das 4 atividades |

Sem separadores entre itens do resumo.

#### 11.9.1 Cobertura de colunas — Seção Resumo

> **Decisão 24/jun/2026:** colunas de agregação (Acumulado, Rolling N, Ano A/B, ▲%/▲R$) removidas do DFC — não agregavam leitura prática no contexto de fluxo de caixa. DFC exibe apenas os 13 meses mensais.

| Linha | VAL_COLS (C–O) | % AV |
|---|---|---|
| Atividades (×4) | SUMIFS `dfc_n1` + corte | — |
| CAIXA INÍCIO | `f_SaldoBancos` EOMONTH / cadeia FIM | — |
| CAIXA FIM | INÍCIO + FLUXO (VAL_COLS) | — |
| FLUXO DE CAIXA | Σ 4 Atividades | — |
| Movimentação Mês | Espelho FLUXO VAL_COLS | — |

> **% AV não existe no DFC.** As colunas PCT_COLS, ACUM_P e ROLL_P **não são criadas** — o DFC usa layout compacto com colunas value consecutivas (C-O), sem interleaving de % AV. Ver §11.9.2.

**Estilo das linhas de Atividades:**
- Coluna B (rótulo): `font(C_DARK, bold=True, size=10)`, sem preenchimento
- Colunas de valor (VAL_COLS): estilo N3 — sem preenchimento, `font(C_DARK, bold=False, size=10)`

#### 11.9.2 Layout de colunas do DFC *(estrutura diferente do DRE)*

O DFC usa colunas consecutivas para valores mensais, sem interleaving de % AV e sem colunas de agregação:

| Coluna(s) | Conteúdo | Largura |
|---|---|---|
| A | Separador | 1.86 |
| B | Rótulos | autofit |
| C – O | 13 meses de valor (consecutivos, C=mais antigo, O=sel_Ancora) | 11 |

**Header row 7 do DFC:**
- `C7`–`N7`: `=EDATE(<col_seguinte>7,-1)` em cadeia a partir de `O7`
- `O7`: `=sel_Ancora` (mês mais recente; formato `MMM/YYYY`)
- Formatação condicional âmbar aplicada a `C7:O7` (Realizado × Projeção)

**Seletores no DFC (linhas 4-6):** o DFC **não possui seletores interativos** próprios.
As fórmulas usam `named ranges` workbook-level (`sel_BU`, `sel_MesCorte`, `sel_Projecao`,
`sel_RollingN`, `sel_AnoA/B`, `sel_PeriodoA/B`) que apontam para a aba **DRE Gerencial**.
O usuário altera os seletores no DRE; o DFC reflete automaticamente.

**Seção Detalhe (após meia linha):**

Herda todas as regras do DRE (§11.8): meia linha antes de cada N1 (exceto o 1º), recuos, agrupamento N3, cores por nível.

| Nível | Cor | Exemplos de rótulo |
|---|---|---|
| N1 | cyan-pastel | Atividades Operacionais / Não Operacionais / Investimento / Financiamento |
| N2 | azul-gelo | Entradas [Atividade] / Saídas [Atividade] |
| N3 | sem fundo | categorias do MapaAloc |

- `SEM_DFC` e `Efeito Zero`: **ignorados** pelo builder — não geram linhas no DFC
- Última linha: `Movimentação Mês` (roxo-logo) — soma do fluxo do mês

---

### 11.10 Arquitetura dos módulos Python

O script de carga é organizado em módulos com responsabilidades distintas:

| Módulo | Responsabilidade |
|---|---|
| `etl.py` | Orquestrador — entry point `python etl.py <CODIGO>`; chama os demais na sequência correta |
| `extractors/extractor_<codigo>.py` | Leitura e normalização específica por cliente/formato |
| `staging.py` | Staging universal: validação, JOIN MapaAloc, enriquecimento, montagem da `f_Base` |
| `loader.py` | Leitura de fontes universais: MapaAloc e `f_SaldoBancos` existente |
| `builder.py` | Gera estrutura DRE/DFC/Lista a partir da hierarquia do MapaAloc |
| `writer.py` | Escreve o workbook com dados e estrutura gerada |

**Regra:** `builder.py` roda a cada carga — não há verificação de diff.

> **Nota de implementação:** a reordenação de abas usa `wb._sheets.sort()` (atributo privado
> do openpyxl, estável em 3.1.x). Alternativa sem API privada: criar as abas já na ordem
> correta em `writer.py`. Monitorar em atualizações do openpyxl. O DRE/DFC é sempre regenerado a partir do MapaAloc, garantindo sincronia automática quando N2 ou N3 são adicionados ou alterados.

### 11.11 Fórmulas por bloco de coluna

**N3 — valor mensal:** ver §11.3 (SUMIFS com corte determinístico).

**N2 — subtotal:**
```excel
=SUM(<células N3 filhas na mesma coluna>)
```
Builder gera referências explícitas a cada carga.

**N1 — subtotal:**
```excel
=SUM(<células N2 filhas na mesma coluna>)
```

**KPI:**
```excel
=<KPI_anterior> + SUM(<células N1 entre KPI_anterior e este KPI>)
```
Funciona como SUM direto pois valores chegam com sinal correto (§1.10).

**% AV** (colunas D, F, H … AB):
```excel
=C9/C$8
```
`C$8` = Receita Bruta (linha fixada pelo builder, coluna relativa). Sem SUMIFS separado.

**Acumulado** (AD):
```excel
=SUM(C9,E9,G9,I9,K9,M9,O9,Q9,S9,U9,W9,Y9,AA9)
```
Colunas não-contíguas; builder lista explicitamente.

**Rolling N** (AG) — SUMPRODUCT não-volátil:
```excel
=SUMPRODUCT(
  (COLUMN(C9:AA9) >= 29 - 2*sel_RollingN) *
  (MOD(COLUMN(C9:AA9) - 3, 2) = 0) *
  C9:AA9
)
```
`sel_RollingN` = Defined Name apontando para AG7. Range válido: 2–12.
`MOD(COLUMN-3,2)=0` seleciona colunas C, E, G … AA (valor); exclui D, F, H … AB (% AV).

**DFC — CAIXA INÍCIO DO MÊS:**
```excel
' 1ª coluna (C) — lê f_SaldoBancos:
=SUMIFS(f_SaldoBancos[valor],
  f_SaldoBancos[data], EOMONTH(C$7,-1),
  f_SaldoBancos[BU],  IF(sel_BU="Todas","*",sel_BU))

' Colunas seguintes (E, G …) — cadeia do mês anterior:
=<CAIXA_FIM da coluna anterior>
```

**DFC — CAIXA FIM DO MÊS:**
```excel
=<CAIXA_INÍCIO_col> + <FLUXO_DE_CAIXA_col>
```

**DFC — resumo (N1):**
Mesmo padrão do §11.3 com critério adicional `f_Base[dfc_n1] = <rótulo_N1>`.
Sem filtro por N2 ou N3 — agrega toda a atividade.

**Ano A / Ano B** (AJ / AK):
```excel
=SUMIFS(f_Base[valor],
  f_Base[ano],             sel_AnoA,
  f_Base[dre_n3],          n3_ref,
  f_Base[bu],              IF(sel_BU="Todas","*",sel_BU),
  f_Base[tipo_registro],   sel_TipoA,
  IF(ISNUMBER(SEARCH("Trim",sel_PeriodoA)), f_Base[trimestre],
     IF(ISNUMBER(SEARCH("Sem",sel_PeriodoA)), f_Base[semestre],
                                               f_Base[mes_num])),
  IF(ISNUMBER(SEARCH("Trim",sel_PeriodoA)), VALUE(LEFT(sel_PeriodoA,1)),
     IF(ISNUMBER(SEARCH("Sem",sel_PeriodoA)), VALUE(LEFT(sel_PeriodoA,1)),
                                               MATCH(sel_PeriodoA,lista_periodo,0))))
```
SUMIFS com coluna de período dinâmica no `criteria_range` via IF (§11.5). `sel_TipoA` controla
tipo de dado — sem corte automático neste bloco (design intencional; ver §11.3 exceção).
Ano B: mesma fórmula com `sel_AnoB` e `sel_TipoB`. `MATCH(sel_PeriodoA,lista_periodo,0)`
converte nome do mês em número via posição na `lista_periodo` — locale-independent.

**Variação** (AL / AM):
```excel
=IF(AK9=0,"", (AJ9-AK9)/ABS(AK9))   ← AL: ▲% (divisor absoluto — §10.7)
=AJ9-AK9                              ← AM: ▲R$
```

**% AV nos blocos agregados** — mesma regra: `valor / <mesma_coluna>$8` (linha de Receita Bruta).
Exemplo: Acumulado % AV = `=AD9/AD$8` · Rolling % AV = `=AG9/AG$8` · Ano A % AV = `=AJ9/AJ$8`.

### 11.12 Aba `cad_cliente` — layout

| Elemento | Regra |
|---|---|
| Estrutura | Vertical — 1 campo por linha; Col A = nome do campo; Col B = valor |
| Grupos | Cabeçalhos de seção (§3.1) em Col A em negrito; Col B vazia nas linhas de cabeçalho |
| Escrita | ETL escreve a aba a cada carga com os valores do `cad_cliente/*.md` do cliente |
| Defined Name | Apenas `cad_mes_corte` → aponta para a célula valor de `mes_corte_realizado` |
| Leitura por fórmula | `sel_MesCorte` (célula auxiliar) converte `cad_mes_corte` de texto `"AAAA-MM"` para DATE (§10.2.2) |
| Demais campos | Informacionais — sem Defined Name |

---

## 12. Critérios de Aceite — "Pronto para Entrega" *(NOVO)*

Relatório só é **entregável** quando todos os itens abaixo passam. **Tolerância universal de
bate: ±R$ 0,99** (diferenças menores que R$ 1,00 são ruído de arredondamento, aceitas).

- [ ] Contagem de colunas da `f_Base` confere com o declarado em `cad_cliente`
      (`23 + condicionais_ligadas + kpi_vivos`)
- [ ] `_sem_mapa = 0` — ou lista de categorias não mapeadas documentada e justificada
- [ ] DRE: soma das linhas N3 = subtotal N1 correspondente (cada cascata) — |diferença| ≤ R$ 0,99
- [ ] DRE: bate reverso de cada `kpi_*` de subtotal = cascata N3 correspondente (§5) — |diferença| ≤ R$ 0,99
- [ ] DFC: CAIXA Fim = CAIXA Início + Σ fluxos do período — |diferença| ≤ R$ 0,99
- [ ] Bate de colisão Realizado×Projeção = 0 meses em colisão (§4.3 item 5)
- [ ] N3-único verificado: 0 violações em `dre_n3` e `dfc_n3`
- [ ] BU distintas na `f_Base` ⊆ `bu_valores_validos` do `cad_cliente`
- [ ] Células de valor mensais com o IF de corte presente (§10.2.1 / §11.3); blocos Acumulado/Rolling/Ano A/B no DRE usam corte ou `sel_TipoA/B` (design §11.11); DFC usa apenas os 13 meses mensais — sem colunas de agregação (§11.9.1)
- [ ] Aba check: todas as sinalizações verdes, **exceto** pendências explicitamente documentadas

**Regra de bloqueio:** pendências documentadas (com ressalva escrita ao cliente — ex.: saldo
de abertura ausente §4.2, diferença fonte×controle manual) **não bloqueiam** entrega.
Sinalização vermelha **não documentada** bloqueia.

---

## 13. Justificativas — pontos da revisão NÃO ajustados *(NOVO)*

Registro de governança: itens levantados na revisão externa que foram **avaliados e
deliberadamente não alterados**, com a razão. Evita reabrir discussão fechada.

### 13.1 "Schema da fonte é caixa-preta" — NÃO PROCEDE

A fonte AB é inspecionável e estável. O arquivo de lançamentos tem colunas concretas e
tipadas: `data_caixa` (DATE), `historico`, `categoria`, `valor` (**numérico nativo**), `bu`,
`conta_bancaria`, `fornecedor_cliente`, `tipo_registro`, `validado`. Documentado em
`AB_Modelo_v1.md` §3.2 (histórico) e refletido na fonte real. **Não se cria
`schemas_fonte/AB_schema_v1.md`** — seria documentação redundante de informação já existente
no `cad_cliente` + fonte. Se um novo ERP entrar com schema instável, aí sim se documenta o
schema **daquele** ERP.

### 13.2 `conversao_defensiva_valor = Sim` no AB — mantido por precaução, não necessidade

No AB o `valor` já chega numérico nativo, então a conversão defensiva é **redundante na
prática**. Mantida ligada como rede barata (custo nulo se o valor já é número). A conversão é
necessária de fato no GCG/Conta Azul, onde valores vêm como texto formatado (`"1.234,56"`).
Não é inconsistência — é defesa uniforme de baixo custo.

### 13.3 ETL deve podar Realizado futuro — REJEITADO (decisão de simplicidade)

A revisão sugeriu o staging excluir `Realizado` com `data_caixa > mes_corte`. **Rejeitado.**
Coexistência na `f_Base` é permitida (§10.2.1); o SUMIFS resolve o corte. Razão: o ETL não
precisa conhecer `mes_corte`, a fonte do cliente pode conter Realizado adiantado sem
pré-processamento, e o ponto único de verdade do corte fica no relatório. **Contrapartida
aceita e mitigada:** o bate de colisão (§4.3 item 5) vira controle essencial e o IF de corte
é obrigatório em toda célula (§12, checklist).

### 13.4 Fallback de saldo `#N/D` em vez de `0` — REJEITADO

A revisão pediu trocar `saldo_inicial = 0` por `#N/D`. **Rejeitado.** `#N/D` propaga erro e
quebra todas as somas de fluxo a jusante, deixando o DFC inteiro inutilizável por um único
dado faltante. Escolha: DFC **funcional** com CAIXA Início = 0 + aviso em `f_Erros` + check
vermelha (§4.2). O alerta cumpre o objetivo de "não enganar" sem sacrificar a usabilidade do
relatório. Quando o operador preencher o mês de abertura, o saldo real entra automaticamente.

### 13.5 Inventário de referências defasadas — corrigir na próxima geração de docs

Rebaixamento do v7 e dos `*_Modelo_v1.md` aplicado em §0. Inventário completo das menções a
versões antigas, para a varredura final quando esta janela fechar e o `v15` for gerado:

| Arquivo | Menção defasada | Ação |
|---|---|---|
| `GCG_Modelo_v1.md` | "34 colunas / v6"; cita `AZ_Modelo_Padrao_v6.md`, `Checkpoint_v7` | Histórico; substituído por `cad_cliente_GCG.md` |
| `AB_Modelo_v1.md` | "37 colunas / v7"; cita `Checkpoint_v8` | Histórico; substituído por `cad_cliente_AB.md` |
| `GCG_Modelo_v1.md` §8 | aponta `GCG_PowerQuery_Codigos_M_v2.md` | Verificar existência ou remover referência |
| `cad_cliente_GCG.md` §1 | `doc_especifico = GCG_Modelo_v1.md (defasado)` | Atualizar na janela GCG |

> `AZ_Modelo_Padrao_v7/v8`, `v13` e Checkpoints `vN` **não estão neste repositório de projeto**
> — só citados. Se existirem em outro local, aplicar o mesmo rebaixamento do §0.

### 13.6 Validação do `AB_MapaAloc_v11` externo — pendência legítima, fora do escopo desta janela

Validação da exceção `Impostos sobre Resultado` como N1 próprio no `AB_MapaAloc_v11` canônico
é pendência de governance do cliente AB. Ver `cad_cliente_AB.md` §5.

---

*Versão 20 — 23/jun/2026 — substitui v19. Fonte de verdade corrente. Pendências em aberto no cabeçalho.*
*Fonte de verdade corrente. Conteúdo de cliente em `cad_cliente/*.md`.*
*Contrato `f_Base` = 23 + condicionais_ligadas + kpi_vivos (por cliente).*
*Contrato MapaAloc = 25 colunas, 5 blocos.*
*Projeções/Forecast — design FECHADO; implementação pendente por cliente.*
*v7 e `*_Modelo_v1.md` rebaixados a histórico (§0). Critérios de aceite em §12. Justificativas em §13.*
*Paleta de cores universal em `SDD/DesignDoc_Relatorio.md` (§11.6). Aba Lista documentada em §11.7.*
