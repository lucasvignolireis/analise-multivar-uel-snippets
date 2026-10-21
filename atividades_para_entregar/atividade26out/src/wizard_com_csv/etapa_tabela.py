from copy import deepcopy
import pandas as pd
from shiny import module, ui, render, reactive


@module.ui
def etapa_tabela_ui():
    return ui.card(
        ui.h4("Passo 2: Conferir os dados"),
        ui.output_text("status_tabela"),
        ui.output_table("preview_tabela"),
        ui.input_action_button("confirmar_tabela", "Confirmar dados"),
    )


@module.server
def etapa_tabela_server(input, output, session, *, estado_wizard):
    LIMITE_LINHAS_EXIBICAO = 10000

    @reactive.calc
    def _df():
        s = estado_wizard()
        path_arquivo = s["passos"]["arquivo"]["dados"].get("path_arquivo")
        separador = s["passos"]["arquivo"]["dados"].get("separador", ",")

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

    @reactive.effect
    @reactive.event(input.confirmar_tabela)
    def _confirmar_tabela():
        df = _df()
        if df is None:
            return

        df_exibicao = _df_exibicao()

        s = deepcopy(estado_wizard())
        s["passos"]["tabela"]["dados"]["n_linhas"] = int(df.shape[0])
        s["passos"]["tabela"]["dados"]["colunas"] = [str(c) for c in df.columns]
        s["passos"]["tabela"]["dados"]["preview"] = (
            df_exibicao.fillna("").to_dict(orient="records")
        )

        s["passos"]["tabela"]["estado"] = "preenchido"
        s["passos"]["relatorio"]["estado"] = "em_processo"
        s["etapa_atual"] = "relatorio"

        estado_wizard.set(s)