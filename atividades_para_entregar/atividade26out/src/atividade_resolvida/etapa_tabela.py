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
  overflow: auto;                 /* rola só aqui dentro */
  background: #f3f4f6;            /* cinza bem claro */
  border: 1px solid #d1d5db;
  border-radius: 8px;
  scrollbar-gutter: stable;       /* reserva espaço, a barra não "pula" */
  scrollbar-width: auto;          /* Firefox: barra normal, não fina */
  scrollbar-color: #6b7280 #e5e7eb;
}

/* Chrome/Edge/Safari: barra mais grossa e visível */
.tabela-scroll::-webkit-scrollbar { width: 14px; height: 14px; }
.tabela-scroll::-webkit-scrollbar-track { background: #e5e7eb; }
.tabela-scroll::-webkit-scrollbar-thumb {
  background: #6b7280;
  border-radius: 8px;
  border: 3px solid #e5e7eb;
}
.tabela-scroll::-webkit-scrollbar-thumb:hover { background: #4b5563; }

.tabela-scroll table {
  --bs-table-bg: transparent;     /* deixa o cinza do container aparecer */
  border-collapse: separate;      /* necessário p/ borda do header sticky */
  border-spacing: 0;
  margin-bottom: 0;
  width: 100%;
  font-size: 0.8rem;              /* fonte menor */
}

/* células mais compactas */
.tabela-scroll th,
.tabela-scroll td {
  padding: 0.25rem 0.5rem;
}

/* cabeçalho fixo: só o tbody rola */
.tabela-scroll thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #e5e7eb;
  border-bottom: 2px solid #9ca3af;
}
"""


@module.ui
def etapa_tabela_ui():
    blocos = []
    for chave, titulo in CONJUNTOS.items():
        blocos.append(ui.h5(titulo))
        blocos.append(ui.output_text(f"status_{chave}"))
        blocos.append(
            ui.div(ui.output_table(f"tabela_{chave}"), class_="tabela-scroll")
        )
        blocos.append(ui.hr())

    return ui.card(
        ui.tags.style(CSS_TABELAS),
        ui.h4("Passo 2: Conferir os dados"),
        ui.output_text("status_geral"),
        *blocos,
        ui.h5("PCA (Xcalib)"),
        ui.p(
            "Veja a variância explicada e escolha os parâmetros da análise "
            "(número de PCs, centragem e autoescalonamento)."
        ),
        ui.output_plot("grafico_variancia"),
        ui.output_ui("controles_pca_ui"),
        ui.hr(),
        ui.input_action_button("confirmar_tabela", "Confirmar dados e gerar relatório"),
    )


@module.server
def etapa_tabela_server(input, output, session, *, estado_wizard):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../atividade26out
    PASTA_OUTPUTS = BASE_DIR / "outputs"

    gerando = reactive.value(False)
    erro_geracao = reactive.value("")

    def _fonte(chave):
        """Devolve (path relativo a dados/, separador, path absoluto) do conjunto."""
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
    def grafico_variancia():
        df = _df_xcalib()
        if df is None:
            return None

        _, var, var_acum = variancia_explicada(df)

        with reactive.isolate():
            conf_pca = (
                estado_wizard()
                .get("passos", {})
                .get("tabela", {})
                .get("dados", {})
                .get("pca", {})
            )
            n_pcs = int(conf_pca.get("n_pcs", 2))

        n_pcs = max(1, min(n_pcs, len(var)))
        return figura_variancia(var, var_acum, n_pcs=n_pcs)

    @render.ui
    def controles_pca_ui():
        df = _df_xcalib()
        if df is None:
            return None

        _, var, _ = variancia_explicada(df)
        n_max = len(var)

        with reactive.isolate():
            conf_pca = (
                estado_wizard()
                .get("passos", {})
                .get("tabela", {})
                .get("dados", {})
                .get("pca", {})
            )
            n_pcs_atual = int(conf_pca.get("n_pcs", 2))
            centragem_atual = conf_pca.get("centragem", "media")
            auto_atual = bool(conf_pca.get("autoescalonamento", False))

        n_pcs_atual = max(1, min(n_pcs_atual, n_max))

        return ui.TagList(
            ui.input_numeric(
                "n_pcs",
                f"Número de PCs (1 a {n_max}):",
                value=n_pcs_atual,
                min=1,
                max=n_max,
                step=1,
            ),
            ui.input_select(
                "pca_centragem",
                "Centragem:",
                choices={"media": "Na média", "nenhuma": "Sem centragem"},
                selected=centragem_atual if centragem_atual in ("media", "nenhuma") else "media",
            ),
            ui.input_checkbox(
                "pca_autoescalonamento",
                "Autoescalonamento (desvio padrão)",
                value=auto_atual,
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

        # parâmetros PCA escolhidos na UI
        n_pcs = input.n_pcs()
        if n_pcs is None:
            erro_geracao.set("Escolha um número de PCs válido.")
            return
        n_pcs = int(n_pcs)

        centragem = input.pca_centragem() or "media"
        if centragem not in ("media", "nenhuma"):
            centragem = "media"

        autoescalonamento = bool(input.pca_autoescalonamento())

        gerando.set(True)
        try:
            nome_pasta = datetime.now().strftime("%Y-%m-%d-%H-%M")
            pasta_saida = PASTA_OUTPUTS / nome_pasta
            pasta_saida.mkdir(parents=True, exist_ok=True)

            # 0) Scatter plot geral (X vs Y por elemento químico)
            nome_png = "grafico_visualizacao_inicial_dados.png"
            elementos = gerar_scatter_elementos(
                dfs["xcalib"], dfs["ycalib"],
                dfs["xvalid"], dfs["yvalid"],
                pasta_saida / nome_png,
            )

            # 0b) Um scatter por elemento
            graficos_elementos = gerar_scatter_por_elemento(
                dfs["xcalib"], dfs["ycalib"],
                dfs["xvalid"], dfs["yvalid"],
                elementos,
                pasta_saida,
            )

            # 0c) PCA (ajustado em Xcalib) com parâmetros escolhidos
            pca = gerar_pca(
                dfs["xcalib"],
                dfs["xvalid"],
                pasta_saida,
                n_pcs=n_pcs,
                centragem=centragem,
                autoescalonamento=autoescalonamento,
            )

            # 1) Resumo dos conjuntos
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

            # dados das tabelas para anexo no Typst
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
            d_tab["pca"]["n_pcs"] = n_pcs
            d_tab["pca"]["centragem"] = centragem
            d_tab["pca"]["autoescalonamento"] = autoescalonamento

            d_rel = s["passos"]["relatorio"]["dados"]
            d_rel["pasta_saida"] = str(pasta_saida)

            # 2) Renderiza Typst com Jinja
            contexto_typst = {
                "conjuntos": conjuntos,
                "tabelas": tabelas,
                "scatter_nome": nome_png,
                "elementos": elementos,
                "graficos_elementos": graficos_elementos,
                "pca": pca,
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

            # 3) Compila PDF com Typst
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
                + pca.get("arquivos", [])
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