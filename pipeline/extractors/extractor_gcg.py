from pathlib import Path
from typing import Any
import pandas as pd

_ARQ_PAGAR   = "contas_a_pagar"
_ARQ_RECEBER = "contas_a_receber"

# De-para Conta bancária → BU (tabela fechada — cad_cliente_GCG.md §6).
# "Inter - Ag 0001 C/C 10845153-4" contém '/' na própria sigla "C/C" — não é
# notação split; por isso a checagem de match exato precede a checagem de '/'.
_BU_POR_CONTA = {
    "Itaú - AG 3820 CC 43029-0":              "CPF",
    "Itaú - CDB":                              "CPF",
    "BTG - Camilla":                           "CPF",
    "BB - ELO":                                "CPF",
    "Recepção (Caixinha)":                     "CPF",
    "BB - AG 0525 CC 35440-6":                 "CNPJ",
    "BB - Aplicação Fundo BB RF LP SELIC":     "CNPJ",
    "Caixa Econômica":                         "CNPJ",
    "Infinite Pay":                            "CNPJ",
    "Inter - Ag 0001 C/C 10845153-4":          "CNPJ",
    "Saúde Service":                           "CNPJ",
    "Stone":                                   "CNPJ",
    "Recebimentos | Camilla Garritano":        "CNPJ",
    "Ajustes de efeito zero (justificar)":     "CNPJ",
}

_COL_VALOR_ABERTO = "Valor total da parcela em aberto (R$)"

_COLS_COMUNS = [
    "Situação", "Data de vencimento", "Data do último pagamento",
    "Data de competência", "Descrição", "Observações", "Categoria 1",
    "Conta bancária", "Valor original da parcela (R$)", _COL_VALOR_ABERTO,
]

_COLS_POR_TIPO = {
    "pagar":   _COLS_COMUNS + ["Nome do fornecedor", "Valor total pago da parcela (R$)"],
    "receber": _COLS_COMUNS + ["Nome do cliente", "Valor total recebido da parcela (R$)"],
}

_OUT_COLS = [
    "data_caixa", "historico", "categoria", "valor", "bu", "tipo_registro",
    "conta_bancaria", "fornecedor_cliente",
    "data_competencia", "data_vencimento", "valor_original",
]


def _find_arquivo(folder: Path, substring: str) -> Path | None:
    candidatos = sorted(
        f for f in folder.iterdir()
        if f.is_file() and substring in f.name.lower()
    )
    return candidatos[0] if candidatos else None


def _historico(descricao: Any, observacoes: Any) -> Any:
    if pd.isna(observacoes) or not str(observacoes).strip():
        return descricao
    return f"{descricao} — {observacoes}"


def _erro(motivo: str, categoria=None, bu=None, tipo_registro=None,
          data_caixa=None, valor=None) -> dict[str, Any]:
    return {
        "id_lcto": None, "data_caixa": data_caixa, "categoria": categoria,
        "bu": bu, "tipo_registro": tipo_registro, "valor": valor,
        "motivo": motivo,
    }


def _processa_arquivo(path: Path, tipo_doc: str) -> tuple[list[dict], list[dict[str, Any]]]:
    """tipo_doc: 'pagar' ou 'receber'."""
    df = pd.read_excel(path)

    esperadas = _COLS_POR_TIPO[tipo_doc]
    missing = [c for c in esperadas if c not in df.columns]
    if missing:
        raise ValueError(f"colunas ausentes: {missing}")

    if tipo_doc == "pagar":
        col_valor_quitado = "Valor total pago da parcela (R$)"
        col_fornecedor_cliente = "Nome do fornecedor"
    else:
        col_valor_quitado = "Valor total recebido da parcela (R$)"
        col_fornecedor_cliente = "Nome do cliente"

    linhas: list[dict] = []
    erros: list[dict[str, Any]] = []

    for _, r in df.iterrows():
        situacao = r["Situação"]
        categoria = r["Categoria 1"]

        if situacao == "Perdido/Desconsiderado":
            continue

        if situacao == "Quitado":
            tipo_registro = "Realizado"
            data_caixa = r["Data do último pagamento"]
            valor = r[col_valor_quitado]
        elif situacao == "Em aberto":
            tipo_registro = "Projetado"
            data_caixa = r["Data de vencimento"]
            valor = r[_COL_VALOR_ABERTO]
        elif situacao == "Atrasado":
            tipo_registro = "Atrasado"
            data_caixa = r["Data de vencimento"]
            valor = r[_COL_VALOR_ABERTO]
        else:
            erros.append(_erro(
                f"Situação desconhecida em {path.name}: {situacao!r}",
                categoria=categoria,
            ))
            continue

        conta_raw = r["Conta bancária"]
        conta = None if (pd.isna(conta_raw) or not str(conta_raw).strip()) else str(conta_raw).strip()

        if pd.isna(valor) and conta is None:
            erros.append(_erro(
                f"Lançamento incompleto em {path.name}: valor e conta bancária ausentes",
                categoria=categoria, tipo_registro=tipo_registro,
            ))
            continue

        if conta is None:
            bu = None
        elif conta in _BU_POR_CONTA:
            bu = _BU_POR_CONTA[conta]
        elif "/" in conta:
            erros.append(_erro(
                f"Conta bancária split não suportado em {path.name}: {conta!r}",
                categoria=categoria, tipo_registro=tipo_registro,
                data_caixa=data_caixa, valor=valor,
            ))
            continue
        else:
            erros.append(_erro(
                f"Conta bancária sem mapeamento de BU conhecido em {path.name}: {conta!r}",
                categoria=categoria, tipo_registro=tipo_registro,
                data_caixa=data_caixa, valor=valor,
            ))
            continue

        linhas.append({
            "data_caixa":         data_caixa,
            "historico":          _historico(r["Descrição"], r["Observações"]),
            "categoria":          categoria,
            "valor":              valor,
            "bu":                 bu,
            "tipo_registro":      tipo_registro,
            "conta_bancaria":     conta,
            "fornecedor_cliente": r[col_fornecedor_cliente],
            "data_competencia":   r["Data de competência"],
            "data_vencimento":    r["Data de vencimento"],
            "valor_original":     r["Valor original da parcela (R$)"],
        })

    return linhas, erros


def load(folder: Path, cfg: dict) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Lê os dois exports Conta Azul (contas_a_pagar / contas_a_receber) de f_Lctos/."""
    erros_leitura: list[dict[str, Any]] = []
    linhas: list[dict] = []

    for substring, tipo_doc in ((_ARQ_PAGAR, "pagar"), (_ARQ_RECEBER, "receber")):
        path = _find_arquivo(folder, substring)
        if path is None:
            erros_leitura.append(
                _erro(f"Arquivo contendo '{substring}' não encontrado em f_Lctos")
            )
            continue
        try:
            arq_linhas, arq_erros = _processa_arquivo(path, tipo_doc)
            linhas.extend(arq_linhas)
            erros_leitura.extend(arq_erros)
        except Exception as e:
            erros_leitura.append(
                _erro(f"Arquivo '{path.name}' em f_Lctos não pôde ser lido: {e}")
            )

    if not linhas:
        return pd.DataFrame(columns=_OUT_COLS), erros_leitura

    df = pd.DataFrame(linhas, columns=_OUT_COLS)
    df["valor"]            = pd.to_numeric(df["valor"], errors="coerce")
    df["valor_original"]   = pd.to_numeric(df["valor_original"], errors="coerce")
    df["data_caixa"]       = pd.to_datetime(df["data_caixa"], errors="coerce")
    df["data_competencia"] = pd.to_datetime(df["data_competencia"], errors="coerce")
    df["data_vencimento"]  = pd.to_datetime(df["data_vencimento"], errors="coerce")
    df["categoria"]        = df["categoria"].str.strip()
    return df, erros_leitura
