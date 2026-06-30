import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import re
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

_REQUIRED_KEYS: dict[str, type] = {
    "codigo":                 str,
    "nome":                   str,
    "segmento_cliente":       str,
    "status":                 str,
    "origem_dados_realizado": str,
    "bu_validos":             list,
    "tipo_reg_validos":       list,
    "mapa_fonte":             dict,
    "mes_corte_realizado":    str,
    "dre_cascade":            list,
}


def _load_cfg(codigo: str) -> dict:
    cfg_path = BASE_DIR / "assets" / "cad_clientes" / f"cad_cliente_{codigo}.json"
    if not cfg_path.exists():
        print(f"ERRO: arquivo de configuração não encontrado: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def _validate_cfg(cfg: dict, codigo: str) -> None:
    errors = []

    for key, expected in _REQUIRED_KEYS.items():
        if key not in cfg:
            errors.append(f"chave obrigatória ausente: '{key}'")
        elif not isinstance(cfg[key], expected):
            errors.append(
                f"'{key}' deve ser {expected.__name__}, "
                f"recebeu {type(cfg[key]).__name__}"
            )

    if not errors:
        if not re.fullmatch(r"\d{4}-\d{2}", cfg.get("mes_corte_realizado", "")):
            errors.append(
                f"'mes_corte_realizado' deve ter formato AAAA-MM, "
                f"recebeu: {cfg.get('mes_corte_realizado')!r}"
            )
        if not cfg.get("bu_validos"):
            errors.append("'bu_validos' não pode ser lista vazia")
        for i, entry in enumerate(cfg.get("dre_cascade", [])):
            for k in ("n1_names", "kpi_label", "is_roxo"):
                if k not in entry:
                    errors.append(f"dre_cascade[{i}]: chave '{k}' ausente")

    if errors:
        print(f"ERRO: cad_cliente_{codigo}.json inválido:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)


def _build_cad_config(cfg: dict, lctos_dir: Path) -> dict:
    def _sim_nao(flag): return "Sim" if cfg.get(flag) else "Não"
    return {
        "codigo":                    cfg["codigo"],
        "nome":                      cfg["nome"],
        "segmento_cliente":          cfg["segmento_cliente"],
        "status":                    cfg["status"],
        "origem_dados_realizado":    cfg["origem_dados_realizado"],
        "path_lctos":                str(lctos_dir),
        "staging_mapa_fonte":        cfg.get("staging_mapa_fonte", ""),
        "conversao_defensiva_valor": cfg.get("conversao_defensiva_valor", "Não"),
        "bu_origem":                 cfg.get("bu_origem", ""),
        "bu_valores_validos":        " | ".join(cfg["bu_validos"]),
        "tem_conta_bancaria":        _sim_nao("tem_conta_bancaria"),
        "tem_fornecedor_cliente":    _sim_nao("tem_fornecedor_cliente"),
        "mes_corte_realizado":       cfg["mes_corte_realizado"],
        "reforecast_vigente_ref":    cfg.get("reforecast_vigente_ref") or "",
        "mapaaloc_arquivo":          cfg.get("mapaaloc_arquivo", ""),
        "moeda":                     cfg.get("moeda", "BRL"),
    }


def main():
    if len(sys.argv) < 2:
        print("Uso: python etl.py <CODIGO_CLIENTE>   ex: python etl.py AB")
        sys.exit(1)

    codigo = sys.argv[1].upper()
    cfg    = _load_cfg(codigo)
    _validate_cfg(cfg, codigo)

    dados_dir  = BASE_DIR / "assets" / "dados" / f"{cfg['codigo']} - {cfg['nome']}"
    mapa_path  = dados_dir / f"{cfg['codigo']}_MapaAloc.xlsx"
    lctos_dir  = dados_dir / "f_Lctos"

    if not dados_dir.exists():
        print(f"ERRO: pasta de dados do cliente não encontrada: {dados_dir}")
        sys.exit(1)
    if not mapa_path.exists():
        print(f"ERRO: MapaAloc não encontrado: {mapa_path}")
        sys.exit(1)
    if not lctos_dir.exists():
        print(f"ERRO: pasta de lançamentos não encontrada: {lctos_dir}")
        sys.exit(1)
    logo_path   = BASE_DIR / "assets" / "logo" / "5.png"
    ts          = datetime.now().strftime("%Y%m%d%H%M")
    output_path = BASE_DIR / "relatorios" / f"{codigo}_RelatFinanceiro_{ts}.xlsx"

    dre_cascade    = [(i["n1_names"], i["kpi_label"], i["is_roxo"]) for i in cfg["dre_cascade"]]
    mes_corte_date = pd.Timestamp(f"{cfg['mes_corte_realizado']}-01")
    bu_validos     = set(cfg["bu_validos"])
    cad_config     = _build_cad_config(cfg, lctos_dir)
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
    erros_integ = staging.check_mapa_categorias(mapa) + staging.check_mapa_n3_unico(mapa)
    if erros_integ:
        print(f"  ERRO CRÍTICO: {len(erros_integ)} problema(s) de integridade no MapaAloc")
        for e in erros_integ:
            print(f"    {e['motivo']}")
        f_erros_df   = pd.DataFrame(erros_integ, columns=f_erros_cols)
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
        print(f"  ERRO CRÍTICO: MapaAloc com {len(erros_integ)} problema(s) de integridade")
        print(f"  f_Base  : vazia")
        print(f"  f_Erros : {len(erros_integ)} ocorrência(s) crítica(s)")
        print(f"  Salvo em: {output_path}")
        return

    print(f"  OK — categoria única, N3 único DRE e DFC")

    # ── Lançamentos ───────────────────────────────────────────────────────────
    print("Carregando f_Lctos...")
    lctos, erros_leitura = extractor.load(lctos_dir, cfg)
    print(f"  {len(lctos)} linhas")
    if erros_leitura:
        print(f"  {len(erros_leitura)} arquivo(s) não pôde(ram) ser lido(s)")

    print("Validando erros técnicos...")
    validos, erros_tec = staging.split_errors(lctos, cfg)
    print(f"  Erros técnicos: {len(erros_tec)} | Válidas: {len(validos)}")

    print("Enriquecendo com MapaAloc...")
    enriched, erros_mapa = staging.enrich(validos, mapa, cfg)
    print(f"  _sem_mapa: {enriched['_sem_mapa'].sum()}")

    all_erros = erros_leitura + erros_tec + erros_mapa

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
    print(f"    Erros de leitura : {len(erros_leitura)}")
    print(f"    Erros técnicos   : {len(erros_tec)}")
    print(f"    _sem_mapa        : {len(erros_mapa)}")
    print(f"  Salvo em: {output_path}")


if __name__ == "__main__":
    main()
