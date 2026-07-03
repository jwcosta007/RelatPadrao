# Changelog — RelatPadrao / AZ Resultados

Histório de mudanças na especificação e bugs resolvidos.
Mudanças de código rastreadas via `git log`.

---

## Especificação — Histórico de versões

### v25 (03/jul/2026) — AB: novo formato de origem + f_bancos preenchido

- `extractor_ab.py`: adaptado para ler o novo formato de export "consolidado" da AB —
  primeira aba do arquivo (nome livre, ex. `Sheet1`), colunas já no schema final
  (`data_caixa`, `historico`, `categoria`, `valor`, `bu`, `conta_bancaria`,
  `fornecedor_cliente`, `tipo_registro`). Substitui o formato antigo (aba fixa `f_Lctos`,
  colunas em português `Data`/`Histórico`/`Categoria`/`BU`/`Conta`/`Fornecedor-Cliente`/
  `Tipo Registro`) — sem suporte a ambos, decisão de James (formato antigo descontinuado).
- `assets/dados/AB - AB Aeterno/f_bancos/AB_f_Bancos.xlsx` preenchido por James — DFC AB
  não depende mais do fallback CAIXA INÍCIO = 0.

### v24 (30/jun/2026) — Implantação GCG: cadastro completo

- `cad_cliente_GCG.json` criado — passa validação Pydantic (`_CadClienteConfig`).
- `cad_cliente_GCG.md` v03 — campos completos: segmento Estética, BUs CPF/CNPJ,
  5 condicionais ligadas (conta_bancaria, fornecedor_cliente, data_competencia,
  data_vencimento, valor_original), cascade DRE em 5 estágios (sem Impostos sobre Resultado),
  de-para conta bancária → BU com 14 contas mapeadas, shape f_Base 35 colunas (23+5+7).
- `GCG_MapaAloc.xlsx` — 166 categorias, 26 colunas, 5 blocos, 7 KPIs ativos.
  `kpi_cmv` com 4 Sim no mapa mas pendente ativação em código (P8).

### v23 (30/jun/2026) — Logging em arquivo e alinhamento de type hints

- `etl.py`: `_setup_logging()` substitui `basicConfig`; grava em `logs/etl.log`
  via `RotatingFileHandler` (1 MB, 3 backups, UTF-8) além do console.
- `loader.py`: `list[dict]` → `list[dict[str, Any]]` em `load_f_bancos` e `_erro_bancos`;
  `from typing import Any` adicionado. Alinha com o padrão de type hints já adotado nos demais módulos.
- `.gitignore`: `logs/` adicionado.

### v22 (30/jun/2026) — Contrato universal f_Bancos.xlsx

- §4.2: contrato do arquivo `f_Bancos.xlsx` estabilizado como universal (sem mapeamento por cliente):
  colunas `data | BU | nome_conta | saldo` em todos os clientes.
- §4.2: `f_bancos_col_map` **removido** do JSON e do loader — não existe mais.
- §4.2: normalização de data documentada — qualquer data do mês aceita, convertida para `AAAA-MM-01`.
- §4.2: duplicatas — mesmo `(BU, nome_conta, mês)`: aviso em `f_Erros`, mantém maior data; não bloqueante.
- §11.11: fórmula CAIXA INÍCIO corrigida — `EOMONTH(C$7,-1)` → `EDATE(C$7,-1)` (EOMONTH devolvia
  último dia do mês anterior; com datas no dia 01, EDATE é o correto).
- §6.9: fallback atualizado — `f_SaldoBancos` vazio (tabela sem linhas), não mais `saldo 0` via seed.
- `cad_cliente_AB.json`: campo `saldo_seed` removido — substituído pelo mecanismo de `f_bancos/`.
- `cad_cliente_GCG.md`: seção `f_bancos/` adicionada documentando o arquivo de referência.

### v21 (30/jun/2026) — f_SaldoBancos por convenção de pasta

- §4.2: origem de saldos bancários redesenhada — ETL sempre procura `f_bancos/` na pasta do
  cliente; presença da pasta ativa leitura; ausência aciona fallback (saldo 0 + aviso em
  `f_Erros`). Elimina necessidade de flag no `cad_cliente`. Dois avisos distintos:
  pasta/arquivo ausente vs mês de abertura faltando no arquivo.
- §4.4: `f_bancos/` adicionada à estrutura canônica de pastas (opcional); nota de que
  `path_bancos` não existe no JSON — convenção é a especificação.
- §6.9: decisão travada atualizada para refletir origem por convenção.
- `cad_cliente_AB.md` §7: débito técnico registrado — criar `f_Bancos.xlsx` para AB.
- `ROADMAP.md`: item de criação de `f_bancos/` para AB adicionado à próxima iteração.

### v20 (23/jun/2026) — consolidado de v19

- §11.9.1: % AV corrigida — colunas não criadas (não "ocultadas"); referência ao novo §11.9.2
- §11.9.2 NOVO: layout de colunas DFC (estrutura compacta sem interleaving de % AV)
- §11.9.2 NOVO: ausência de seletores interativos no DFC (linhas 4-6); controle via DRE
- §11.6: referência atualizada para `DesignDoc_Relatorio.md`

### v19 (jun/2026) — consolidado de v18

- §11.9: cobertura de colunas do DFC Resumo por linha (Atividades, CAIXA INÍCIO/FIM, FLUXO, Movimentação Mês)
- §11.9: fórmula `_dfc_n1_ano` para blocos ANO A/B das linhas de Atividades
- §11.9: % AV **não utilizada** no DFC — colunas PCT_COLS, ACUM_P, ROLL_P existem no layout mas ficam vazias
- §11.9: estilo das linhas de Atividades — col B negrito sem fill; colunas de valor → N3 (sem fill, sem negrito)

### v18 (jun/2026) — consolidado de v17

- §11.4: rótulos de seletores (B4=`"Unidade"`, B5=`"Mês/Ano"`, E5=`"Projeção"`), merge `F5:G5` para `sel_Projecao`, valores default de `sel_Ancora` e `sel_Projecao`
- §11.4: coluna % AV — descrição corrigida para `"% AV"`
- §11.4.1: `sel_Projecao` documentado como `F5:G5` mesclado com âncora em `F5`

### v17/v16 (jun/2026) — consolidado de v14b

- §1.10: convenção de sinal em `f_Lctos`
- §11.4: seletores AJ5/AK5 (`sel_TipoA`/`sel_TipoB`) para Ano A/B; DRE e DFC declarados idênticos
- §11.6: paleta de cores universal (`DesignDoc_Relatorio.md`)
- §11.7: aba `Lista` — estrutura completa, `lista_tipo_registro` (Col D), intervalos nomeados, `lista_rolling_n` 2–12
- §11.8: estrutura de linhas DRE Gerencial
- §11.9: estrutura de linhas DFC
- §11.10: arquitetura modular Python
- §11.11: fórmulas por bloco de coluna (N2/N1/KPI/% AV/Acumulado/Rolling/DFC/Ano A/B/Variação)
- §11.12: layout da aba `cad_cliente`

### v15b/c/d (jun/2026) — sobre v14b

- §11.8 NOVO: estrutura de linhas do DRE Gerencial
- §11.9 NOVO: estrutura de linhas do DFC
- §11.10 NOVO: arquitetura dos módulos Python
- §11.4: layout de seletores DRE e DFC declarado idêntico; desvios do arquivo-piloto documentados como não replicáveis
- §11.6 NOVO: paleta de cores — padrão universal AZ Resultados
- §11.7 NOVO: aba `Lista` — estrutura de colunas, classificação, intervalos nomeados

### v14b (mai/2026) — sobre v14.0

- §0: `AZ_Modelo_Padrao_v7.md` rebaixado a histórico
- §4.2: fallback saldo ausente
- §10.2 + §11.3: contrato de tipo das datas
- §11.4: Defined Names obrigatórios
- §12: Critérios de Aceite
- §13: justificativas de pontos não ajustados

### v14.0 (mai/2026) — sobre v13

- §1.3: `fornecedor_cliente`
- §1.6 / §6.3: `d_Calendario` condicional
- §1.9: flag no `cad_cliente`
- §4.1: erro técnico vs `_sem_mapa`
- §4.2: `f_SaldoBancos` manual
- §6.8: `_sem_mapa` inclusivo
- §11: estrutura do workbook

---

## Bugs já resolvidos — não repetir

| Bug | Correção definitiva |
|---|---|
| Nomes `let` duplicados no mesmo escopo M | Nomes distintos por passo |
| Lazy evaluation pula validação não referenciada | Validação inline no passo que consome |
| Loop O(n²) em `d_Calendario` (`dia_util_num`) | `List.Buffer` + `List.PositionOf` + `List.Range` |
| `_sem_mapa` com falso negativo | `dre_n1 IS NULL` após LEFT JOIN (Python / `JoinKind.LeftOuter` em M) |
| `JoinKind.Left` em Power Query Desktop | `JoinKind.LeftOuter` |
| Header de duas linhas no MapaAloc | `Table.Skip(Aba,1)` → `Table.PromoteHeaders` |
| Campos ausentes preenchidos com placeholder | `null`, nunca `"ND"`/`"BRL"`/string vazia |
| Mês pt-BR dependente de locale | Lista estática no ETL |
| `MONTH(1&sel_Periodo)` locale-dependente na fórmula Excel (falha silenciosa em EN-US) | `MATCH(sel_Periodo,lista_periodo,0)` — posição na lista = número do mês, sem dependência de locale |
| Colunas AL (▲%) e AM (▲R$) sem fill/fonte no DRE | `_vp` e `_va` adicionados a `_sty_cols` em `_write_items()` |
| Valores `###` em colunas de acumulado por largura insuficiente | Formato `#,##0.00` → `#,##0` (sem casas decimais) reduz largura dos números |
