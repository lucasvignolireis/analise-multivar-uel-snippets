from copy import deepcopy
from datetime import datetime
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from shiny import module, ui, render, reactive

from atividade_resolvida.relatorio_typst import renderizar_relatorio_typst

LINHA = "__linha__"


@module.ui
def etapa_tabela_ui():
    return ui.card(
        ui.h4("Passo 2: Conferir os dados"),
        ui.output_text("status_tabela"),
        ui.layout_columns(
            ui.output_ui("seletor_x_ui"),
            ui.output_ui("seletor_y_ui"),
        ),
        ui.output_table("preview_tabela"),
        ui.output_text("aviso_confirmar"),
        ui.input_action_button("confirmar_tabela", "Confirmar dados e gerar relatório"),
    )


@module.server
def etapa_tabela_server(input, output, session, *, estado_wizard):
    LIMITE_LINHAS_EXIBICAO = 10000
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # /
    PASTA_OUTPUTS = BASE_DIR / "outputs"

    gerando = reactive.value(False)
    erro_geracao = reactive.value("")

    @reactive.calc
    def _fonte():
        dados = estado_wizard()["passos"]["carregamento"]["dados"]
        return dados.get("path_arquivo"), dados.get("separador", ",")

    @reactive.calc
    def _df():
        path_arquivo, separador = _fonte()
        if not path_arquivo:
            return None
        try:
            return pd.read_csv(path_arquivo, sep=separador)
        except Exception:
            return None

    @reactive.calc
    def _df_exibicao():
        df = _df()
        if df is None:
            return None
        if len(df) > LIMITE_LINHAS_EXIBICAO:
            return df.head(LIMITE_LINHAS_EXIBICAO)
        return df

    @reactive.calc
    def _colunas_numericas():
        df = _df()
        if df is None:
            return []
        return [str(c) for c in df.select_dtypes(include="number").columns]

    def _fazer_figura(df, col_x, cols_y):
        if col_x == LINHA:
            x = df.index
            xlabel = "linha"
        else:
            x = df[col_x]
            xlabel = col_x

        fig, ax = plt.subplots(figsize=(8, 5))
        for col in cols_y:
            ax.scatter(x, df[col], alpha=0.7, label=col)

        ax.set_xlabel(xlabel)
        ax.set_ylabel("valor" if len(cols_y) > 1 else cols_y[0])
        ax.set_title("Scatter plot")
        ax.grid(True, alpha=0.3)
        if len(cols_y) > 1:
            ax.legend()
        fig.tight_layout()
        return fig

    @render.ui
    def seletor_x_ui():
        df = _df()
        if df is None:
            return None

        choices = {LINHA: "(número da linha)"}
        choices.update({c: c for c in _colunas_numericas()})

        return ui.input_select(
            "col_x",
            "Eixo X:",
            choices=choices,
            selected=LINHA,
        )

    @render.ui
    def seletor_y_ui():
        cols = _colunas_numericas()
        if not cols:
            return None
        return ui.input_checkbox_group(
            "cols_y",
            "Colunas Y:",
            choices=cols,
            selected=cols[:1],
        )

    @render.text
    def status_tabela():
        if gerando():
            return "Gerando relatório... aguarde."
        if erro_geracao():
            return f"Erro ao gerar relatório: {erro_geracao()}"

        df = _df()
        if df is None:
            return "Selecione e confirme um arquivo na etapa anterior."

        n_linhas, n_colunas = df.shape
        if n_linhas > LIMITE_LINHAS_EXIBICAO:
            return (
                f"Arquivo carregado: {n_linhas} linhas, {n_colunas} colunas. "
                f"Exibindo somente as primeiras {LIMITE_LINHAS_EXIBICAO} linhas."
            )

        return (
            f"Arquivo carregado com sucesso: {n_linhas} linhas, {n_colunas} colunas. "
            "Exibindo todas as linhas."
        )

    @render.table
    def preview_tabela():
        df_exibicao = _df_exibicao()
        if df_exibicao is None:
            return pd.DataFrame()
        return df_exibicao

    @render.text
    def aviso_confirmar():
        if _df() is not None and not input.cols_y():
            return "Selecione ao menos uma coluna Y para continuar."
        return ""

    @reactive.effect
    @reactive.event(input.confirmar_tabela)
    def _confirmar_tabela():
        erro_geracao.set("")

        df = _df()
        if df is None:
            return

        cols_y = list(input.cols_y() or [])
        if not cols_y:
            return

        col_x = input.col_x() or LINHA
        path_arquivo, separador = _fonte()

        gerando.set(True)
        try:
            nome_pasta = datetime.now().strftime("%Y-%m-%d-%H-%M")
            pasta_saida = PASTA_OUTPUTS / nome_pasta
            pasta_saida.mkdir(parents=True, exist_ok=True)

            # 1) Gera scatter
            nome_png = "scatter.png"
            caminho_png = pasta_saida / nome_png

            fig = _fazer_figura(df, col_x, cols_y)
            fig.savefig(caminho_png, dpi=150)
            plt.close(fig)

            # 2) Atualiza estado com dados da tabela + relatório
            s = deepcopy(estado_wizard())

            d_tab = s["passos"]["tabela"]["dados"]
            d_tab["n_linhas"] = int(df.shape[0])
            d_tab["colunas"] = [str(c) for c in df.columns]
            d_tab["preview"] = _df_exibicao().fillna("").to_dict(orient="records")
            d_tab["col_x"] = col_x
            d_tab["cols_y"] = cols_y

            d_rel = s["passos"]["relatorio"]["dados"]
            d_rel["pasta_saida"] = str(pasta_saida)
            d_rel["scatter_nome"] = nome_png
            d_rel["scatter_path"] = str(caminho_png)

            # 3) Renderiza Typst com Jinja
            contexto_typst = {
                "arquivo_path": str(path_arquivo),
                "separador": separador,
                "n_linhas": int(df.shape[0]),
                "n_colunas": int(df.shape[1]),
                "col_x_label": "linha" if col_x == LINHA else col_x,
                "cols_y": cols_y,
                "scatter_nome": nome_png,  # relativo ao .typ
            }

            print("[relatorio] contexto typst:", contexto_typst, flush=True)

            nome_typ = "relatorio.typ"
            nome_pdf = "relatorio.pdf"
            caminho_typ = pasta_saida / nome_typ
            caminho_pdf = pasta_saida / nome_pdf

            print("[relatorio] arquivos a de relatorios a serem gerados:", caminho_typ,", ", caminho_pdf, flush=True)

            try:
                conteudo_typ = renderizar_relatorio_typst(
                    contexto_typst,
                    template_name="template_relatorio.typ.j2",
                )
            except Exception as e:
                import traceback
                traceback.print_exc()  # <- imprime no terminal
                erro_geracao.set(f"{type(e).__name__}: {e}")
            finally:
                gerando.set(False)

            print("[relatorio] conteudo do .typ:", conteudo_typ, flush=True)
            
            caminho_typ.write_text(conteudo_typ, encoding="utf-8")

            # 4) Compila PDF com Typst
            subprocess.run(
                ["typst", "compile", str(caminho_typ), str(caminho_pdf)],
                check=True,
                cwd=str(pasta_saida),
            )

            d_rel["typ_path"] = str(caminho_typ)
            d_rel["pdf_path"] = str(caminho_pdf)
            d_rel["arquivos"] = [nome_png, nome_typ, nome_pdf]

            s["passos"]["tabela"]["estado"] = "preenchido"
            s["passos"]["relatorio"]["estado"] = "preenchido"
            s["etapa_atual"] = "relatorio"

            estado_wizard.set(s)

        except Exception as e:
            erro_geracao.set(str(e))
        finally:
            gerando.set(False)