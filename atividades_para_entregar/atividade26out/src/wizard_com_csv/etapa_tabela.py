from copy import deepcopy
import pandas as pd
from shiny import module, ui, render, reactive

LINHA = "__linha__"  # valor especial: X = número da linha


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
        ui.input_action_button("confirmar_tabela", "Confirmar dados"),
    )


@module.server
def etapa_tabela_server(input, output, session, *, estado_wizard):
    LIMITE_LINHAS_EXIBICAO = 10000

    # Só muda quando arquivo/separador mudam. Assim a UI dos seletores
    # não é recriada (e a seleção não é perdida) quando outras partes
    # do estado são alteradas.
    @reactive.calc
    def _fonte():
        dados = estado_wizard()["passos"]["arquivo"]["dados"]
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
        return df.head(LIMITE_LINHAS_EXIBICAO)

    @reactive.calc
    def _colunas_numericas():
        df = _df()
        if df is None:
            return []
        return [str(c) for c in df.select_dtypes(include="number").columns]

    @render.ui
    def seletor_x_ui():
        df = _df()
        if df is None:
            return None
        choices = {LINHA: "(número da linha)"}
        choices.update({str(c): str(c) for c in _colunas_numericas()})
        return ui.input_select("col_x", "Eixo X:", choices=choices, selected=LINHA)

    @render.ui
    def seletor_y_ui():
        cols = _colunas_numericas()
        if not cols:
            return None
        return ui.input_checkbox_group(
            "cols_y", "Colunas Y:", choices=cols, selected=cols[:1]
        )

    @render.text
    def status_tabela():
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
        df = _df()
        if df is None:
            return

        cols_y = list(input.cols_y() or [])
        if not cols_y:
            return

        df_exibicao = _df_exibicao()

        s = deepcopy(estado_wizard())
        d = s["passos"]["tabela"]["dados"]
        d["n_linhas"] = int(df.shape[0])
        d["colunas"] = [str(c) for c in df.columns]
        d["preview"] = df_exibicao.fillna("").to_dict(orient="records")
        d["col_x"] = input.col_x() or LINHA
        d["cols_y"] = cols_y

        s["passos"]["tabela"]["estado"] = "preenchido"
        s["passos"]["relatorio"]["estado"] = "em_processo"
        s["etapa_atual"] = "relatorio"

        estado_wizard.set(s)