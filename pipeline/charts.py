"""
charts.py — Criação e injeção de gráficos no workbook AZ Resultados.

Fluxo de dois passos:
  1. build_*(): cria gráfico via openpyxl API (registra âncora e refs no drawing XML)
  2. patch_charts(): após wb.save(), substitui chart*.xml pelo template com formatação
     completa — necessário porque openpyxl não expõe tipografia de eixos/labels via API.

Para adicionar novo gráfico:
  - Escreva build_<nome>(ws, ...) e defina _<NOME>_XML
  - Adicione a entrada em patch_charts() com o caminho 'xl/charts/chart{n}.xml'
"""

import os
import zipfile
from pathlib import Path
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.legend import Legend
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.data_source import NumFmt as ChartNumFmt, StrRef as ChartStrRef
from openpyxl.chart.series import SeriesLabel
from openpyxl.drawing.spreadsheet_drawing import (
    TwoCellAnchor, AnchorMarker as SpreadshAnchor,
)
from openpyxl.utils import column_index_from_string as col2idx

_C_PETROLEO = "175179"
_C_CYAN     = "96CCD4"

# ─────────────────────────────────────────────────────────────────────────────
# KPI — Receita Líquida (chart1)
# Layout fixo: sheet "KPIs", HDR_ROW=7, DATA_ROW=8, colunas C:O
# ─────────────────────────────────────────────────────────────────────────────

_KPI_CHART_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<c:chartSpace'
    ' xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"'
    ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<c:date1904 val="0"/><c:lang val="pt-BR"/><c:roundedCorners val="0"/>'
    '<c:chart>'

    '<c:title>'
    '<c:tx><c:rich>'
    '<a:bodyPr/><a:lstStyle/>'
    '<a:p><a:pPr><a:defRPr b="1" sz="1400"/></a:pPr>'
    '<a:r><a:rPr lang="pt-BR" b="1" sz="1400"/>'
    '<a:t>Receita Líquida</a:t>'
    '</a:r></a:p>'
    '</c:rich></c:tx>'
    '<c:overlay val="0"/>'
    '</c:title>'
    '<c:autoTitleDeleted val="0"/>'

    '<c:plotArea>'
    '<c:barChart>'
    '<c:barDir val="col"/><c:grouping val="clustered"/>'
    '<c:varyColors val="0"/>'
    '<c:gapWidth val="100"/>'
    '<c:ser>'
    '<c:idx val="0"/><c:order val="0"/>'
    '<c:tx><c:strRef><c:f>KPIs!$B$8</c:f></c:strRef></c:tx>'
    '<c:spPr>'
    '<a:solidFill><a:srgbClr val="175179"/></a:solidFill>'
    '<a:ln><a:noFill/></a:ln>'
    '</c:spPr>'
    '<c:invertIfNegative val="0"/>'
    '<c:dLbls>'
    '<c:numFmt formatCode="#,##0.0,&quot;K&quot;" sourceLinked="0"/>'
    '<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'
    '<c:txPr><a:bodyPr/><a:lstStyle/>'
    '<a:p><a:pPr><a:defRPr sz="900" b="1"/></a:pPr></a:p>'
    '</c:txPr>'
    '<c:showLegendKey val="0"/><c:showVal val="1"/>'
    '<c:showCatName val="0"/><c:showSerName val="0"/>'
    '<c:showPercent val="0"/><c:showBubbleSize val="0"/>'
    '<c:showLeaderLines val="0"/>'
    '</c:dLbls>'
    '<c:cat><c:numRef><c:f>KPIs!$C$7:$O$7</c:f></c:numRef></c:cat>'
    '<c:val><c:numRef><c:f>KPIs!$C$8:$O$8</c:f></c:numRef></c:val>'
    '</c:ser>'
    '<c:axId val="1"/><c:axId val="2"/>'
    '</c:barChart>'

    '<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'

    '<c:catAx>'
    '<c:axId val="1"/>'
    '<c:scaling><c:orientation val="minMax"/></c:scaling>'
    '<c:delete val="0"/><c:axPos val="b"/>'
    '<c:numFmt formatCode="mmm/yyyy" sourceLinked="0"/>'
    '<c:majorTickMark val="out"/>'
    '<c:minorTickMark val="none"/>'
    '<c:tickLblPos val="nextTo"/>'
    '<c:txPr><a:bodyPr/><a:lstStyle/>'
    '<a:p><a:pPr><a:defRPr b="1" sz="800"/></a:pPr></a:p>'
    '</c:txPr>'
    '<c:crossAx val="2"/>'
    '<c:crosses val="autoZero"/><c:auto val="1"/>'
    '<c:lblAlgn val="ctr"/><c:lblOffset val="100"/>'
    '</c:catAx>'

    '<c:valAx>'
    '<c:axId val="2"/>'
    '<c:scaling>'
    '<c:orientation val="minMax"/>'
    '<c:min val="0"/>'
    '</c:scaling>'
    '<c:delete val="0"/><c:axPos val="l"/>'
    '<c:numFmt formatCode="#,##0,&quot;K&quot;" sourceLinked="0"/>'
    '<c:majorTickMark val="out"/>'
    '<c:minorTickMark val="none"/>'
    '<c:tickLblPos val="nextTo"/>'
    '<c:crossAx val="1"/>'
    '<c:crosses val="autoZero"/>'
    '<c:crossBetween val="between"/>'
    '<c:majorUnit val="100000"/>'
    '</c:valAx>'

    '</c:plotArea>'
    '<c:legend><c:legendPos val="t"/><c:overlay val="0"/></c:legend>'
    '<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/>'
    '</c:chart>'

    '<c:spPr>'
    '<a:solidFill><a:schemeClr val="bg1"/></a:solidFill>'
    '<a:ln w="9525">'
    '<a:solidFill><a:srgbClr val="96CCD4"/></a:solidFill>'
    '</a:ln>'
    '</c:spPr>'
    '</c:chartSpace>'
).encode('utf-8')


def build_kpi_receita_liquida(ws, hdr_row: int, data_row: int) -> None:
    """Registra gráfico de barras KPI no drawing do workbook (âncora C11:O16).
    A formatação completa é injetada por patch_charts() após wb.save().
    """
    chart = BarChart()
    chart.type     = "col"
    chart.grouping = "clustered"

    data_ref = Reference(ws, min_col=col2idx("C"), max_col=col2idx("O"),
                         min_row=data_row, max_row=data_row)
    chart.add_data(data_ref)
    cats_ref = Reference(ws, min_col=col2idx("C"), max_col=col2idx("O"),
                         min_row=hdr_row)
    chart.set_categories(cats_ref)

    s = chart.series[0]
    s.tx = SeriesLabel(strRef=ChartStrRef(f='KPIs!$B$8'))
    s.graphicalProperties.solidFill = _C_PETROLEO
    s.invertIfNegative = False

    dlbls = DataLabelList()
    dlbls.showVal         = True
    dlbls.showCatName     = False
    dlbls.showSerName     = False
    dlbls.showPercent     = False
    dlbls.showLegendKey   = False
    dlbls.showLeaderLines = False
    dlbls.numFmt = ChartNumFmt(formatCode='#,##0.0,"K"', sourceLinked=False)
    s.dLbls = dlbls

    chart.legend           = Legend()
    chart.legend.legendPos = 't'
    chart.legend.overlay   = False

    anchor        = TwoCellAnchor()
    anchor._from  = SpreadshAnchor(col=col2idx("C") - 1, row=10, colOff=0, rowOff=0)
    anchor.to     = SpreadshAnchor(col=col2idx("O"),     row=15, colOff=0, rowOff=0)
    ws.add_chart(chart)
    ws._charts[-1].anchor = anchor


# ─────────────────────────────────────────────────────────────────────────────
# Pós-save: injeção dos XMLs finais
# ─────────────────────────────────────────────────────────────────────────────

def patch_charts(path: Path) -> None:
    """Substitui XMLs de gráficos no arquivo salvo pela formatação completa.
    Chamar uma vez, imediatamente após writer.save().
    """
    _patch_zip(path, {
        'xl/charts/chart1.xml': _KPI_CHART_XML,
        # chart2, chart3... adicionar aqui quando implementados
    })


def _patch_zip(path: Path, replacements: dict[str, bytes]) -> None:
    tmp = Path(str(path) + '.tmp')
    try:
        with zipfile.ZipFile(path, 'r') as zin:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    data = replacements.get(item.filename) or zin.read(item.filename)
                    zout.writestr(item, data)
        os.replace(tmp, path)
    except Exception as e:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise OSError(f"Falha ao injetar XMLs de gráficos em '{path.name}': {e}") from e
