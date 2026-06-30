import openpyxl
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo
from pathlib import Path


def create_workbook() -> openpyxl.Workbook:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    return wb


def write_df_table(wb: openpyxl.Workbook, sheet_name: str,
                   df: pd.DataFrame, table_name: str) -> None:
    ws = wb.create_sheet(sheet_name)
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)
    n_cols = len(df.columns)
    n_rows = max(len(df) + 1, 2)  # OpenXML exige header + ≥1 linha de dados
    ref = f"A1:{get_column_letter(n_cols)}{n_rows}"
    tbl = Table(displayName=table_name, ref=ref)
    tbl.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    ws.add_table(tbl)


def save(wb: openpyxl.Workbook, path: Path) -> None:
    try:
        wb.save(path)
    except PermissionError as e:
        raise PermissionError(
            f"Não foi possível salvar '{path.name}' — feche o arquivo no Excel e tente novamente"
        ) from e
    except Exception as e:
        raise OSError(f"Falha ao salvar '{path.name}': {e}") from e
