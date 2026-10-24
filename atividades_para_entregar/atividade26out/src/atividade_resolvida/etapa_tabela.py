from copy import deepcopy
from datetime import datetime
from pathlib import Path
import subprocess

import pandas as pd
from shiny import module, ui, render, reactive

from atividade_resolvida.relatorio_typst import renderizar_relatorio_typst
from atividade_resolvida.grafico_visualizacao_inicial_dados import (
    gerar_scatter_elementos,
    gerar_scatter_por_elemento,
)
from atividade_resolvida.pca_analise import (
    gerar_pca,
    variancia_explicada,
    figura_variancia,
)
from atividade_resolvida.regressao_simples import gerar_regressao_simples

LIMITE_LINHAS_EXIBICAO = 1000

CONJUNTOS = {
    "xvalid": "Conjunto de validação (X)",
    "xcalib": "Conjunto de calibração (X)",
    "yvalid": "Conjunto de validação (Y)",
    "ycalib": "Conjunto de calibração (Y)",
}

PCA_KEYS = ["a", "b", "c", "d"]

CSS_TABELAS = """
.tabela-scroll {
  max-height: 400px;
  overflow: auto;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  scrollbar-gutter: stable;
  scrollbar-width: auto;
  scrollbar-color: #6b7280 #e5e7eb;
}
.tabela-scroll::-webkit-scrollbar { width: 14px; height: 14px; }
.tabela-scroll::-webkit-scrollbar-track { background: #e5e7eb; }
.tabela-scroll::-webkit-scrollbar-thumb {
  background: #6b7280;
  border-radius: 8px;
  border: 3px solid #e5e7eb;
}
.tabela-scroll::-webkit-scrollbar-thumb:hover { background: #4b5563; }

.tabela-scroll table {
  --bs-table-bg: transparent;
  border-collapse: separate;
  border-spacing: 0;
  margin-bottom: 0;
  width: 100%;
  font-size: 0.8rem;
}
.tabela-scroll th, .tabela-scroll td { padding: 0.25rem 0.5rem; }
.tabela-scroll thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #e5e7eb;
  border-bottom: 2px solid #9ca3af;
}

.pca-box {
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0.8rem;
  margin-bottom: 0.8rem;
  background: #fafafa;
}
"""


def _pca_card_ui(k: str):
    K = k.upper()
    return ui.div(
        ui.h6(f"PCA {K}"),
        ui.output_plot(f"grafico_variancia_{k}"),
        ui.output_ui(f"controles_pca_{k}_ui"),
        class_="pca-box",
    )


@module.ui
def etapa_tabela_ui():
    blocos = []
    for chave, titulo in CONJUNTOS.items():
        blocos.append(ui.h5(titulo))
        blocos.append(ui.output_text(f"status_{chave}"))
        blocos.append(ui.div(ui.output_table(f"tabela_{chave}"), class_="tabela-scroll"))
        blocos.append(ui.hr())

    return ui.card(
        ui.tags.style(CSS_TABELAS),
        ui.h4("Passo 2: Conferir os dados"),
        ui.output_text("status_geral"),
        *blocos,
        ui.h5("PCA comparativo (4 análises)"),
        ui.p("Configure as análises PCA A/B/C/D (agregação, n_pcs, centragem e autoescalonamento)."),
        _pca_card_ui("a"),
        _pca_card_ui("b"),
        _pca_card_ui("c"),
        _pca_card_ui("d"),
        ui.hr(),
        ui.h5("Regressão linear simples"),
        ui.output_ui("seletor_elemento_ui"),
        ui.hr(),
        ui.input_action_button("confirmar_tabela", "Confirmar dados e gerar relatório"),
    )


@module.server
def etapa_tabela_server(input, output, session, *, estado_wizard):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    PASTA_OUTPUTS = BASE_DIR / "outputs"

    gerando = reactive.value(False)
    erro_geracao = reactive.value("")

    def _fonte(chave):
        s = estado_wizard()["passos"]["carregamento"]
        d = s["dados"]
        rel = d.get(f"{chave}_path")
        sep = d.get(f"{chave}_sep", ",")
        if not rel:
            return None, sep, None
        pasta_conf = Path(s["conf"].get("path", "dados/"))
        if not pasta_conf.is_absolute():
            pasta_conf = (BASE_DIR / pasta_conf).resolve()
        return rel, sep, (pasta_conf / rel).resolve()

    def _ler(chave):
        _, sep, caminho = _fonte(chave)
        if caminho is None:
            return None
        try:
            return pd.read_csv(caminho, sep=sep)
        except Exception:
            return None

    @reactive.calc
    def _df_xvalid():
        return _ler("xvalid")

    @reactive.calc
    def _df_xcalib():
        return _ler("xcalib")

    @reactive.calc
    def _df_yvalid():
        return _ler("yvalid")

    @reactive.calc
    def _df_ycalib():
        return _ler("ycalib")

    DFS = {
        "xvalid": _df_xvalid,
        "xcalib": _df_xcalib,
        "yvalid": _df_yvalid,
        "ycalib": _df_ycalib,
    }

    def _status(df):
        if df is None:
            return "Não carregado. Confirme os arquivos na etapa anterior."
        n_linhas, n_colunas = df.shape
        if n_linhas > LIMITE_LINHAS_EXIBICAO:
            return (
                f"{n_linhas} linhas, {n_colunas} colunas. "
                f"Exibindo somente as primeiras {LIMITE_LINHAS_EXIBICAO} linhas."
            )
        return f"{n_linhas} linhas, {n_colunas} colunas. Exibindo todas as linhas."

    def _exibicao(df):
        if df is None:
            return pd.DataFrame()
        return df.head(LIMITE_LINHAS_EXIBICAO)

    def _ler_input_safe(input_id, default=None):
        try:
            v = getattr(input, input_id)()
            if v is None:
                return default
            return v
        except Exception:
            return default

    def _pca_conf_estado():
        dados = estado_wizard().get("passos", {}).get("tabela", {}).get("dados", {})
        pca = dados.get("pca", {})
        analises = pca.get("analises", {})
        out = {}
        defaults = {
            "a": {"nome": "PCA A", "agregar": False, "n_pcs": 2, "centragem": "media", "autoescalonamento": False},
            "b": {"nome": "PCA B", "agregar": False, "n_pcs": 4, "centragem": "media", "autoescalonamento": True},
            "c": {"nome": "PCA C", "agregar": True,  "n_pcs": 2, "centragem": "media", "autoescalonamento": False},
            "d": {"nome": "PCA D", "agregar": True,  "n_pcs": 4, "centragem": "media", "autoescalonamento": True},
        }
        for k in PCA_KEYS:
            base = defaults[k].copy()
            base.update(analises.get(k, {}))
            out[k] = base
        return out

    def _pca_conf_input(k: str):
        est = _pca_conf_estado()[k]
        n_pcs = int(_ler_input_safe(f"pca_{k}_n_pcs", est["n_pcs"]))
        centragem = _ler_input_safe(f"pca_{k}_centragem", est["centragem"])
        auto = bool(_ler_input_safe(f"pca_{k}_autoescalonamento", est["autoescalonamento"]))
        agregar = bool(_ler_input_safe(f"pca_{k}_agregar", est["agregar"]))

        if centragem not in ("media", "nenhuma"):
            centragem = "media"

        return {
            "nome": est.get("nome", f"PCA {k.upper()}"),
            "agregar": agregar,
            "n_pcs": n_pcs,
            "centragem": centragem,
            "autoescalonamento": auto,
        }

    def _elementos_regressao():
        xc, yc = _df_xcalib(), _df_ycalib()
        xv, yv = _df_xvalid(), _df_yvalid()
        if any(d is None for d in (xc, yc, xv, yv)):
            return []
        return [
            str(c) for c in xc.columns
            if str(c) != "Amostra"
            and (str(c) in yc.columns)
            and (str(c) in xv.columns)
            and (str(c) in yv.columns)
        ]

    @render.ui
    def seletor_elemento_ui():
        els = _elementos_regressao()
        if not els:
            return ui.p("Carregue os dados para escolher o elemento.")

        est = estado_wizard().get("passos", {}).get("tabela", {}).get("dados", {})
        padrao_estado = est.get("elemento_analisado", "V")
        atual_input = _ler_input_safe("elemento_regressao", None)

        if atual_input in els:
            selecionado = atual_input
        elif padrao_estado in els:
            selecionado = padrao_estado
        else:
            selecionado = els[0]

        return ui.input_select(
            "elemento_regressao",
            "Elemento para regressão linear simples:",
            choices=els,
            selected=selecionado,
        )

    @render.text
    def status_xvalid():
        return _status(_df_xvalid())

    @render.text
    def status_xcalib():
        return _status(_df_xcalib())

    @render.text
    def status_yvalid():
        return _status(_df_yvalid())

    @render.text
    def status_ycalib():
        return _status(_df_ycalib())

    @render.table
    def tabela_xvalid():
        return _exibicao(_df_xvalid())

    @render.table
    def tabela_xcalib():
        return _exibicao(_df_xcalib())

    @render.table
    def tabela_yvalid():
        return _exibicao(_df_yvalid())

    @render.table
    def tabela_ycalib():
        return _exibicao(_df_ycalib())

    def _registrar_pca(k: str):
        @output(id=f"grafico_variancia_{k}")
        @render.plot
        def _plot():
            df = _df_xcalib()
            if df is None:
                return None

            est = _pca_conf_estado()[k]

            n_pcs = int(_ler_input_safe(f"pca_{k}_n_pcs", est["n_pcs"]))
            centragem = _ler_input_safe(f"pca_{k}_centragem", est["centragem"])
            auto = bool(_ler_input_safe(f"pca_{k}_autoescalonamento", est["autoescalonamento"]))

            if centragem not in ("media", "nenhuma"):
                centragem = "media"

            _, var, var_acum = variancia_explicada(
                df, centragem=centragem, autoescalonamento=auto
            )
            n_pcs = max(1, min(n_pcs, len(var)))

            return figura_variancia(
                var,
                var_acum,
                n_pcs=n_pcs,
                titulo=f"PCA {k.upper()}: variância explicada",
            )

        @output(id=f"controles_pca_{k}_ui")
        @render.ui
        def _ui():
            df = _df_xcalib()
            if df is None:
                return None

            est = _pca_conf_estado()[k]

            _, var, _ = variancia_explicada(
                df,
                centragem=est["centragem"],
                autoescalonamento=bool(est["autoescalonamento"]),
            )
            n_max = len(var)
            n_atual = max(1, min(int(est["n_pcs"]), n_max))

            return ui.TagList(
                ui.input_checkbox(
                    f"pca_{k}_agregar",
                    "Agregar Xcalib + Xvalid para ajustar PCA",
                    value=bool(est["agregar"]),
                ),
                ui.input_numeric(
                    f"pca_{k}_n_pcs",
                    f"Número de PCs (1 a {n_max}):",
                    value=n_atual,
                    min=1,
                    max=n_max,
                    step=1,
                ),
                ui.input_select(
                    f"pca_{k}_centragem",
                    "Centragem:",
                    choices={"media": "Na média", "nenhuma": "Sem centragem"},
                    selected=est["centragem"] if est["centragem"] in ("media", "nenhuma") else "media",
                ),
                ui.input_checkbox(
                    f"pca_{k}_autoescalonamento",
                    "Autoescalonamento (desvio padrão)",
                    value=bool(est["autoescalonamento"]),
                ),
            )

    for _k in PCA_KEYS:
        _registrar_pca(_k)

    @render.text
    def status_geral():
        if gerando():
            return "Gerando relatório... aguarde."
        if erro_geracao():
            return f"Erro ao gerar relatório: {erro_geracao()}"
        if any(f() is None for f in DFS.values()):
            return "Selecione e confirme os arquivos na etapa anterior."
        return "Os quatro conjuntos foram carregados."

    @reactive.effect
    @reactive.event(input.confirmar_tabela)
    def _confirmar_tabela():
        erro_geracao.set("")
        dfs = {chave: f() for chave, f in DFS.items()}
        if any(df is None for df in dfs.values()):
            erro_geracao.set("Algum conjunto não pôde ser lido.")
            return

        confs = {k: _pca_conf_input(k) for k in PCA_KEYS}

        elemento_reg = _ler_input_safe("elemento_regressao", None)
        if elemento_reg is None:
            erro_geracao.set("Escolha um elemento para regressão linear simples.")
            return

        gerando.set(True)
        try:
            nome_pasta = datetime.now().strftime("%Y-%m-%d-%H-%M")
            pasta_saida = PASTA_OUTPUTS / nome_pasta
            pasta_saida.mkdir(parents=True, exist_ok=True)

            nome_png = "grafico_visualizacao_inicial_dados.png"
            elementos = gerar_scatter_elementos(
                dfs["xcalib"], dfs["ycalib"],
                dfs["xvalid"], dfs["yvalid"],
                pasta_saida / nome_png,
            )

            graficos_elementos = gerar_scatter_por_elemento(
                dfs["xcalib"], dfs["ycalib"],
                dfs["xvalid"], dfs["yvalid"],
                elementos,
                pasta_saida,
            )

            pca_resultados = {}
            for k in PCA_KEYS:
                cfg = confs[k]
                pca_resultados[k] = gerar_pca(
                    dfs["xcalib"],
                    dfs["xvalid"],
                    pasta_saida,
                    n_pcs=cfg["n_pcs"],
                    centragem=cfg["centragem"],
                    autoescalonamento=cfg["autoescalonamento"],
                    prefixo=f"pca_{k}",
                    agregar=cfg["agregar"],
                )
                pca_resultados[k]["nome"] = cfg["nome"]

            regressao = gerar_regressao_simples(
                dfs["xcalib"],
                dfs["ycalib"],
                dfs["xvalid"],
                dfs["yvalid"],
                elemento_reg,
                pasta_saida,
            )

            conjuntos = []
            for chave, titulo in CONJUNTOS.items():
                rel, sep, _ = _fonte(chave)
                df = dfs[chave]
                conjuntos.append({
                    "chave": chave,
                    "titulo": titulo,
                    "path": rel,
                    "separador": sep,
                    "n_linhas": int(df.shape[0]),
                    "n_colunas": int(df.shape[1]),
                    "colunas": [str(c) for c in df.columns],
                })

            tabelas = []
            for chave, titulo in CONJUNTOS.items():
                rel, _, _ = _fonte(chave)
                df = dfs[chave]
                exib = df.head(LIMITE_LINHAS_EXIBICAO).fillna("")
                tabelas.append({
                    "titulo": titulo,
                    "path": rel,
                    "n_linhas": int(df.shape[0]),
                    "n_exibidas": int(exib.shape[0]),
                    "colunas": [str(c) for c in exib.columns],
                    "linhas": exib.astype(str).values.tolist(),
                })

            s = deepcopy(estado_wizard())

            d_tab = s["passos"]["tabela"]["dados"]
            d_tab["conjuntos"] = conjuntos
            d_tab.setdefault("pca", {})
            d_tab["pca"]["analises"] = confs
            d_tab["elemento_analisado"] = elemento_reg

            d_rel = s["passos"]["relatorio"]["dados"]
            d_rel["pasta_saida"] = str(pasta_saida)

            contexto_typst = {
                "conjuntos": conjuntos,
                "tabelas": tabelas,
                "scatter_nome": nome_png,
                "elementos": elementos,
                "graficos_elementos": graficos_elementos,
                "pca_analises": pca_resultados,
                "pca_ordem": PCA_KEYS,
                "regressao": regressao,
            }

            nome_typ = "relatorio.typ"
            nome_pdf = "relatorio.pdf"
            caminho_typ = pasta_saida / nome_typ
            caminho_pdf = pasta_saida / nome_pdf

            conteudo_typ = renderizar_relatorio_typst(
                contexto_typst,
                template_name="template_relatorio.typ.j2",
            )
            caminho_typ.write_text(conteudo_typ, encoding="utf-8")

            subprocess.run(
                ["typst", "compile", str(caminho_typ), str(caminho_pdf)],
                check=True,
                cwd=str(pasta_saida),
            )

            pca_arquivos = []
            for k in PCA_KEYS:
                pca_arquivos.extend(pca_resultados[k].get("arquivos", []))

            d_rel["typ_path"] = str(caminho_typ)
            d_rel["pdf_path"] = str(caminho_pdf)
            d_rel["arquivos"] = (
                [nome_png]
                + [g["nome"] for g in graficos_elementos]
                + pca_arquivos
                + regressao.get("arquivos", [])
                + [nome_typ, nome_pdf]
            )

            s["passos"]["tabela"]["estado"] = "preenchido"
            s["passos"]["relatorio"]["estado"] = "preenchido"
            s["etapa_atual"] = "relatorio"

            estado_wizard.set(s)

        except Exception as e:
            import traceback
            traceback.print_exc()
            erro_geracao.set(f"{type(e).__name__}: {e}")
        finally:
            gerando.set(False)