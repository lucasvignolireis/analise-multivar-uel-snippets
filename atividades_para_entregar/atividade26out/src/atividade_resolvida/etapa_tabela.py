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

LIMITE_LINHAS_EXIBICAO = 1000

CONJUNTOS = {
    "xvalid": "Conjunto de validação (X)",
    "xcalib": "Conjunto de calibração (X)",
    "yvalid": "Conjunto de validação (Y)",
    "ycalib": "Conjunto de calibração (Y)",
}

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
        ui.h5("PCA comparativo (Xcalib)"),
        ui.p("Configure duas análises PCA para comparação (A e B)."),
        ui.div(
            ui.div(
                ui.h6("PCA A"),
                ui.output_plot("grafico_variancia_a"),
                ui.output_ui("controles_pca_a_ui"),
                class_="pca-box",
            ),
            ui.div(
                ui.h6("PCA B"),
                ui.output_plot("grafico_variancia_b"),
                ui.output_ui("controles_pca_b_ui"),
                class_="pca-box",
            ),
        ),
        ui.hr(),
        ui.input_action_button("confirmar_tabela", "Confirmar dados e gerar relatório"),
    )


@module.server
def etapa_tabela_server(input, output, session, *, estado_wizard):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    PASTA_OUTPUTS = BASE_DIR / "outputs"

    gerando = reactive.value(False)
    erro_geracao = reactive.value("")

    def _get_conf_pca():
        dados = estado_wizard().get("passos", {}).get("tabela", {}).get("dados", {})
        pca = dados.get("pca", {})
        comp = pca.get("comparativo", {})
        a = comp.get("a", {})
        b = comp.get("b", {})
        return a, b

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

    @render.plot
    def grafico_variancia_a():
        df = _df_xcalib()
        if df is None:
            return None
        a, _ = _get_conf_pca()
        n_pcs = int(a.get("n_pcs", 2))
        centragem = a.get("centragem", "media")
        auto = bool(a.get("autoescalonamento", True))
        _, var, var_acum = variancia_explicada(df, centragem=centragem, autoescalonamento=auto)
        n_pcs = max(1, min(n_pcs, len(var)))
        fig = figura_variancia(var, var_acum, n_pcs=n_pcs)
        fig.axes[0].set_title("PCA A: variância explicada")
        return fig

    @render.plot
    def grafico_variancia_b():
        df = _df_xcalib()
        if df is None:
            return None
        _, b = _get_conf_pca()
        n_pcs = int(b.get("n_pcs", 2))
        centragem = b.get("centragem", "media")
        auto = bool(b.get("autoescalonamento", False))
        _, var, var_acum = variancia_explicada(df, centragem=centragem, autoescalonamento=auto)
        n_pcs = max(1, min(n_pcs, len(var)))
        fig = figura_variancia(var, var_acum, n_pcs=n_pcs)
        fig.axes[0].set_title("PCA B: variância explicada")
        return fig

    @render.ui
    def controles_pca_a_ui():
        df = _df_xcalib()
        if df is None:
            return None
        a, _ = _get_conf_pca()
        _, var, _ = variancia_explicada(
            df,
            centragem=a.get("centragem", "media"),
            autoescalonamento=bool(a.get("autoescalonamento", True)),
        )
        n_max = len(var)
        atual = max(1, min(int(a.get("n_pcs", 2)), n_max))

        return ui.TagList(
            ui.input_numeric("pca_a_n_pcs", f"Número de PCs (1 a {n_max}):", value=atual, min=1, max=n_max, step=1),
            ui.input_select(
                "pca_a_centragem",
                "Centragem:",
                choices={"media": "Na média", "nenhuma": "Sem centragem"},
                selected=a.get("centragem", "media"),
            ),
            ui.input_checkbox(
                "pca_a_autoescalonamento",
                "Autoescalonamento (desvio padrão)",
                value=bool(a.get("autoescalonamento", True)),
            ),
        )

    @render.ui
    def controles_pca_b_ui():
        df = _df_xcalib()
        if df is None:
            return None
        _, b = _get_conf_pca()
        _, var, _ = variancia_explicada(
            df,
            centragem=b.get("centragem", "media"),
            autoescalonamento=bool(b.get("autoescalonamento", False)),
        )
        n_max = len(var)
        atual = max(1, min(int(b.get("n_pcs", 2)), n_max))

        return ui.TagList(
            ui.input_numeric("pca_b_n_pcs", f"Número de PCs (1 a {n_max}):", value=atual, min=1, max=n_max, step=1),
            ui.input_select(
                "pca_b_centragem",
                "Centragem:",
                choices={"media": "Na média", "nenhuma": "Sem centragem"},
                selected=b.get("centragem", "media"),
            ),
            ui.input_checkbox(
                "pca_b_autoescalonamento",
                "Autoescalonamento (desvio padrão)",
                value=bool(b.get("autoescalonamento", False)),
            ),
        )

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

        # PCA A
        a_n = input.pca_a_n_pcs()
        a_c = input.pca_a_centragem() or "media"
        a_s = bool(input.pca_a_autoescalonamento())

        # PCA B
        b_n = input.pca_b_n_pcs()
        b_c = input.pca_b_centragem() or "media"
        b_s = bool(input.pca_b_autoescalonamento())

        if a_n is None or b_n is None:
            erro_geracao.set("Escolha um número de PCs válido em PCA A e PCA B.")
            return

        a_n = int(a_n)
        b_n = int(b_n)

        if a_c not in ("media", "nenhuma"):
            a_c = "media"
        if b_c not in ("media", "nenhuma"):
            b_c = "media"

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

            pca_a = gerar_pca(
                dfs["xcalib"], dfs["xvalid"], pasta_saida,
                n_pcs=a_n, centragem=a_c, autoescalonamento=a_s, prefixo="pca_a",
            )
            pca_b = gerar_pca(
                dfs["xcalib"], dfs["xvalid"], pasta_saida,
                n_pcs=b_n, centragem=b_c, autoescalonamento=b_s, prefixo="pca_b",
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
            d_tab.setdefault("pca", {}).setdefault("comparativo", {})
            d_tab["pca"]["comparativo"]["a"] = {
                "nome": "PCA A",
                "n_pcs": a_n,
                "centragem": a_c,
                "autoescalonamento": a_s,
            }
            d_tab["pca"]["comparativo"]["b"] = {
                "nome": "PCA B",
                "n_pcs": b_n,
                "centragem": b_c,
                "autoescalonamento": b_s,
            }

            d_rel = s["passos"]["relatorio"]["dados"]
            d_rel["pasta_saida"] = str(pasta_saida)

            contexto_typst = {
                "conjuntos": conjuntos,
                "tabelas": tabelas,
                "scatter_nome": nome_png,
                "elementos": elementos,
                "graficos_elementos": graficos_elementos,
                "pca_comp": {"a": pca_a, "b": pca_b},
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

            d_rel["typ_path"] = str(caminho_typ)
            d_rel["pdf_path"] = str(caminho_pdf)
            d_rel["arquivos"] = (
                [nome_png]
                + [g["nome"] for g in graficos_elementos]
                + pca_a.get("arquivos", [])
                + pca_b.get("arquivos", [])
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