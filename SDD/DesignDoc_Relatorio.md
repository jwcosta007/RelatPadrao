# DesignDoc_Relatorio — Paleta de Cores, Hierarquia Visual e Seletores

**Status:** validado (23/jun/2026)
**Escopo:** padrão universal AZ Resultados — aplica-se a **todos** os clientes e arquivos de relatório gerados pelo Modelo Padrão. Qualquer desvio deve ser documentado em `cad_cliente/*.md` do cliente em questão.
**Referência nas regras:** `SDD/RegrasRelatPadrao.md` §11.6

---

## Paleta de cores

| Hex ARGB   | Nome          | RGB visual    |
|------------|---------------|---------------|
| FF175179   | azul-petróleo | escuro        |
| FF96CCD4   | cyan-pastel   | médio         |
| FFE3F3FD   | azul-gelo     | claro         |
| FFA64A8B   | roxo-logo     | assinatura AZ |
| FFF9F5CE   | creme         | seletores     |
| —          | sem fundo     | branco/padrão |

---

## DRE Gerencial — hierarquia de cores

| Cor                    | Linhas                                                                                                                                                                              | Obs                          |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------|
| FF175179 azul-petróleo | RECEITA LÍQUIDA · MARGEM DE CONTRIBUIÇÃO · EBITDA · LUCRO LÍQUIDO                                                                                                                  | 4 KPIs principais; altura 15 |
| FF96CCD4 cyan-pastel   | Todos os N1 do DRE · Receita Bruta (N2 promovido — §11.8.1)                                                                                                                        | —                            |
| FFE3F3FD azul-gelo     | Todos os N2 do DRE (exceto Receita Bruta)                                                                                                                                           | —                            |
| sem fundo              | N3 detalhe                                                                                                                                                                          | —                            |
| FFA64A8B roxo-logo     | RESULTADO INVESTIDORES — última linha                                                                                                                                               | assinatura AZ                |

---

## DFC — hierarquia de cores

| Cor                    | Linhas                                                                              | Obs           |
|------------------------|-------------------------------------------------------------------------------------|---------------|
| FF175179 azul-petróleo | FLUXO DE CAIXA (total principal)                                                    | —             |
| FF96CCD4 cyan-pastel   | CAIXA INÍCIO/FIM DO MÊS                                                             | —             |
| sem fundo (col B negrito) | Atividades Operacionais / Não Op. / Investimento / Financiamento — Seção Resumo. Col B: dark, bold, 10pt. Colunas de valor: N3 (sem fill, dark, não-negrito, 10pt) | —  |
| FFE3F3FD azul-gelo     | Entradas/Saídas dentro de cada atividade (N2) — Seção Detalhe                       | —             |
| sem fundo              | N3 detalhe — Seção Detalhe                                                          | —             |
| FFA64A8B roxo-logo     | Movimentação Mês — última linha                                                      | assinatura AZ |

> **% AV no DFC:** colunas PCT_COLS, ACUM_P e ROLL_P **não são criadas** na aba DFC. O layout DFC usa colunas value consecutivas (C-O) sem interleaving. % AV existe apenas no DRE Gerencial. Ver §11.9.3 das Regras.

---

## Tipografia e alturas de linha

| Elemento | Fonte | Altura de linha |
|---|---|---|
| KPI (azul-petróleo) | tamanho 11, branca, negrito | padrão para fonte 11 |
| N1 (cyan-pastel) | tamanho 10, escura, negrito | padrão para fonte 10 |
| N2 (azul-gelo) | tamanho 10, escura, sem negrito | padrão para fonte 10 |
| N3 (sem fundo) | tamanho 10, padrão, sem negrito | padrão para fonte 10 |
| Roxo-logo | tamanho 11, branca, negrito | padrão para fonte 11 |
| Linha separadora | — | 50% da altura padrão N3 |

**Indentação coluna B** (recuo nativo Excel — `Alignment(indent=N)`; nunca espaços no texto):

| Nível | indent |
|---|---|
| N1 | 0 |
| N2 | 2 |
| N3 | 4 |

**DFC — seção resumo:** as 4 linhas de atividades (Operacionais, Não Operacionais, Investimento, Financiamento) são exibidas sem cor de fundo. CAIXA INÍCIO/FIM seguem cyan-pastel; FLUXO DE CAIXA segue azul-petróleo.

---

## Seletores de usuário

> **Âmbito:** seletores interativos existem apenas no **DRE Gerencial**. A aba DFC não possui seletores próprios — usa os named ranges do DRE. Ver §DFC — Estrutura de colunas.

`FFF9F5CE` (creme) é **reservado exclusivamente** para células manipuláveis pelo usuário
final. Nenhum outro elemento do workbook usa este fundo.

**Estilo obrigatório de todo seletor:**
- Fundo: `FFF9F5CE`
- Fonte: negrito, `FF175179` (azul-petróleo)
- Borda: fina (`thin`), cor `FF96CCD4` (cyan-pastel), externa (perímetro da célula ou do bloco mesclado)

**Estilo obrigatório de todo rótulo de seletor** (B4, B5, E5 e equivalentes em outros relatórios):
- Fundo: sem preenchimento
- Fonte: padrão (não negrito, não colorida)
- Borda: fina (`thin`), cor `FF96CCD4` (cyan-pastel), externa

**`sel_BU` — mesclagem horizontal:**
- Mesclar sempre 5 células (`C4:G4`) para acomodar nomes longos de BU sem impactar a largura das demais colunas.
- `DefinedName sel_BU` aponta para a célula âncora (`C4`).
- openpyxl: `ws.merge_cells('C4:G4')`, valor e formatação em `ws['C4']`.

**`sel_Projecao` — mesclagem horizontal:**
- Mesclar 2 células (`F5:G5`) para acomodar o rótulo do valor selecionado.
- `DefinedName sel_Projecao` aponta para a célula âncora (`F5`).
- openpyxl: `ws.merge_cells('F5:G5')`, valor e formatação em `ws['F5']`.

**Bordas em células mescladas (openpyxl):**
A borda externa envolve o bloco mesclado como um único retângulo. Aplicar nas células do perímetro:
- Borda `top` em todas as células da primeira linha do merge
- Borda `bottom` em todas as células da última linha do merge
- Borda `left` na célula mais à esquerda do merge
- Borda `right` na célula mais à direita do merge

---

## Cabeçalho de datas — sinalização Realizado × Projeção

A linha de cabeçalho de datas (linha 7 do DRE e DFC) usa formatação condicional para
sinalizar visualmente a fronteira entre Realizado e Projeção.

| Estado | Fundo | Fonte |
|---|---|---|
| `mes <= sel_MesCorte` (Realizado) | `FF175179` azul-petróleo | branca, negrito |
| `mes > sel_MesCorte` (Projeção) | `FFB8860B` âmbar escuro | branca, negrito |

**Implementação DRE:** `FormulaRule` aplicada ao range `C7:AA7` com fórmula `=C7>sel_MesCorte`.
**Implementação DFC:** range `C7:O7` (colunas value consecutivas).
O Excel ajusta a referência célula a célula; `sel_MesCorte` é o Defined Name do workbook.

**Decisão fechada — sinalização restrita ao cabeçalho:**
A mudança de cor não se estende às linhas de subtotal (N1, KPI) nem ao corpo do relatório.
Motivo: cor no corpo já carrega significado hierárquico (N1/N2/KPI). Adicionar o eixo
Realizado×Projeção nas mesmas células criaria ambiguidade de leitura. O cabeçalho âmbar
é sinal de coluna — cobre toda a coluna abaixo sem necessidade de reforço linha a linha.

---

## Formatação de células e números

### Seletor de data (`sel_Ancora` — C5)

`C5` armazena uma data (1º dia do mês âncora). Formato: `"MMM/YYYY"` (ex.: `jun/2026`).
openpyxl: `ws["C5"].number_format = "MMM/YYYY"`

### Cabeçalhos de data — linha 7

Células de cabeçalho de mês contêm fórmulas de data (EDATE/sel_Ancora).
Formato: `"MMM/YYYY"` em ambas as abas.
- **DRE:** VAL_COLS (C, E, G … AA) — colunas alternadas (interleaved com % AV)
- **DFC:** C–O consecutivas (sem interleaving)

### Valores monetários

Formato: `"#,##0.00;-#,##0.00"` — notação OOXML (EN); exibe `1.234,56` em PT-BR. Sem prefixo de moeda; negativos com sinal à esquerda.

**DRE Gerencial:**

| Bloco | Colunas DRE |
|---|---|
| 13 meses | VAL_COLS (C, E, G … AA) |
| Acumulado | AD (`ACUM_V`) |
| Rolling N | AG (`ROLL_V`) |
| Ano A / Ano B | AJ, AK |
| Variação R$ | AM |

**DFC** *(colunas diferentes)*: apenas C–O (13 meses) — sem colunas de agregação. Ver §DFC — Estrutura de colunas.

### Análise vertical e variação %

Formato: `"#,##0.0%_);-#,##0.0%"` — notação OOXML (EN); exibe `12,5%` em PT-BR.

**DRE Gerencial** *(% AV existe apenas no DRE)*:

| Bloco | Colunas DRE |
|---|---|
| % AV — 13 meses | PCT_COLS (D, F, H … AB) |
| % AV — Acumulado | AE (`ACUM_P`) |
| % AV — Rolling N | AH (`ROLL_P`) |
| Variação % | AL |

**DFC**: sem colunas % AV e sem colunas de agregação — apenas os 13 meses mensais (C–O).

### Seletor Rolling N (AG7)
Formato: `"00"` — exibe valores de 2–12 sempre com 2 dígitos (ex.: `06`).

> Todos os formatos numéricos respeitam as cores, tamanhos e negritos definidos nas seções Paleta e Tipografia.

---

## Visual geral

### Linhas de grade
Todas as abas de relatório (DRE Gerencial, DFC) têm as linhas de grade desativadas.
openpyxl: `ws.sheet_view.showGridLines = False`

### Logotipo
- **Posição:** B2 como referência — âncora absoluta, não está dentro da célula
- **Altura:** 25 px; largura proporcional (aspect ratio original mantido)
- **Âncora:** `AbsoluteAnchor` — não se move nem redimensiona ao alterar colunas ou linhas
- **Linha 2:** altura ajustada para `18.75 pt` (= 25 px)
- **Origem do arquivo:** `LOGO_PATH` = `assets/logo/` na raiz do projeto — configurado por cliente em `etl_ab.py`
- **Coordenadas EMU:** X = largura col A (18 px), Y = altura row 1 (20 px)

openpyxl:
```python
img.anchor = AbsoluteAnchor(
    pos=XDRPoint2D(pixels_to_EMU(18), pixels_to_EMU(20)),
    ext=XDRPositiveSize2D(pixels_to_EMU(width), pixels_to_EMU(25)),
)
ws.row_dimensions[2].height = 18.75
```

---

## Agrupamento de linhas e colunas

### Linhas — N3 (detalhe)

N3 rows são agrupadas para permitir colapso pelo usuário. O botão +/− deve aparecer
**acima** do grupo (junto à linha N2), não abaixo.

```python
ws.sheet_properties.outlinePr.summaryBelow = False   # botão acima
ws.row_dimensions[row].outline_level = 1
ws.row_dimensions[row].hidden = False
```

### Colunas — % AV

Cada coluna % AV é agrupada com sua coluna de valor de referência. O botão +/− deve
aparecer **à esquerda** do grupo (junto à coluna de valor), permitindo ocultar o % AV
sem perder o valor.

```python
ws.sheet_properties.outlinePr.summaryRight = False   # botão à esquerda
ws.column_dimensions[col].outline_level = 1
ws.column_dimensions[col].hidden = False
```

Colunas % AV a agrupar:

| Bloco | Colunas % AV | Coluna valor de referência |
|---|---|---|
| 13 meses | D, F, H, J, L, N, P, R, T, V, X, Z, AB | C, E, G, I, K, M, O, Q, S, U, W, Y, AA |
| Acumulado | AE | AD |
| Rolling N | AH | AG |

> `summaryBelow` e `summaryRight` são propriedades da aba — definir uma vez por aba.
> Verificado: ambas sobrevivem a save/reload em openpyxl 3.1.5.

---

## DFC — Estrutura de colunas *(diferente do DRE)*

O DFC tem layout mínimo — sem colunas % AV e sem colunas de agregação:

> **Decisão 24/jun/2026:** Acumulado, Rolling N, Ano A/B, ▲%/▲R$ removidos do DFC. DRE mantém todas as colunas de agregação.

| Bloco | Colunas | Largura |
|---|---|---|
| Separador | A | 1.86 |
| Rótulos | B | autofit |
| 13 meses (value) | C – O | 11 |

**Seletores:** DFC não possui seletores interativos (linhas 4-6 são vazias). Controle via DRE Gerencial.

---

## Larguras de coluna

### Colunas separadoras (A, AC, AF, AI, AN)
Sempre vazias — espaço visual entre blocos. Largura: `1.86` unidades Excel (≈ 18 px a 125% DPI).
openpyxl: `ws.column_dimensions[col].width = 1.86`

### Colunas de valor monetário
Largura: `11` — VAL_COLS (C, E, G … AA), ACUM_V (AD), ROLL_V (AG), ANO_A (AJ), ANO_B (AK), VAR_ABS (AM).

### Colunas de análise vertical e variação %
Largura: `7` — PCT_COLS (D, F, H … AB), ACUM_P (AE), ROLL_P (AH), VAR_PCT (AL).

### Coluna B — rótulos (autofit)
Largura = `min(max_len_labels + 2, 50)`. Calculada a cada carga com base no comprimento máximo dos rótulos presentes na coluna.

### Tipografia das colunas % AV
Mesma fonte das colunas de valor da linha correspondente: N3 = size 10 sem negrito; N2 = size 10 sem negrito; N1 = size 10 negrito; KPI = size 11 negrito.

---

## Regras de aplicação (openpyxl)

- Fundo via `PatternFill("solid", fgColor="XXXXXX")` — 6 dígitos hex sem prefixo `FF`
- Fonte dos KPIs principais (azul-petróleo): branca, negrito
- Fonte N1 cyan-pastel: escura (padrão), negrito
- Fonte N2 azul-gelo: escura (padrão), sem negrito
- Fonte N3: padrão, sem negrito
- Roxo-logo: fonte branca, negrito
- Altura das linhas KPI (azul-petróleo): 15 pt
- Seletores: fundo `FFF9F5CE`, fonte negrito `175179`, borda thin `96CCD4` externa; `sel_BU` merge `C4:G4`; `sel_Projecao` merge `F5:G5`
- Rótulos de seletor: sem preenchimento, borda thin `96CCD4` externa
- Formato data: `"MMM/YYYY"` — `sel_Ancora` (C5) e VAL_COLS linha 7
- Formato monetário: `"#,##0.00;-#,##0.00"` — corpo do relatório (valores); notação OOXML
- Formato percentual: `"#,##0.0%_);-#,##0.0%"` — corpo do relatório (% AV e variação %); notação OOXML
- % AV (PCT_COLS, ACUM_P, ROLL_P): populadas apenas no DRE Gerencial; no DFC estas colunas **não existem** (layout diferente — ver §11.9.3 das Regras)
