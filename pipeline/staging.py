import pandas as pd
from typing import Any

F_ERROS_COLS = ["id_lcto", "data_caixa", "categoria", "bu", "tipo_registro", "valor", "motivo"]

_KPI_COLS_ALL = [
    "kpi_ebitda", "kpi_mc", "kpi_cv", "kpi_cf", "kpi_fcf_firma",
    "kpi_fcf_equity", "kpi_provisao", "kpi_receita_liquida", "kpi_lucro_liquido",
]

_NUCLEO_COLS = [
    "tipo_registro", "data_caixa", "historico", "categoria", "valor", "bu",
    "fonte", "sinal", "id_lcto",
    "mes_caixa", "ano", "trimestre", "semestre", "mes_num",
    "dre_n1", "dre_n2", "dre_n3", "dre_ordem",
    "dfc_n1", "dfc_n2", "dfc_n3", "dfc_ordem",
    "_sem_mapa",
]

_COND_FLAGS = [
    ("tem_conta_bancaria",     "conta_bancaria"),
    ("tem_fornecedor_cliente", "fornecedor_cliente"),
    ("tem_data_competencia",   "data_competencia"),
    ("tem_data_vencimento",    "data_vencimento"),
    ("tem_valor_original",     "valor_original"),
    ("tem_documento",          "documento"),
]


def get_f_base_cols(cfg: dict, mapa: pd.DataFrame) -> list[str]:
    """Deriva lista de colunas da f_Base: núcleo + condicionais ligadas + KPIs vivos."""
    cols = list(_NUCLEO_COLS)
    for flag, col in _COND_FLAGS:
        if cfg.get(flag):
            cols.append(col)
    kpi_ativos = [c for c in _KPI_COLS_ALL if c in mapa.columns and (mapa[c] == "Sim").any()]
    return cols + kpi_ativos


def _err(r: pd.Series, motivo: str) -> dict[str, Any]:
    return {k: r.get(k) for k in ["id_lcto", "data_caixa", "categoria", "bu", "tipo_registro", "valor"]} | {"motivo": motivo}


def check_mapa_categorias(mapa: pd.DataFrame) -> list[dict[str, Any]]:
    dup = mapa.groupby("categoria").size()
    dup = dup[dup > 1]
    return [
        {
            "id_lcto": None, "data_caixa": None, "categoria": cat,
            "bu": None, "tipo_registro": None, "valor": None,
            "motivo": (f"Categoria duplicada no MapaAloc: {cat!r} — "
                       f"{n} ocorrências. Corrigir MapaAloc e recarregar."),
        }
        for cat, n in dup.items()
    ]


def split_errors(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    bu_validos       = set(cfg["bu_validos"])
    tipo_reg_validos = set(cfg["tipo_reg_validos"])
    erros, valid = [], pd.Series(True, index=df.index)

    def _add(mask, motivo_fn):
        for _, r in df[mask & valid].iterrows():
            erros.append(_err(r, motivo_fn(r)))
        return ~mask

    valid &= _add(df["data_caixa"].isna(),
                  lambda r: "data_caixa ausente ou inválida")
    valid &= _add(~df["tipo_registro"].isin(tipo_reg_validos),
                  lambda r: f"tipo_registro desconhecido: {r['tipo_registro']!r}")
    valid &= _add(~df["bu"].isin(bu_validos),
                  lambda r: f"BU fora do domínio: {r['bu']!r}")
    valid &= _add(df["valor"].isna(),
                  lambda r: "Falha de conversão de valor — não numérico")
    return df[valid].copy(), erros


def enrich(df: pd.DataFrame, mapa: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    df = df.merge(mapa, on="categoria", how="left")
    df["_sem_mapa"] = df["dre_n1"].isna()
    df["fonte"]     = df["tipo_registro"].map(cfg["mapa_fonte"])
    df["mes_caixa"] = df["data_caixa"].dt.to_period("M").dt.to_timestamp()
    df["ano"]       = df["data_caixa"].dt.year
    df["mes_num"]   = df["data_caixa"].dt.month
    df["trimestre"] = df["data_caixa"].dt.quarter
    df["semestre"]  = ((df["data_caixa"].dt.month - 1) // 6 + 1)
    df = df.reset_index(drop=True)
    df["id_lcto"]   = df.index + 1

    erros = [
        _err(r, f"Sem mapeamento no MapaAloc — categoria: {r['categoria']!r}")
        for _, r in df[df["_sem_mapa"]].iterrows()
    ]
    return df, erros


def build_f_base(df: pd.DataFrame, f_base_cols: list[str]) -> pd.DataFrame:
    for col in f_base_cols:
        if col not in df.columns:
            df[col] = None
    return df[f_base_cols].copy()
