import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import pandas as pd
from pathlib import Path
from datetime import datetime

import loader
import builder
import writer

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(r"C:\Dev\projetos\RelatPadrao")
LCTOS_PATH = BASE_DIR / "assets" / "Piloto" / "ABAeterno" / "f_Lctos_2023_2026_proj.xlsx"
MAPA_PATH  = BASE_DIR / "assets" / "Piloto" / "ABAeterno" / "AB_MapaAloc_v11 - Atual utilizado na AB.xlsx"
LOGO_PATH  = BASE_DIR / "assets" / "logo" / "5.png"

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG AB AETERNO  (cad_cliente_ABv03)
# ─────────────────────────────────────────────────────────────────────────────
BU_VALIDOS       = {"Ab Aeterno", "Da Una Vita", "Holding"}
TIPO_REG_VALIDOS = {"Realizado", "Orçado", "Reforecast"}
MAPA_FONTE       = {"Realizado": "Dados Oficiais",
                    "Orçado": "Orçamento",
                    "Reforecast": "Reforecast"}

CAD_CONFIG = {
    "codigo":                    "AB",
    "nome":                      "AB Aeterno",
    "segmento_cliente":          "Servicos",
    "status":                    "Ativo",
    "origem_dados_realizado":    "Arquivo Empresa",
    "path_lctos":                str(LCTOS_PATH),
    "staging_mapa_fonte":        "Realizado→Dados Oficiais | Orçado→Orçamento",
    "conversao_defensiva_valor": "Sim",
    "bu_origem":                 "f_Lctos_direto",
    "bu_valores_validos":        "Ab Aeterno | Da Una Vita | Holding",
    "tem_conta_bancaria":        "Sim",
    "tem_fornecedor_cliente":    "Sim",
    "mes_corte_realizado":       "2026-05",
    "reforecast_vigente_ref":    "",
    "mapaaloc_arquivo":          "AB_MapaAloc_v11 - Atual utilizado na AB.xlsx",
    "mapaaloc_versao":           "v11",
    "moeda":                     "BRL",
}

_ts         = datetime.now().strftime("%Y%m%d%H%M")
OUTPUT_PATH = BASE_DIR / "relatorios" / f"{CAD_CONFIG['codigo']}_RelatFinanceiro_{_ts}.xlsx"

# ─────────────────────────────────────────────────────────────────────────────
# CASCADE DRE — define posição dos KPIs na cascata (§9 do v16)
# ─────────────────────────────────────────────────────────────────────────────
# (n1_names_em_ordem, kpi_label, is_roxo_logo)
DRE_CASCADE = [
    (["Receita Líquida"],
     "RECEITA LÍQUIDA", False),

    (["Custos", "Despesas Comerciais"],
     "MARGEM DE CONTRIBUIÇÃO", False),

    (["Despesas"],
     "EBITDA", False),

    (["Investimentos", "Resultado Financeiro",
      "Resultado Não Operacional", "Impostos sobre Resultado"],
     "LUCRO LÍQUIDO", False),

    (["Societário"],
     "RESULTADO INVESTIDORES", True),
]

# ─────────────────────────────────────────────────────────────────────────────
# CONTRATOS DE COLUNAS  (fonte: cad_cliente_ABv03.md §2.2)
# ─────────────────────────────────────────────────────────────────────────────
F_BASE_COLS = [
    "tipo_registro","data_caixa","historico","categoria","valor","bu",
    "fornecedor_cliente","fonte","sinal","id_lcto",
    "mes_caixa","ano","trimestre","semestre","mes_num",
    "dre_n1","dre_n2","dre_n3","dre_ordem",
    "dfc_n1","dfc_n2","dfc_n3","dfc_ordem",
    "_sem_mapa","conta_bancaria",
    "kpi_ebitda","kpi_mc","kpi_cv","kpi_cf","kpi_fcf_firma",
    "kpi_fcf_equity","kpi_provisao","kpi_receita_liquida","kpi_lucro_liquido",
]

F_ERROS_COLS = ["id_lcto","data_caixa","categoria","bu",
                "tipo_registro","valor","motivo"]

F_SALDO_SEED = pd.DataFrame([
    {"data": pd.Timestamp("2022-12-31"), "BU": "Holding", "nome_conta": "PJ", "valor": 0},
    {"data": pd.Timestamp("2022-12-31"), "BU": "Holding", "nome_conta": "PF", "valor": 0},
], columns=["data", "BU", "nome_conta", "valor"])


# ─────────────────────────────────────────────────────────────────────────────
# ETL — transformação de dados
# ─────────────────────────────────────────────────────────────────────────────
def split_errors(df):
    erros, valid = [], pd.Series(True, index=df.index)

    def _add(mask, motivo_fn):
        for _, r in df[mask & valid].iterrows():
            erros.append(_err(r, motivo_fn(r)))
        return ~mask

    valid &= _add(df["data_caixa"].isna(),
                  lambda r: "data_caixa ausente ou inválida")
    valid &= _add(~df["tipo_registro"].isin(TIPO_REG_VALIDOS),
                  lambda r: f"tipo_registro desconhecido: {r['tipo_registro']!r}")
    valid &= _add(~df["bu"].isin(BU_VALIDOS),
                  lambda r: f"BU fora do domínio: {r['bu']!r}")
    valid &= _add(df["valor"].isna(),
                  lambda r: "Falha de conversão de valor — não numérico")
    return df[valid].copy(), erros


def _err(r, motivo):
    return {k: r.get(k) for k in ["id_lcto","data_caixa","categoria",
                                    "bu","tipo_registro","valor"]} | {"motivo": motivo}


def check_mapa_categorias(mapa):
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


def enrich(df, mapa):
    df = df.merge(mapa, on="categoria", how="left")
    df["_sem_mapa"] = df["dre_n1"].isna()
    df["fonte"]     = df["tipo_registro"].map(MAPA_FONTE)
    df["mes_caixa"] = df["data_caixa"].dt.to_period("M").dt.to_timestamp()
    df["ano"]       = df["data_caixa"].dt.year
    df["mes_num"]   = df["data_caixa"].dt.month
    df["trimestre"] = df["data_caixa"].dt.quarter
    df["semestre"]  = ((df["data_caixa"].dt.month - 1) // 6 + 1)
    df = df.reset_index(drop=True)
    df["id_lcto"]   = df.index + 1

    erros = [_err(r, f"Sem mapeamento no MapaAloc — categoria: {r['categoria']!r}")
             for _, r in df[df["_sem_mapa"]].iterrows()]
    return df, erros


def build_f_base(df):
    for col in F_BASE_COLS:
        if col not in df.columns:
            df[col] = None
    return df[F_BASE_COLS].copy()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("Carregando MapaAloc...")
    mapa = loader.load_mapaaloc(MAPA_PATH)
    print(f"  {len(mapa)} categorias ativas")

    mes_corte_date = pd.Timestamp(f"{CAD_CONFIG['mes_corte_realizado']}-01")

    print("Verificando integridade do MapaAloc...")
    erros_dup = check_mapa_categorias(mapa)
    if erros_dup:
        print(f"  ERRO CRÍTICO: {len(erros_dup)} categoria(s) duplicada(s)")
        for e in erros_dup:
            print(f"    {e['motivo']}")
        f_erros_df   = pd.DataFrame(erros_dup, columns=F_ERROS_COLS)
        f_base_vazia = pd.DataFrame(columns=F_BASE_COLS)
        f_saldo = loader.load_existing_saldo(OUTPUT_PATH)
        if f_saldo.empty:
            f_saldo = F_SALDO_SEED.copy()
        enriched_vazio = pd.DataFrame(columns=["mes_caixa", "tipo_registro"])
        wb = writer.create_workbook()
        wb.create_sheet("DRE Gerencial")
        wb.create_sheet("DFC")
        writer.write_df_table(wb, "f_Base",        f_base_vazia, "f_Base")
        wb.create_sheet("Lista")
        writer.write_df_table(wb, "f_Erros",       f_erros_df,   "f_Erros")
        writer.write_df_table(wb, "f_SaldoBancos", f_saldo,      "f_SaldoBancos")
        wb.create_sheet("cad_cliente")
        wb.create_sheet("check")
        builder.build_lista(wb, enriched_vazio, BU_VALIDOS)
        builder.build_cad_cliente(wb, CAD_CONFIG)
        builder.build_dre(wb, mapa, DRE_CASCADE, mes_corte=mes_corte_date, logo_path=LOGO_PATH)
        builder.build_dfc(wb, mapa, mes_corte=mes_corte_date, logo_path=LOGO_PATH)
        print(f"Salvando {OUTPUT_PATH.name}...")
        writer.save(wb, OUTPUT_PATH)
        print(f"\nResumo:")
        print(f"  ERRO CRÍTICO: MapaAloc com {len(erros_dup)} categoria(s) duplicada(s)")
        print(f"  f_Base  : vazia")
        print(f"  f_Erros : {len(erros_dup)} ocorrência(s) crítica(s)")
        print(f"  Salvo em: {OUTPUT_PATH}")
        return

    print("Carregando f_Lctos...")
    lctos = loader.load_lctos(LCTOS_PATH)
    print(f"  {len(lctos)} linhas")

    print("Validando erros técnicos...")
    validos, erros_tec = split_errors(lctos)
    print(f"  Erros técnicos: {len(erros_tec)} | Válidas: {len(validos)}")

    print("Enriquecendo com MapaAloc...")
    enriched, erros_mapa = enrich(validos, mapa)
    print(f"  _sem_mapa: {enriched['_sem_mapa'].sum()}")

    all_erros = erros_tec + erros_mapa

    print("Verificando f_SaldoBancos...")
    f_saldo = loader.load_existing_saldo(OUTPUT_PATH)
    if f_saldo.empty:
        f_saldo = F_SALDO_SEED.copy()
        print(f"  Sem dados — seed aplicado ({len(f_saldo)} linhas)")
    else:
        print(f"  {len(f_saldo)} linhas preservadas")

    print("Montando f_Base...")
    f_base = build_f_base(enriched)
    print(f"  {len(f_base)} linhas × {len(f_base.columns)} colunas")

    f_erros_df = pd.DataFrame(all_erros if all_erros else [], columns=F_ERROS_COLS)

    print("Construindo workbook...")
    wb = writer.create_workbook()

    # Abas criadas na ordem final — sem sort posterior (§11.10)
    wb.create_sheet("DRE Gerencial")
    wb.create_sheet("DFC")
    wb.create_sheet("KPIs")
    writer.write_df_table(wb, "f_Base",        f_base,     "f_Base")
    wb.create_sheet("Lista")
    writer.write_df_table(wb, "f_Erros",       f_erros_df, "f_Erros")
    writer.write_df_table(wb, "f_SaldoBancos", f_saldo,    "f_SaldoBancos")
    wb.create_sheet("cad_cliente")
    wb.create_sheet("check")

    builder.build_lista(wb, enriched, BU_VALIDOS)
    builder.build_cad_cliente(wb, CAD_CONFIG)
    builder.build_dre(wb, mapa, DRE_CASCADE, mes_corte=mes_corte_date, logo_path=LOGO_PATH)
    builder.build_dfc(wb, mapa, mes_corte=mes_corte_date, logo_path=LOGO_PATH)
    builder.build_kpi(wb, mes_corte=mes_corte_date, logo_path=LOGO_PATH)

    print(f"Salvando {OUTPUT_PATH.name}...")
    writer.save(wb, OUTPUT_PATH)
    writer.patch_kpi_chart(OUTPUT_PATH)

    print(f"\nResumo:")
    print(f"  f_Base  : {len(f_base)} linhas, {len(f_base.columns)} colunas")
    print(f"  f_Erros : {len(all_erros)} ocorrências")
    print(f"    Erros técnicos : {len(erros_tec)}")
    print(f"    _sem_mapa      : {len(erros_mapa)}")
    print(f"  Salvo em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
