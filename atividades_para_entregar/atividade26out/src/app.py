from shiny import App, ui

app_ui = ui.page_fluid(
    ui.h1("Começando os testes!"),

    ui.p("App tipo 'hello world' para o exercício do Prof. Melquíades."),

    ui.p(ui.tags.small("Lucas Vignoli Reis, 28 set 2026, Londrina"))
)

def server(input, output, session):
    pass

app = App(app_ui, server)