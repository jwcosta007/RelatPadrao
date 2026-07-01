"""
Testes unitários do extractor GCG (pipeline/extractors/extractor_gcg.py).
Usa arquivos xlsx sintéticos gravados em tmp_path — não requer dados reais
do cliente (assets/dados/GCG - GCG Clinica/ é gitignored).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline" / "extractors"))

import pandas as pd
import pytest

import extractor_gcg as gcg

_COMUNS = {
    "Situação":                              "Quitado",
    "Data de vencimento":                    pd.Timestamp("2026-03-10"),
    "Data do último pagamento":              pd.Timestamp("2026-03-12"),
    "Data de competência":                   pd.Timestamp("2026-03-01"),
    "Descrição":                             "Compra de insumos",
    "Observações":                           None,
    "Categoria 1":                           "Cat A",
    "Conta bancária":                        "Itaú - AG 3820 CC 43029-0",
    "Valor original da parcela (R$)":        1000.0,
    "Valor total da parcela em aberto (R$)": 1000.0,
}


def _linha_pagar(**overrides):
    row = {**_COMUNS, "Nome do fornecedor": "Fornecedor X",
           "Valor total pago da parcela (R$)": 990.0}
    row.update(overrides)
    return row


def _linha_receber(**overrides):
    row = {**_COMUNS, "Nome do cliente": "Cliente Y",
           "Valor total recebido da parcela (R$)": 990.0}
    row.update(overrides)
    return row


def _grava(folder: Path, nome: str, linhas: list[dict]) -> None:
    pd.DataFrame(linhas).to_excel(folder / nome, index=False)


def _grava_pagar_receber(folder: Path, pagar_linhas=None, receber_linhas=None,
                          pagar_nome="visao_contas_a_pagar (9).xlsx",
                          receber_nome="visao_contas_a_receber (16).xlsx"):
    """Grava os dois arquivos Conta Azul. `[]` grava um placeholder Perdido/Desconsiderado
    (colunas presentes, sem gerar linha nem erro) para isolar o cenário testado no outro
    arquivo. `None` mantém uma linha padrão válida em ambos."""
    pagar = pagar_linhas if pagar_linhas is not None else [_linha_pagar()]
    receber = receber_linhas if receber_linhas is not None else [_linha_receber()]
    if not pagar:
        pagar = [_linha_pagar(**{"Situação": "Perdido/Desconsiderado"})]
    if not receber:
        receber = [_linha_receber(**{"Situação": "Perdido/Desconsiderado"})]
    _grava(folder, pagar_nome, pagar)
    _grava(folder, receber_nome, receber)


CFG = {}  # extractor_gcg.load não usa cfg — mantido pelo contrato de assinatura


class TestSituacoes:

    def test_quitado_gera_realizado_com_data_ultimo_pagamento_e_valor_pago(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Situação": "Quitado",
            "Valor total pago da parcela (R$)": 995.5,
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        row = df.iloc[0]
        assert row["tipo_registro"] == "Realizado"
        assert row["data_caixa"] == pd.Timestamp("2026-03-12")
        assert row["valor"] == 995.5
        assert erros == []

    def test_em_aberto_gera_projetado_com_data_vencimento_e_valor_aberto(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Situação": "Em aberto",
            "Valor total da parcela em aberto (R$)": 700.0,
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        row = df.iloc[0]
        assert row["tipo_registro"] == "Projetado"
        assert row["data_caixa"] == pd.Timestamp("2026-03-10")
        assert row["valor"] == 700.0
        assert erros == []

    def test_atrasado_gera_atrasado_com_data_vencimento_e_valor_aberto(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Situação": "Atrasado",
            "Valor total da parcela em aberto (R$)": 300.0,
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        row = df.iloc[0]
        assert row["tipo_registro"] == "Atrasado"
        assert row["data_caixa"] == pd.Timestamp("2026-03-10")
        assert row["valor"] == 300.0
        assert erros == []

    def test_perdido_desconsiderado_excluido_sem_erro(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Situação": "Perdido/Desconsiderado",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert len(df) == 0
        assert erros == []

    def test_situacao_desconhecida_vira_erro_tecnico(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Situação": "Situação Nova Inexistente",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert len(df) == 0
        assert len(erros) == 1
        assert "Situação desconhecida" in erros[0]["motivo"]


class TestBuDePara:

    def test_conta_cpf_mapeada(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Conta bancária": "BTG - Camilla",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert df.iloc[0]["bu"] == "CPF"
        assert erros == []

    def test_conta_cnpj_mapeada(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Conta bancária": "Stone",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert df.iloc[0]["bu"] == "CNPJ"
        assert erros == []

    def test_conta_com_c_barra_c_nao_e_tratada_como_split(self, tmp_path):
        """'Inter - Ag 0001 C/C 10845153-4' tem '/' mas é match exato — não é split."""
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Conta bancária": "Inter - Ag 0001 C/C 10845153-4",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert len(df) == 1
        assert df.iloc[0]["bu"] == "CNPJ"
        assert erros == []

    def test_conta_split_gera_erro_tecnico(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Conta bancária": "BB - AG 0525 CC 35440-6 / Inter - Ag 0001 C/C 10845153-4",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert len(df) == 0
        assert len(erros) == 1
        assert "split" in erros[0]["motivo"]

    def test_conta_sem_mapeamento_conhecido_gera_erro_tecnico(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Conta bancária": "Conta Nova Desconhecida",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert len(df) == 0
        assert len(erros) == 1
        assert "sem mapeamento de BU conhecido" in erros[0]["motivo"]


class TestLinhaIncompleta:

    def test_valor_e_conta_ambos_vazios_gera_erro_tecnico(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Situação": "Atrasado",
            "Valor total da parcela em aberto (R$)": None,
            "Conta bancária": None,
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert len(df) == 0
        assert len(erros) == 1
        assert "incompleto" in erros[0]["motivo"]

    def test_valor_ausente_mas_conta_presente_nao_e_incompleto(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Situação": "Atrasado",
            "Valor total da parcela em aberto (R$)": None,
            "Conta bancária": "Stone",
        })], receber_linhas=[])
        df, erros = gcg.load(tmp_path, CFG)
        assert erros == []
        assert len(df) == 1
        assert pd.isna(df.iloc[0]["valor"])


class TestHistoricoEFornecedorCliente:

    def test_historico_concatena_observacoes_quando_presentes(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Descrição": "Compra de insumos",
            "Observações": "Pago com desconto",
        })], receber_linhas=[])
        df, _ = gcg.load(tmp_path, CFG)
        assert df.iloc[0]["historico"] == "Compra de insumos — Pago com desconto"

    def test_historico_e_so_descricao_quando_observacoes_vazias(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Descrição": "Compra de insumos", "Observações": None,
        })], receber_linhas=[])
        df, _ = gcg.load(tmp_path, CFG)
        assert df.iloc[0]["historico"] == "Compra de insumos"

    def test_fornecedor_cliente_no_arquivo_pagar(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Nome do fornecedor": "Fornecedor ABC",
        })], receber_linhas=[])
        df, _ = gcg.load(tmp_path, CFG)
        assert df.iloc[0]["fornecedor_cliente"] == "Fornecedor ABC"

    def test_fornecedor_cliente_no_arquivo_receber(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[], receber_linhas=[_linha_receber(**{
            "Nome do cliente": "Cliente ABC",
        })])
        df, _ = gcg.load(tmp_path, CFG)
        assert df.iloc[0]["fornecedor_cliente"] == "Cliente ABC"


class TestColunasCondicionais:

    def test_data_competencia_vencimento_e_valor_original_presentes(self, tmp_path):
        _grava_pagar_receber(tmp_path, pagar_linhas=[_linha_pagar(**{
            "Data de competência":            pd.Timestamp("2026-02-01"),
            "Data de vencimento":              pd.Timestamp("2026-03-10"),
            "Valor original da parcela (R$)":  1234.56,
        })], receber_linhas=[])
        df, _ = gcg.load(tmp_path, CFG)
        row = df.iloc[0]
        assert row["data_competencia"] == pd.Timestamp("2026-02-01")
        assert row["data_vencimento"] == pd.Timestamp("2026-03-10")
        assert row["valor_original"] == 1234.56


class TestArquivosAusentes:

    def test_arquivo_pagar_ausente_gera_erro_leitura(self, tmp_path):
        _grava(tmp_path, "visao_contas_a_receber (16).xlsx", [_linha_receber()])
        df, erros = gcg.load(tmp_path, CFG)
        motivos = [e["motivo"] for e in erros]
        assert any("contas_a_pagar" in m for m in motivos)

    def test_ambos_arquivos_presentes_combinam_linhas(self, tmp_path):
        _grava_pagar_receber(tmp_path)
        df, erros = gcg.load(tmp_path, CFG)
        assert len(df) == 2
        assert erros == []
