import sys

from shiny import App, ui

versao_do_python = sys.version.splitlines()[0]

app_ui = ui.page_fluid(
    ui.h1("Começando os testes!"),

    ui.p("App tipo 'hello world' para o exercício do Prof. Melquíades."),

    ui.p(ui.tags.small("Lucas Vignoli Reis, 28 set 2026, Londrina")),

    ui.hr(),

    ui.tags.small(f"Ambiente python configurado por devenv.nix. Versão do Python: {versao_do_python}"),
)

def server(input, output, session):
    pass

app = App(app_ui, server)