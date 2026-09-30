from pathlib import Path
import pandas as pd
from shiny import App, ui, render


# Resolve paths relative to this file
BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / ".." / "dados" / "Xcalib.csv"

app_ui = ui.page_fluid(
    ui.h2("Teste abrindo CSV"),
    ui.p("Vamos abrir um CSV, mostrar na página e gerar um relatório no Typst. Para testar como funciona."),
    ui.p(f"Abrindo o a arquivo: {CSV_PATH}"),
    ui.output_code("status"),
    ui.output_table("tabela"),
)

def server(input, output, session):
    @render.text
    def status():
        if not CSV_PATH.exists():
            return f"Não encontrei o arquivo: \"{CSV_PATH}\""
        return f"Arquivo encontrado: carregando \"{CSV_PATH}\""

    @render.table
    def tabela():
        if not CSV_PATH.exists():
            return pd.DataFrame({"erro": [f"Não conseguiu abrir o arquivo: {CSV_PATH}"]})
        return pd.read_csv(CSV_PATH, sep=",")

app = App(app_ui, server)