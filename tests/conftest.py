import sys
from pathlib import Path

# Permite importar os módulos de pipeline/ sem instalação de pacote
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

import pandas as pd
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de dados sintéticos
# ─────────────────────────────────────────────────────────────────────────────

MAPA_COLS = [
    "categoria","sinal",
    "dre_n1","dre_n2","dre_n3","dre_ordem",
    "dfc_n1","dfc_n2","dfc_n3","dfc_ordem",
    "kpi_ebitda","kpi_mc","kpi_cv","kpi_cf","kpi_fcf_firma",
    "kpi_fcf_equity","kpi_provisao","kpi_receita_liquida","kpi_lucro_liquido",
]

def make_mapa(categorias, dre_n1="Receita Líquida", dre_n3=None):
    """MapaAloc mínimo para testes unitários."""
    n = len(categorias)
    return pd.DataFrame({
        "categoria":    categorias,
        "sinal":        [1] * n,
        "dre_n1":       [dre_n1] * n,
        "dre_n2":       ["Receita Bruta"] * n,
        "dre_n3":       dre_n3 if dre_n3 else categorias,
        "dre_ordem":    list(range(n)),
        "dfc_n1":       ["Atividades Operacionais"] * n,
        "dfc_n2":       ["DFC N2"] * n,
        "dfc_n3":       dre_n3 if dre_n3 else categorias,
        "dfc_ordem":    list(range(n)),
        "kpi_ebitda":         ["Não"] * n,
        "kpi_mc":             ["Não"] * n,
        "kpi_cv":             ["Não"] * n,
        "kpi_cf":             ["Não"] * n,
        "kpi_fcf_firma":      ["Não"] * n,
        "kpi_fcf_equity":     ["Não"] * n,
        "kpi_provisao":       ["Não"] * n,
        "kpi_receita_liquida":["Não"] * n,
        "kpi_lucro_liquido":  ["Não"] * n,
    })


def make_lctos(categorias=None, bus=None, tipos=None, datas=None, valores=None):
    """DataFrame de lançamentos mínimo para testes unitários."""
    n = len(categorias or ["Cat A"])
    return pd.DataFrame({
        "data_caixa":    datas    or [pd.Timestamp("2024-01-15")] * n,
        "historico":     ["hist"] * n,
        "categoria":     categorias or ["Cat A"] * n,
        "valor":         valores  or [1000.0] * n,
        "bu":            bus      or ["Ab Aeterno"] * n,
        "tipo_registro": tipos    or ["Realizado"] * n,
        "conta_bancaria":     [None] * n,
        "fornecedor_cliente": [None] * n,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures compartilhadas
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mapa_simples():
    return make_mapa(["Cat A", "Cat B", "Cat C"])


@pytest.fixture
def lctos_validos():
    return make_lctos(["Cat A", "Cat B"])


BASE_DIR = Path(__file__).parent.parent
LCTOS_PATH = BASE_DIR / "assets" / "Piloto" / "ABAeterno" / "f_Lctos_2023_2026_proj.xlsx"
MAPA_PATH  = BASE_DIR / "assets" / "Piloto" / "ABAeterno" / "AB_MapaAloc_v11 - Atual utilizado na AB.xlsx"

dados_disponiveis = pytest.mark.skipif(
    not LCTOS_PATH.exists() or not MAPA_PATH.exists(),
    reason="Dados do piloto AB não disponíveis (assets/Piloto/ é gitignored)"
)
