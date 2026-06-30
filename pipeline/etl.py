import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import re
import sys
import json
import logging
import importlib
import pandas as pd
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator, ValidationError

import loader
import staging
import builder
import writer
import charts

BASE_DIR = Path(__file__).parent.parent

log = logging.getLogger("etl")


# ─────────────────────────────────────────────────────────────────────────────
# Schema de validação do cad_cliente_*.json (pydantic)
# ─────────────────────────────────────────────────────────────────────────────

class _DreCascadeEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    n1_names:  list[str]
    kpi_label: str
    is_roxo:   bool


class _CadClienteConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    codigo:                 str
    nome:                   str
    segmento_cliente:       str
    status:                 str
    origem_dados_realizado: str
    bu_validos:             list[str]
    tipo_reg_validos:       list[str]
    mapa_fonte:             dict[str, str]
    mes_corte_realizado:    str
    dre_cascade:            list[_DreCascadeEntry]

    @field_validator("mes_corte_realizado")
    @classmethod
    def _check_mes_corte(cls, v: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}", v):
            raise ValueError(f"deve ter formato AAAA-MM, recebeu: {v!r}")
        return v

    @field_validator("bu_validos")
    @classmethod
    def _check_bu_validos(cls, v: list) -> list:
        if not v:
            raise ValueError("não pode ser lista vazia")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de carga e validação
# ─────────────────────────────────────────────────────────────────────────────

def _load_cfg(codigo: str) -> dict:
    cfg_path = BASE_DIR / "assets" / "cad_clientes" / f"cad_cliente_{codigo}.json"
    if not cfg_path.exists():
        log.error(f"ERRO: arquivo de configuração não encontrado: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def _validate_cfg(cfg: dict, codigo: str) -> None:
    try:
        _CadClienteConfig(**cfg)
    except ValidationError as e:
        log.error(f"ERRO: cad_cliente_{codigo}.json inválido:")
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            log.error(f"  • {loc}: {err['msg']}")
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


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def _setup_logging() -> None:
    from logging.handlers import RotatingFileHandler
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("%(message)s"))

    file_h = RotatingFileHandler(
        logs_dir / "etl.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_h.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(console)
    root.addHandler(file_h)


def main():
    _setup_logging()

    if len(sys.argv) < 2:
        log.error("Uso: python etl.py <CODIGO_CLIENTE>   ex: python etl.py AB")
        sys.exit(1)

    codigo = sys.argv[1].upper()
    cfg    = _load_cfg(codigo)
    _validate_cfg(cfg, codigo)

    dados_dir  = BASE_DIR / "assets" / "dados" / f"{cfg['codigo']} - {cfg['nome']}"
    mapa_path  = dados_dir / f"{cfg['codigo']}_MapaAloc.xlsx"
    lctos_dir  = dados_dir / "f_Lctos"
    bancos_dir = dados_dir / "f_bancos"

    if not dados_dir.exists():
        log.error(f"ERRO: pasta de dados do cliente não encontrada: {dados_dir}")
        sys.exit(1)
    if not mapa_path.exists():
        log.error(f"ERRO: MapaAloc não encontrado: {mapa_path}")
        sys.exit(1)
    if not lctos_dir.exists():
        log.error(f"ERRO: pasta de lançamentos não encontrada: {lctos_dir}")
        sys.exit(1)

    logo_path   = BASE_DIR / "assets" / "logo" / "5.png"
    ts          = datetime.now().strftime("%Y%m%d%H%M")
    output_path = BASE_DIR / "relatorios" / f"{codigo}_RelatFinanceiro_{ts}.xlsx"

    dre_cascade    = [(i["n1_names"], i["kpi_label"], i["is_roxo"]) for i in cfg["dre_cascade"]]
    mes_corte_date = pd.Timestamp(f"{cfg['mes_corte_realizado']}-01")
    bu_validos     = set(cfg["bu_validos"])
    cad_config     = _build_cad_config(cfg, lctos_dir)
    f_erros_cols   = staging.F_ERROS_COLS

    extractor = importlib.import_module(f"extractors.extractor_{codigo.lower()}")

    # ── MapaAloc ──────────────────────────────────────────────────────────────
    log.info("Carregando MapaAloc...")
    try:
        mapa = loader.load_mapaaloc(mapa_path)
    except RuntimeError as e:
        log.error(f"ERRO: {e}")
        sys.exit(1)
    log.info(f"  {len(mapa)} categorias ativas")

    f_base_cols = staging.get_f_base_cols(cfg, mapa)

    log.info("Verificando integridade do MapaAloc...")
    erros_integ = staging.check_mapa_categorias(mapa) + staging.check_mapa_n3_unico(mapa)
    if erros_integ:
        log.error(f"  ERRO CRÍTICO: {len(erros_integ)} problema(s) de integridade no MapaAloc")
        for e in erros_integ:
            log.error(f"    {e['motivo']}")
        f_erros_df   = pd.DataFrame(erros_integ, columns=f_erros_cols)
        f_base_vazia = pd.DataFrame(columns=f_base_cols)
        f_saldo, _ = loader.load_f_bancos(bancos_dir, cfg)
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
        log.info(f"Salvando {output_path.name}...")
        try:
            writer.save(wb, output_path)
        except OSError as e:
            log.error(f"ERRO: {e}")
            sys.exit(1)
        log.info(f"\nResumo:")
        log.info(f"  ERRO CRÍTICO: MapaAloc com {len(erros_integ)} problema(s) de integridade")
        log.info(f"  f_Base  : vazia")
        log.info(f"  f_Erros : {len(erros_integ)} ocorrência(s) crítica(s)")
        log.info(f"  Salvo em: {output_path}")
        return

    log.info(f"  OK — categoria única, N3 único DRE e DFC")

    # ── Lançamentos ───────────────────────────────────────────────────────────
    log.info("Carregando f_Lctos...")
    lctos, erros_leitura = extractor.load(lctos_dir, cfg)
    log.info(f"  {len(lctos)} linhas")
    if erros_leitura:
        log.info(f"  {len(erros_leitura)} arquivo(s) não pôde(ram) ser lido(s)")

    log.info("Validando erros técnicos...")
    validos, erros_tec = staging.split_errors(lctos, cfg)
    log.info(f"  Erros técnicos: {len(erros_tec)} | Válidas: {len(validos)}")

    log.info("Enriquecendo com MapaAloc...")
    enriched, erros_mapa = staging.enrich(validos, mapa, cfg)
    log.info(f"  _sem_mapa: {enriched['_sem_mapa'].sum()}")

    all_erros = erros_leitura + erros_tec + erros_mapa

    log.info("Carregando f_SaldoBancos...")
    f_saldo, erros_bancos = loader.load_f_bancos(bancos_dir, cfg)
    if f_saldo.empty:
        log.info("  f_bancos não encontrado — f_SaldoBancos vazio")
    else:
        log.info(f"  {len(f_saldo)} linhas carregadas de f_bancos/")
    all_erros.extend(erros_bancos)

    log.info("Montando f_Base...")
    f_base = staging.build_f_base(enriched, f_base_cols)
    log.info(f"  {len(f_base)} linhas × {len(f_base.columns)} colunas")

    f_erros_df = pd.DataFrame(all_erros if all_erros else [], columns=f_erros_cols)

    # ── Workbook ──────────────────────────────────────────────────────────────
    log.info("Construindo workbook...")
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

    log.info(f"Salvando {output_path.name}...")
    try:
        writer.save(wb, output_path)
        charts.patch_charts(output_path)
    except OSError as e:
        log.error(f"ERRO: {e}")
        sys.exit(1)

    log.info(f"\nResumo:")
    log.info(f"  f_Base  : {len(f_base)} linhas, {len(f_base.columns)} colunas")
    log.info(f"  f_Erros : {len(all_erros)} ocorrências")
    log.info(f"    Erros de leitura : {len(erros_leitura)}")
    log.info(f"    Erros técnicos   : {len(erros_tec)}")
    log.info(f"    _sem_mapa        : {len(erros_mapa)}")
    log.info(f"  Salvo em: {output_path}")


if __name__ == "__main__":
    main()
