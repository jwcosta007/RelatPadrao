"""
Testes unitários das funções ETL de etl_ab.py.
Não requerem arquivos de dados reais — usam DataFrames sintéticos.
"""
import pandas as pd
import pytest

import etl_ab
from conftest import make_mapa, make_lctos


# ─────────────────────────────────────────────────────────────────────────────
# check_mapa_categorias
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckMapaCategorias:

    def test_sem_duplicatas_retorna_lista_vazia(self):
        mapa = make_mapa(["Cat A", "Cat B", "Cat C"])
        assert etl_ab.check_mapa_categorias(mapa) == []

    def test_categoria_duplicada_detectada(self):
        mapa = make_mapa(["Cat A", "Cat A", "Cat B"])
        erros = etl_ab.check_mapa_categorias(mapa)
        assert len(erros) == 1
        assert "Cat A" in erros[0]["motivo"]

    def test_multiplas_duplicatas(self):
        mapa = make_mapa(["Cat A", "Cat A", "Cat B", "Cat B"])
        erros = etl_ab.check_mapa_categorias(mapa)
        assert len(erros) == 2

    def test_mapa_vazio_retorna_lista_vazia(self):
        mapa = make_mapa([])
        assert etl_ab.check_mapa_categorias(mapa) == []


# ─────────────────────────────────────────────────────────────────────────────
# split_errors
# ─────────────────────────────────────────────────────────────────────────────

class TestSplitErrors:

    def test_linha_valida_passa(self):
        df = make_lctos(["Cat A"], bus=["Ab Aeterno"], tipos=["Realizado"])
        validos, erros = etl_ab.split_errors(df)
        assert len(validos) == 1
        assert erros == []

    def test_bu_invalido_vai_para_erros(self):
        df = make_lctos(["Cat A"], bus=["BU Inexistente"])
        validos, erros = etl_ab.split_errors(df)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "BU fora do domínio" in erros[0]["motivo"]

    def test_tipo_registro_invalido_vai_para_erros(self):
        df = make_lctos(["Cat A"], tipos=["TipoInexistente"])
        validos, erros = etl_ab.split_errors(df)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "tipo_registro desconhecido" in erros[0]["motivo"]

    def test_data_caixa_nula_vai_para_erros(self):
        df = make_lctos(["Cat A"], datas=[None])
        validos, erros = etl_ab.split_errors(df)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "data_caixa" in erros[0]["motivo"]

    def test_valor_nulo_vai_para_erros(self):
        df = make_lctos(["Cat A"], valores=[None])
        validos, erros = etl_ab.split_errors(df)
        assert len(validos) == 0
        assert len(erros) == 1
        assert "valor" in erros[0]["motivo"]

    def test_mix_validos_e_invalidos(self):
        df = make_lctos(
            categorias=["Cat A", "Cat B", "Cat C"],
            bus=["Ab Aeterno", "BU Ruim", "Holding"],
            tipos=["Realizado", "Realizado", "Orçado"],
        )
        validos, erros = etl_ab.split_errors(df)
        assert len(validos) == 2
        assert len(erros) == 1

    def test_todos_bu_validos_aceitos(self):
        for bu in etl_ab.BU_VALIDOS:
            df = make_lctos(["Cat A"], bus=[bu])
            validos, erros = etl_ab.split_errors(df)
            assert len(validos) == 1, f"BU válida '{bu}' foi rejeitada"

    def test_todos_tipo_reg_validos_aceitos(self):
        for tipo in etl_ab.TIPO_REG_VALIDOS:
            df = make_lctos(["Cat A"], tipos=[tipo])
            validos, erros = etl_ab.split_errors(df)
            assert len(validos) == 1, f"tipo_registro '{tipo}' foi rejeitado"


# ─────────────────────────────────────────────────────────────────────────────
# enrich
# ─────────────────────────────────────────────────────────────────────────────

class TestEnrich:

    def test_categoria_mapeada_sem_mapa_false(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"])
        enrich, erros = etl_ab.enrich(df, mapa)
        assert enrich["_sem_mapa"].iloc[0] is False or enrich["_sem_mapa"].iloc[0] == False
        assert erros == []

    def test_categoria_nao_mapeada_sem_mapa_true(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat INEXISTENTE"])
        enrich, erros = etl_ab.enrich(df, mapa)
        assert enrich["_sem_mapa"].iloc[0] == True
        assert len(erros) == 1
        assert "Sem mapeamento" in erros[0]["motivo"]

    def test_campos_derivados_calculados(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"], datas=[pd.Timestamp("2024-03-15")])
        result, _ = etl_ab.enrich(df, mapa)
        row = result.iloc[0]
        assert row["ano"] == 2024
        assert row["mes_num"] == 3
        assert row["trimestre"] == 1
        assert row["semestre"] == 1
        assert row["mes_caixa"] == pd.Timestamp("2024-03-01")

    def test_id_lcto_sequencial(self):
        mapa = make_mapa(["Cat A", "Cat B"])
        df = make_lctos(["Cat A", "Cat B"])
        result, _ = etl_ab.enrich(df, mapa)
        assert list(result["id_lcto"]) == [1, 2]

    def test_fonte_mapeada_corretamente(self):
        mapa = make_mapa(["Cat A"])
        for tipo, fonte_esperada in etl_ab.MAPA_FONTE.items():
            df = make_lctos(["Cat A"], tipos=[tipo])
            result, _ = etl_ab.enrich(df, mapa)
            assert result["fonte"].iloc[0] == fonte_esperada


# ─────────────────────────────────────────────────────────────────────────────
# build_f_base
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildFBase:

    def _make_enriched(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"])
        enriched, _ = etl_ab.enrich(df, mapa)
        return enriched

    def test_colunas_na_ordem_correta(self):
        enriched = self._make_enriched()
        f_base = etl_ab.build_f_base(enriched)
        assert list(f_base.columns) == etl_ab.F_BASE_COLS

    def test_numero_de_colunas(self):
        enriched = self._make_enriched()
        f_base = etl_ab.build_f_base(enriched)
        assert len(f_base.columns) == len(etl_ab.F_BASE_COLS)

    def test_coluna_ausente_preenchida_com_none(self):
        mapa = make_mapa(["Cat A"])
        df = make_lctos(["Cat A"])
        enriched, _ = etl_ab.enrich(df, mapa)
        # kpi_ebitda não existe no enriched (não vem do mapa sintético com Sim)
        f_base = etl_ab.build_f_base(enriched)
        assert "kpi_ebitda" in f_base.columns

    def test_numero_de_linhas_preservado(self):
        mapa = make_mapa(["Cat A", "Cat B"])
        df = make_lctos(["Cat A", "Cat B"])
        enriched, _ = etl_ab.enrich(df, mapa)
        f_base = etl_ab.build_f_base(enriched)
        assert len(f_base) == 2
