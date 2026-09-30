from pathlib import Path
import pandas as pd
from shiny import App, ui, render

app_ui = ui.page_fluid(
    ui.h2("Teste: abrir CSV e gerar relatório"),
)

app = App(app_ui, None)