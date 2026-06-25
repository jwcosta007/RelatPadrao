# Roadmap — RelatPadrao / AZ Resultados

> Visão estratégica de médio e longo prazo. Para tasks concretas e rastreáveis, usar GitHub Issues.
> Detalhamento técnico das decisões em aberto: `SDD/SRS_RegrasRelatPadrao.md` §7.1.

---

## Próxima iteração (pós-piloto AB)

- **Aba `check` — fórmulas de validação:** soma KPI vs cascata N3; `_sem_mapa = 0`; contador `f_Erros` (vermelho se > 0); bate colisão Realizado×Projeção; bate DFC caixa; BU duplo-check. Design em aberto — ver `SDD/SRS_RegrasRelatPadrao.md` §7.1.
- **Implantação demais clientes (ES, GCG, LA, OS):** aguardar validação piloto AB; criar `etl_<codigo>.py` por cliente. Cadastros em `assets/cad_clientes/` já existem.
- **`d_Calendario` / `d_Feriados`:** criar somente quando `tem_data_competencia = Sim` ou `tem_data_vencimento = Sim` no `cad_cliente`. AB não usa.
- **Suite de testes automatizados:** cobrir DRE, DFC simplificado, f_Base, KPIs e integridade do MapaAloc.

## Médio prazo

- **Frente Projeções/Forecast (§10):** aba O×R com seletores duplos, gráfico FP&A 3 séries, bate colisão na `check`. Design FECHADO em `SDD/SRS_RegrasRelatPadrao.md` §10; implementação pendente.
- **Gerador de MapaAloc:** sugere KPIs-padrão; alerta KPI sem nenhum "Sim"; gera header 2 linhas + checagem N3-único automática (DRE+DFC).
- **Gerador de DRE/DFC a partir do MapaAloc:** cascata + fórmulas SUMIFS; invariante §6.10.

## Longo prazo / greenfield

- **`id_lcto` persistente** (chave natural/hash) → migração Python/PostgreSQL.
- Camada 0 plena, conector-por-ERP, fato-magra, KPI flags como tabela de associação → backlog greenfield.
