from pathlib import Path
from typing import Any
import pandas as pd

_OUT_COLS = [
    "data_caixa", "historico", "categoria", "valor", "bu",
    "conta_bancaria", "fornecedor_cliente", "tipo_registro",
]


def load(folder: Path, cfg: dict) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Lê todos os arquivos em f_Lctos/ e normaliza para shape intermediário.

    Espera colunas já no nome final (data_caixa, historico, categoria, valor,
    bu, conta_bancaria, fornecedor_cliente, tipo_registro) na primeira aba do
    arquivo — formato de export "consolidado" adotado pela AB Aeterno.
    """
    erros_leitura: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []

    for f in sorted(folder.iterdir()):
        if f.is_dir():
            continue
        try:
            df = pd.read_excel(f, sheet_name=0)
            missing = [c for c in _OUT_COLS if c not in df.columns]
            if missing:
                raise ValueError(f"colunas ausentes: {missing}")
            df["valor"]     = pd.to_numeric(df["valor"], errors="coerce")
            df["categoria"] = df["categoria"].str.strip()
            df["bu"]        = df["bu"].str.strip()
            frames.append(df[_OUT_COLS])
        except Exception as e:
            erros_leitura.append({
                "id_lcto": None, "data_caixa": None, "categoria": None,
                "bu": None, "tipo_registro": None, "valor": None,
                "motivo": f"Arquivo '{f.name}' em f_Lctos não pôde ser lido: {e}",
            })

    if not frames:
        return pd.DataFrame(columns=_OUT_COLS), erros_leitura

    return pd.concat(frames, ignore_index=True), erros_leitura
