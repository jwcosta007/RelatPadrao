import logging
import pandas as pd
from pathlib import Path

log = logging.getLogger(__name__)

MAPA_COLS = [
    "categoria", "sinal",
    "dre_n1", "dre_n2", "dre_n3", "dre_ordem",
    "dfc_n1", "dfc_n2", "dfc_n3", "dfc_ordem",
    "kpi_ebitda", "kpi_mc", "kpi_cv", "kpi_cf", "kpi_fcf_firma",
    "kpi_fcf_equity", "kpi_provisao", "kpi_receita_liquida", "kpi_lucro_liquido",
]

F_SALDO_COLS = ["data", "BU", "nome_conta", "valor"]


def load_mapaaloc(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_excel(path, sheet_name="Mapa", skiprows=1)
        df = df[df["ativo"] == "Sim"].copy()
        df["categoria"] = df["categoria"].str.strip()
        return df[MAPA_COLS].reset_index(drop=True)
    except Exception as e:
        raise RuntimeError(f"Falha ao ler MapaAloc '{path.name}': {e}") from e


def load_existing_saldo(output_path: Path) -> pd.DataFrame:
    if output_path.exists():
        try:
            return pd.read_excel(output_path, sheet_name="f_SaldoBancos")
        except ValueError:
            log.warning(f"  Aviso: {output_path.name} existe mas não contém aba 'f_SaldoBancos' — seed será aplicado")
        except Exception:
            pass
    return pd.DataFrame(columns=F_SALDO_COLS)
