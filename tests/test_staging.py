"""
Testes unitários das funções de staging (pipeline/staging.py).
Não requerem arquivos de dados reais — usam DataFrames sintéticos.
"""
import pandas as pd
import pytest

import staging
from conftest import make_mapa, make_lctos, CFG_AB_TEST

_KPI_NOES_2 = {k: ["Não", "Não"] for k in [
    "kpi_ebitda", "kpi_mc", "kpi_cv", "kpi_cf",
    "kpi_fcf_firma", "kpi_fcf_equity", "kpi_provisao",
    "kpi_receita_liquida", "kpi_lucro_liquido",
]}


# ─────────────────────────────────────────────────────────────────────────────
# check_mapa_categorias
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckMapaCategorias:

    def test_sem_duplicatas_retorna_lista_vazia(self):
        mapa = make_mapa(["Cat A", "Cat B", "Cat C"])
        assert staging.check_mapa_categorias(mapa) == []

    def test_categoria_duplicada_detectada(self):
        mapa = make_mapa(["Cat A", "Cat A", "Cat B"])
        erros = staging.check_mapa_categorias(mapa)
        assert len(erros) == 1
        assert "Cat A" in erros[0]["motivo"]

    def test_multiplas_duplicatas(self):
        mapa = make_mapa(["Cat A", "Cat A", "Cat B", "Cat B"])
        erros = staging.check_mapa_categorias(mapa)
        assert len(erros) == 2

    def test_mapa_vazio_retorna_lista_vazia(self):
        mapa = make_mapa([])
        assert staging.check_mapa_categorias(mapa) == []


# ─────────────────────────────────────────────────────────────────────────────
# split_errors
# ─────────────────────────────────────────────────────────────────────────────

class TestSplitErrors:

    def test_linha_valida_passa(self):
        df = make_lctos(["Cat A"], bus=["Ab Aeterno"], tipos=["Realizado"])
        validos, erros = staging.split_errors(df, CFG_AB_TEST)
        assert len(validos) == 1
        assert erros == []

    def test_bu_invalido_vai_para_erros(self):
        df = make_lctos(["Cat A"], bus=["BU Inexistente"])
        validos, erros = staging.split_errors(df, CFG_AB_TEST)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "BU fora do domínio" in erros[0]["motivo"]

    def test_tipo_registro_invalido_vai_para_erros(self):
        df = make_lctos(["Cat A"], tipos=["TipoInexistente"])
        validos, erros = staging.split_errors(df, CFG_AB_TEST)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "tipo_registro desconhecido" in erros[0]["motivo"]

    def test_data_caixa_nula_vai_para_erros(self):
        df = make_lctos(["Cat A"], datas=[None])
        validos, erros = staging.split_errors(df, CFG_AB_TEST)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "data_caixa" in erros[0]["motivo"]

    def test_valor_nulo_vai_para_erros(self):
        df = make_lctos(["Cat A"], valores=[None])
        validos, erros = staging.split_errors(df, CFG_AB_TEST)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "valor" in erros[0]["motivo"]

    def test_mix_validos_e_invalidos(self):
        df = make_lctos(
            categorias=["Cat A", "Cat B", "Cat C"],
            bus=["Ab Aeterno", "BU Ruim", "Holding"],
            tipos=["Realizado", "Realizado", "Orçado"],
        )
        validos, erros = staging.split_errors(df, CFG_AB_TEST)
        assert len(validos) == 2
        assert len(erros) == 1

    def test_todos_bu_validos_aceitos(self):
        for bu in CFG_AB_TEST["bu_validos"]:
            df = make_lctos(["Cat A"], bus=[bu])
            validos, erros = staging.split_errors(df, CFG_AB_TEST)
            assert len(validos) == 1, f"BU válida '{bu}' foi rejeitada"

    def test_todos_tipo_reg_validos_aceitos(self):
        for tipo in CFG_AB_TEST["tipo_reg_validos"]:
            df = make_lctos(["Cat A"], tipos=[tipo])
            validos, erros = staging.split_errors(df, CFG_AB_TEST)
            assert len(validos) == 1, f"tipo_registro '{tipo}' foi rejeitado"


# ─────────────────────────────────────────────────────────────────────────────
# enrich
# ─────────────────────────────────────────────────────────────────────────────

class TestEnrich:

    def test_categoria_mapeada_sem_mapa_false(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"])
        result, erros = staging.enrich(df, mapa, CFG_AB_TEST)
        assert result["_sem_mapa"].iloc[0] == False
        assert erros == []

    def test_categoria_nao_mapeada_sem_mapa_true(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat INEXISTENTE"])
        result, erros = staging.enrich(df, mapa, CFG_AB_TEST)
        assert result["_sem_mapa"].iloc[0] == True
        assert len(erros) == 1
        assert "Sem mapeamento" in erros[0]["motivo"]

    def test_campos_derivados_calculados(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"], datas=[pd.Timestamp("2024-03-15")])
        result, _ = staging.enrich(df, mapa, CFG_AB_TEST)
        row = result.iloc[0]
        assert row["ano"] == 2024
        assert row["mes_num"] == 3
        assert row["trimestre"] == 1
        assert row["semestre"] == 1
        assert row["mes_caixa"] == pd.Timestamp("2024-03-01")

    def test_id_lcto_sequencial(self):
        mapa = make_mapa(["Cat A", "Cat B"])
        df = make_lctos(["Cat A", "Cat B"])
        result, _ = staging.enrich(df, mapa, CFG_AB_TEST)
        assert list(result["id_lcto"]) == [1, 2]

    def test_fonte_mapeada_corretamente(self):
        mapa = make_mapa(["Cat A"])
        for tipo, fonte_esperada in CFG_AB_TEST["mapa_fonte"].items():
            df = make_lctos(["Cat A"], tipos=[tipo])
            result, _ = staging.enrich(df, mapa, CFG_AB_TEST)
            assert result["fonte"].iloc[0] == fonte_esperada


# ─────────────────────────────────────────────────────────────────────────────
# build_f_base
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildFBase:

    def _make_enriched(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"])
        enriched, _ = staging.enrich(df, mapa, CFG_AB_TEST)
        return enriched, mapa

    def test_colunas_corretas(self):
        enriched, mapa = self._make_enriched()
        f_base_cols = staging.get_f_base_cols(CFG_AB_TEST, mapa)
        f_base = staging.build_f_base(enriched, f_base_cols)
        assert list(f_base.columns) == f_base_cols

    def test_coluna_condicional_presente(self):
        enriched, mapa = self._make_enriched()
        f_base_cols = staging.get_f_base_cols(CFG_AB_TEST, mapa)
        f_base = staging.build_f_base(enriched, f_base_cols)
        assert "conta_bancaria" in f_base.columns
        assert "fornecedor_cliente" in f_base.columns

    def test_coluna_ausente_preenchida_com_none(self):
        enriched, mapa = self._make_enriched()
        f_base_cols = staging.get_f_base_cols(CFG_AB_TEST, mapa)
        # kpi_ebitda não tem Sim no mapa sintético — não entra em f_base_cols
        # mas conta_bancaria entra via condicional e deve ser preenchida com None
        f_base = staging.build_f_base(enriched, f_base_cols)
        assert f_base["conta_bancaria"].isna().all()

    def test_numero_de_linhas_preservado(self):
        mapa = make_mapa(["Cat A", "Cat B"])
        df = make_lctos(["Cat A", "Cat B"])
        enriched, _ = staging.enrich(df, mapa, CFG_AB_TEST)
        f_base_cols = staging.get_f_base_cols(CFG_AB_TEST, mapa)
        f_base = staging.build_f_base(enriched, f_base_cols)
        assert len(f_base) == 2

    def test_nucleo_23_colunas_sem_condicionais(self):
        """Sem condicionais ligadas e sem KPIs ativos → exatamente 23 colunas."""
        cfg_min = {**CFG_AB_TEST,
                   "tem_conta_bancaria": False, "tem_fornecedor_cliente": False}
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"])
        enriched, _ = staging.enrich(df, mapa, cfg_min)
        f_base_cols = staging.get_f_base_cols(cfg_min, mapa)
        f_base = staging.build_f_base(enriched, f_base_cols)
        assert len(f_base.columns) == 23


# ─────────────────────────────────────────────────────────────────────────────
# check_mapa_n3_unico
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckMapaN3Unico:

    def test_mapa_valido_retorna_lista_vazia(self):
        mapa = make_mapa(["Cat A", "Cat B"])
        assert staging.check_mapa_n3_unico(mapa) == []

    def test_mesmo_n3_com_mesmo_n1_n2_e_valido(self):
        """Múltiplas categorias com mesmo N3 e mesmo N1/N2 é válido — SUMIFS agrega."""
        mapa = make_mapa(["Cat A", "Cat B"], dre_n3=["N3 X", "N3 X"])
        assert staging.check_mapa_n3_unico(mapa) == []

    def test_dre_n3_com_n1_distintos_detectado(self):
        mapa = pd.DataFrame({
            "categoria": ["Cat A", "Cat B"],
            "sinal": [1, 1],
            "dre_n1":   ["N1 Alpha", "N1 Beta"],
            "dre_n2":   ["N2 X",     "N2 X"],
            "dre_n3":   ["N3 Dup",   "N3 Dup"],
            "dre_ordem": [1, 2],
            "dfc_n1":   ["Op",   "Op"],
            "dfc_n2":   ["Ent",  "Ent"],
            "dfc_n3":   ["Cat A", "Cat B"],
            "dfc_ordem": [1, 2],
            **_KPI_NOES_2,
        })
        erros = staging.check_mapa_n3_unico(mapa)
        assert len(erros) == 1
        assert "dre_n3" in erros[0]["motivo"]
        assert "N3 Dup" in erros[0]["motivo"]

    def test_dfc_n3_com_n1_distintos_detectado(self):
        mapa = pd.DataFrame({
            "categoria": ["Cat A", "Cat B"],
            "sinal": [1, 1],
            "dre_n1":   ["N1 X",  "N1 X"],
            "dre_n2":   ["N2 X",  "N2 X"],
            "dre_n3":   ["Cat A", "Cat B"],
            "dre_ordem": [1, 2],
            "dfc_n1":   ["Op",  "Fin"],
            "dfc_n2":   ["Ent", "Ent"],
            "dfc_n3":   ["DFC Dup", "DFC Dup"],
            "dfc_ordem": [1, 2],
            **_KPI_NOES_2,
        })
        erros = staging.check_mapa_n3_unico(mapa)
        assert len(erros) == 1
        assert "dfc_n3" in erros[0]["motivo"]

    def test_multiplas_violacoes_dre_e_dfc(self):
        mapa = pd.DataFrame({
            "categoria": ["Cat A", "Cat B", "Cat C", "Cat D"],
            "sinal": [1, 1, 1, 1],
            "dre_n1":   ["N1 Alpha", "N1 Beta", "N1 X",   "N1 X"],
            "dre_n2":   ["N2 X",     "N2 X",    "N2 X",   "N2 X"],
            "dre_n3":   ["N3 Dup",   "N3 Dup",  "Cat C",  "Cat D"],
            "dre_ordem": [1, 2, 3, 4],
            "dfc_n1":   ["Op",   "Op",   "Op",      "Fin"],
            "dfc_n2":   ["Ent",  "Ent",  "Ent",     "Ent"],
            "dfc_n3":   ["Cat A", "Cat B", "DFC Dup", "DFC Dup"],
            "dfc_ordem": [1, 2, 3, 4],
            **{k: ["Não", "Não", "Não", "Não"] for k in [
                "kpi_ebitda", "kpi_mc", "kpi_cv", "kpi_cf",
                "kpi_fcf_firma", "kpi_fcf_equity", "kpi_provisao",
                "kpi_receita_liquida", "kpi_lucro_liquido",
            ]},
        })
        erros = staging.check_mapa_n3_unico(mapa)
        assert len(erros) == 2

    def test_mapa_vazio_retorna_lista_vazia(self):
        mapa = make_mapa([])
        assert staging.check_mapa_n3_unico(mapa) == []
