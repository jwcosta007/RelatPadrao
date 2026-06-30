import pandas as pd
from pathlib import Path


def load(path: Path, cfg: dict) -> pd.DataFrame:
    """Lê f_Lctos AB Aeterno (Excel) e normaliza para shape intermediário."""
    df = pd.read_excel(path, sheet_name="Sheet1")
    df["valor"]     = pd.to_numeric(df["valor"], errors="coerce")
    df["categoria"] = df["categoria"].str.strip()
    df["bu"]        = df["bu"].str.strip()
    return df
