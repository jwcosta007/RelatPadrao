# Roadmap — RelatPadrao / AZ Resultados

> Visão estratégica de médio e longo prazo. Para tasks concretas e rastreáveis, usar GitHub Issues.
> Detalhamento técnico das decisões em aberto: `SDD/SRS_RegrasRelatPadrao.md` §7.1.

---

## Concluído

- ✅ **Suite de testes automatizados** — 41 testes em `tests/` (28 unitários + 13 integração). Rodar com `python -m pytest tests/ -v`.
- ✅ **Reestruturação do pipeline** — entry point único `etl.py <CODIGO>`; extratores por cliente em `extractors/`; staging universal; configuração por JSON.
- ✅ **Validação do JSON de configuração** — schema pydantic (`_CadClienteConfig`) em `etl.py`; chaves obrigatórias, tipos, `mes_corte_realizado` (AAAA-MM), `bu_validos` não-vazio e estrutura de `dre_cascade` validados na carga. Erros apontam o campo exato.
- ✅ **Logging estruturado no ETL** — `print` substituídos por `logging` em `etl.py` e `loader.py`; nível e formato configuráveis via `basicConfig` sem alterar o código.
- ✅ **Nova arquitetura de dados de entrada** — `assets/dados/{SIGLA} - {Nome}/`; MapaAloc sem versão no nome; `f_Lctos/` como drop zone. ETL deriva caminhos por convenção (sem `path_mapa`/`path_lctos` no JSON). SRS §4.4.
- ✅ **Verificação N3-único (DRE e DFC)** — `staging.check_mapa_n3_unico()` executada antes de qualquer carga; ETL para com erro claro se houver violação. SRS §6.1.
- ✅ **Cliente AB Aeterno em produção** — DRE Gerencial, DFC, KPIs, f_Base, f_Erros, f_SaldoBancos, cad_cliente, Lista, check.

---

## Próxima iteração

- **Implantação GCG Clínica:** `cad_cliente_GCG.json` + `extractor_gcg.py` (Conta Azul XLS) + leitura de `f_bancos/f_Bancos.xlsx` no loader. Em desenvolvimento.
- **AB — `f_bancos/` com saldos reais:** criar `assets/dados/AB - AB Aeterno/f_bancos/AB_f_Bancos.xlsx` com histórico de saldos mensais por conta/BU. O ETL já suporta a pasta por convenção (SRS §4.2); nenhuma mudança de código necessária. Elimina o CAIXA INÍCIO = 0 no DFC AB.
- **Implantação demais clientes (ES, LA, OS):** aguardar validação GCG; cadastros base em `assets/cad_clientes/` já existem.
- **Aba `check` — fórmulas de validação:** soma KPI vs cascata N3; `_sem_mapa = 0`; contador `f_Erros` (vermelho se > 0); bate colisão Realizado×Projeção; bate DFC caixa; BU duplo-check. Design em aberto — ver `SDD/SRS_RegrasRelatPadrao.md` §7.1.
  - **Pendência C:** IF de corte Realizado×Projeção sem rastreabilidade — builder escreve o IF mas não há verificação de que está em todas as células; a aba `check` é o remédio natural.
  - **Pendência D:** KPIs definidos por flag no MapaAloc sem validação de rótulo — flag `kpi_ebitda = Sim` pode estar na linha errada sem alerta; validar na `check` ou no ETL.
  - **Pendência E:** Fallback saldo zero sem trilha de correção — quando saldo real é preenchido, relatório anterior não é remarcado como desatualizado. Baixa prioridade.
- **`d_Calendario` / `d_Feriados`:** criar somente quando `tem_data_competencia = Sim` ou `tem_data_vencimento = Sim` no `cad_cliente`. AB não usa; GCG a avaliar.

---

## Médio prazo

- **Frente Projeções/Forecast (§10):** aba O×R com seletores duplos, gráfico FP&A 3 séries, bate colisão na `check`. Design FECHADO em `SDD/SRS_RegrasRelatPadrao.md` §10; implementação pendente.
- **Gerador de MapaAloc:** sugere KPIs-padrão; alerta KPI sem nenhum "Sim"; gera header 2 linhas + checagem N3-único automática (DRE+DFC).
- **Gerador de DRE/DFC a partir do MapaAloc:** cascata + fórmulas SUMIFS; invariante §6.10.

---

## Longo prazo / greenfield

- **`id_lcto` persistente** (chave natural/hash) → migração Python/PostgreSQL.
- Camada 0 plena, conector-por-ERP, fato-magra, KPI flags como tabela de associação → backlog greenfield.
