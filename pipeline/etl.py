import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import sys
import json
import importlib
import pandas as pd
from pathlib import Path
from datetime import datetime

import loader
import staging
import builder
import writer

BASE_DIR = Path(__file__).parent.parent


def _load_cfg(codigo: str) -> dict:
    cfg_path = BASE_DIR / "assets" / "cad_clientes" / f"cad_cliente_{codigo}.json"
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def _build_cad_config(cfg: dict, lctos_path: Path) -> dict:
    def _sim_nao(flag): return "Sim" if cfg.get(flag) else "Não"
    return {
        "codigo":                    cfg["codigo"],
        "nome":                      cfg["nome"],
        "segmento_cliente":          cfg["segmento_cliente"],
        "status":                    cfg["status"],
        "origem_dados_realizado":    cfg["origem_dados_realizado"],
        "path_lctos":                str(lctos_path),
        "staging_mapa_fonte":        cfg.get("staging_mapa_fonte", ""),
        "conversao_defensiva_valor": cfg.get("conversao_defensiva_valor", "Não"),
        "bu_origem":                 cfg.get("bu_origem", ""),
        "bu_valores_validos":        " | ".join(cfg["bu_validos"]),
        "tem_conta_bancaria":        _sim_nao("tem_conta_bancaria"),
        "tem_fornecedor_cliente":    _sim_nao("tem_fornecedor_cliente"),
        "mes_corte_realizado":       cfg["mes_corte_realizado"],
        "reforecast_vigente_ref":    cfg.get("reforecast_vigente_ref") or "",
        "mapaaloc_arquivo":          cfg.get("mapaaloc_arquivo", ""),
        "mapaaloc_versao":           cfg.get("mapaaloc_versao", ""),
        "moeda":                     cfg.get("moeda", "BRL"),
    }


def main():
    if len(sys.argv) < 2:
        print("Uso: python etl.py <CODIGO_CLIENTE>   ex: python etl.py AB")
        sys.exit(1)

    codigo = sys.argv[1].upper()
    cfg    = _load_cfg(codigo)

    mapa_path   = BASE_DIR / cfg["path_mapa"]
    lctos_path  = BASE_DIR / cfg["path_lctos"]
    logo_path   = BASE_DIR / "assets" / "logo" / "5.png"
    ts          = datetime.now().strftime("%Y%m%d%H%M")
    output_path = BASE_DIR / "relatorios" / f"{codigo}_RelatFinanceiro_{ts}.xlsx"

    dre_cascade    = [(i["n1_names"], i["kpi_label"], i["is_roxo"]) for i in cfg["dre_cascade"]]
    mes_corte_date = pd.Timestamp(f"{cfg['mes_corte_realizado']}-01")
    bu_validos     = set(cfg["bu_validos"])
    cad_config     = _build_cad_config(cfg, lctos_path)
    f_erros_cols   = staging.F_ERROS_COLS

    f_saldo_seed = pd.DataFrame(
        [{"data": pd.Timestamp(r["data"]), "BU": r["BU"],
          "nome_conta": r["nome_conta"], "valor": r["valor"]}
         for r in cfg.get("saldo_seed", [])],
        columns=["data", "BU", "nome_conta", "valor"],
    )

    extractor = importlib.import_module(f"extractors.extractor_{codigo.lower()}")

    # ── MapaAloc ──────────────────────────────────────────────────────────────
    print("Carregando MapaAloc...")
    mapa = loader.load_mapaaloc(mapa_path)
    print(f"  {len(mapa)} categorias ativas")

    f_base_cols = staging.get_f_base_cols(cfg, mapa)

    print("Verificando integridade do MapaAloc...")
    erros_dup = staging.check_mapa_categorias(mapa)
    if erros_dup:
        print(f"  ERRO CRÍTICO: {len(erros_dup)} categoria(s) duplicada(s)")
        for e in erros_dup:
            print(f"    {e['motivo']}")
        f_erros_df   = pd.DataFrame(erros_dup, columns=f_erros_cols)
        f_base_vazia = pd.DataFrame(columns=f_base_cols)
        f_saldo = loader.load_existing_saldo(output_path)
        if f_saldo.empty:
            f_saldo = f_saldo_seed.copy()
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
        builder.build_lista(wb, enriched_vazio, bu_validos)
        builder.build_cad_cliente(wb, cad_config)
        builder.build_dre(wb, mapa, dre_cascade, mes_corte=mes_corte_date, logo_path=logo_path)
        builder.build_dfc(wb, mapa, mes_corte=mes_corte_date, logo_path=logo_path)
        print(f"Salvando {output_path.name}...")
        writer.save(wb, output_path)
        print(f"\nResumo:")
        print(f"  ERRO CRÍTICO: MapaAloc com {len(erros_dup)} categoria(s) duplicada(s)")
        print(f"  f_Base  : vazia")
        print(f"  f_Erros : {len(erros_dup)} ocorrência(s) crítica(s)")
        print(f"  Salvo em: {output_path}")
        return

    # ── Lançamentos ───────────────────────────────────────────────────────────
    print("Carregando f_Lctos...")
    lctos = extractor.load(lctos_path, cfg)
    print(f"  {len(lctos)} linhas")

    print("Validando erros técnicos...")
    validos, erros_tec = staging.split_errors(lctos, cfg)
    print(f"  Erros técnicos: {len(erros_tec)} | Válidas: {len(validos)}")

    print("Enriquecendo com MapaAloc...")
    enriched, erros_mapa = staging.enrich(validos, mapa, cfg)
    print(f"  _sem_mapa: {enriched['_sem_mapa'].sum()}")

    all_erros = erros_tec + erros_mapa

    print("Verificando f_SaldoBancos...")
    f_saldo = loader.load_existing_saldo(output_path)
    if f_saldo.empty:
        f_saldo = f_saldo_seed.copy()
        print(f"  Sem dados — seed aplicado ({len(f_saldo)} linhas)")
    else:
        print(f"  {len(f_saldo)} linhas preservadas")

    print("Montando f_Base...")
    f_base = staging.build_f_base(enriched, f_base_cols)
    print(f"  {len(f_base)} linhas × {len(f_base.columns)} colunas")

    f_erros_df = pd.DataFrame(all_erros if all_erros else [], columns=f_erros_cols)

    # ── Workbook ──────────────────────────────────────────────────────────────
    print("Construindo workbook...")
    wb = writer.create_workbook()

    wb.create_sheet("DRE Gerencial")
    wb.create_sheet("DFC")
    wb.create_sheet("KPIs")
    writer.write_df_table(wb, "f_Base",        f_base,     "f_Base")
    wb.create_sheet("Lista")
    writer.write_df_table(wb, "f_Erros",       f_erros_df, "f_Erros")
    writer.write_df_table(wb, "f_SaldoBancos", f_saldo,    "f_SaldoBancos")
    wb.create_sheet("cad_cliente")
    wb.create_sheet("check")

    builder.build_lista(wb, enriched, bu_validos)
    builder.build_cad_cliente(wb, cad_config)
    builder.build_dre(wb, mapa, dre_cascade, mes_corte=mes_corte_date, logo_path=logo_path)
    builder.build_dfc(wb, mapa, mes_corte=mes_corte_date, logo_path=logo_path)
    builder.build_kpi(wb, mes_corte=mes_corte_date, logo_path=logo_path)

    print(f"Salvando {output_path.name}...")
    writer.save(wb, output_path)
    writer.patch_kpi_chart(output_path)

    print(f"\nResumo:")
    print(f"  f_Base  : {len(f_base)} linhas, {len(f_base.columns)} colunas")
    print(f"  f_Erros : {len(all_erros)} ocorrências")
    print(f"    Erros técnicos : {len(erros_tec)}")
    print(f"    _sem_mapa      : {len(erros_mapa)}")
    print(f"  Salvo em: {output_path}")


if __name__ == "__main__":
    main()
