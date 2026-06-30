import logging
import pandas as pd
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

MAPA_COLS = [
    "categoria", "sinal",
    "dre_n1", "dre_n2", "dre_n3", "dre_ordem",
    "dfc_n1", "dfc_n2", "dfc_n3", "dfc_ordem",
    "kpi_ebitda", "kpi_mc", "kpi_cv", "kpi_cf", "kpi_fcf_firma",
    "kpi_fcf_equity", "kpi_provisao", "kpi_receita_liquida", "kpi_lucro_liquido",
]

F_SALDO_COLS = ["data", "BU", "nome_conta", "saldo"]


def load_mapaaloc(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_excel(path, sheet_name="Mapa", skiprows=1)
        df = df[df["ativo"] == "Sim"].copy()
        df["categoria"] = df["categoria"].str.strip()
        return df[MAPA_COLS].reset_index(drop=True)
    except Exception as e:
        raise RuntimeError(f"Falha ao ler MapaAloc '{path.name}': {e}") from e


def load_f_bancos(bancos_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Lê saldos bancários de f_bancos/ por convenção de pasta (SRS §4.2).
    Retorna (DataFrame com F_SALDO_COLS, lista de erros para f_Erros).
    DataFrame vazio indica ausência/falha — f_SaldoBancos fica vazio; CAIXA INÍCIO = 0.
    """
    codigo = cfg["codigo"]
    nome   = cfg["nome"]

    if not bancos_dir.exists():
        return pd.DataFrame(columns=F_SALDO_COLS), [_erro_bancos(
            f"pasta f_bancos/ não encontrada para {codigo} — CAIXA INÍCIO = 0. "
            f"Criar assets/dados/{codigo} - {nome}/f_bancos/ com saldos históricos."
        )]

    expected = f"{codigo}_f_Bancos.xlsx"
    xlsx_files = list(bancos_dir.glob(expected))
    if not xlsx_files:
        outros = [p.name for p in bancos_dir.glob("*.xlsx")]
        sufixo = f" Arquivo(s) com nome incorreto encontrado(s): {outros}." if outros else ""
        return pd.DataFrame(columns=F_SALDO_COLS), [_erro_bancos(
            f"f_bancos/ encontrada mas {expected} não encontrado para {codigo} — CAIXA INÍCIO = 0.{sufixo}"
        )]

    path = xlsx_files[0]

    try:
        df = pd.read_excel(path)
    except Exception as e:
        return pd.DataFrame(columns=F_SALDO_COLS), [_erro_bancos(
            f"Erro ao ler {path.name}: {e}"
        )]

    if df.empty:
        return pd.DataFrame(columns=F_SALDO_COLS), [_erro_bancos(
            f"{path.name} está vazio — CAIXA INÍCIO = 0. Preencher com saldos históricos."
        )]

    missing = [c for c in F_SALDO_COLS if c not in df.columns]
    if missing:
        return pd.DataFrame(columns=F_SALDO_COLS), [_erro_bancos(
            f"Colunas ausentes em {path.name}: {missing}. "
            f"Colunas esperadas: {F_SALDO_COLS}."
        )]

    df = df[F_SALDO_COLS].copy()
    df["data"]  = pd.to_datetime(df["data"],  errors="coerce")
    df["saldo"] = pd.to_numeric(df["saldo"],  errors="coerce").fillna(0.0)
    df = df.dropna(subset=["data"]).reset_index(drop=True)

    # Normalizar data para 1º do mês e detectar duplicatas
    df["_mes_key"] = df["data"].dt.to_period("M")
    erros: list[dict[str, Any]] = []
    dup = df.groupby(["BU", "nome_conta", "_mes_key"]).size()
    dup = dup[dup > 1]
    for (bu, conta, mes), count in dup.items():
        erros.append(_erro_bancos(
            f"Saldo duplicado em f_bancos/: conta '{conta}' / BU '{bu}' "
            f"no mês {mes} ({count} entradas) — usando a de maior data."
        ))
    df = df.sort_values("data").groupby(
        ["BU", "nome_conta", "_mes_key"], as_index=False
    ).last()
    df["data"] = df["_mes_key"].dt.to_timestamp()
    df = df.drop(columns=["_mes_key"]).reset_index(drop=True)

    log.info(f"  {len(df)} linhas lidas de {path.name}")
    return df, erros


def _erro_bancos(motivo: str) -> dict[str, Any]:
    return {
        "id_lcto":       None,
        "data_caixa":    pd.NaT,
        "categoria":     "[f_SaldoBancos]",
        "bu":            None,
        "tipo_registro": None,
        "valor":         None,
        "motivo":        motivo,
    }
