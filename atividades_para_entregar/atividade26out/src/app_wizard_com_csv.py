import json
from pathlib import Path
import pandas as pd
from shiny import App, ui, reactive, render

from wizard_com_csv.estado_wizard import (
    estado_inicial_wizard
)
from wizard_com_csv.etapa_arquivo import (
    etapa_arquivo_ui #, etapa_arquivo_server
)

app_ui = ui.page_fluid(
    ui.h2("Teste: abrir CSV e gerar relatório"),
    ui.output_ui("abas_wizard"),
    ui.output_code("estado_wizard_json"),
)

def server(input, output, session):
    estado_wizard = reactive.value(estado_inicial_wizard())

    @render.ui
    def abas_wizard():
        s = estado_wizard()

        t1 = s["passos"]["arquivo"]["titulo"]
        t2 = s["passos"]["tabela"]["titulo"]
        t3 = s["passos"]["relatorio"]["titulo"]

        atual = s["etapa_atual"]
        selected = {
            "arquivo": t1,
            "tabela": t2,
            "relatorio": t3,
        }[atual]

        return ui.navset_tab(
            ui.nav_panel(t1, ui.p("Lorem Ipsum da etapa de arquivo")),
            ui.nav_panel(t2, ui.p("Passo 2 virá em seguida.")),
            ui.nav_panel(t3, ui.p("Passo 3 virá em seguida.")),
            id="wizard_tabs",
            selected=selected,
       )

    @render.code
    def estado_wizard_json():
        return json.dumps(estado_wizard(), indent=2, ensure_ascii=False)


app = App(app_ui, server)



# def titulo_aba(numero: int, titulo: str, estado: str) -> str:
#     mapa = {
#         "vazio": "greyed out",
#         "em_processo": "editing",
#         "preenchido": "done",
#     }
#     return f"{numero}. {titulo} ({mapa.get(estado, estado)})"


# app_ui = ui.page_fluid(
#     ui.h2("Teste abrindo CSV"),
#     ui.output_ui("abas_wizard"),
# )


# def server(input, output, session):
#     wizard_state = reactive.value(estado_inicial_wizard())

#     @ui.render.ui
#     def abas_wizard():
#         s = wizard_state()

#         t1 = titulo_aba(1, s["passos"]["arquivo"]["titulo"], s["passos"]["arquivo"]["estado"])
#         t2 = titulo_aba(2, s["passos"]["tabela"]["titulo"], s["passos"]["tabela"]["estado"])
#         t3 = titulo_aba(3, s["passos"]["relatorio"]["titulo"], s["passos"]["relatorio"]["estado"])

#         atual = s["etapa_atual"]
#         selected = {
#             "arquivo": t1,
#             "tabela": t2,
#             "relatorio": t3,
#         }[atual]

#         return ui.navset_tab(
#             ui.nav_panel(t1, etapa_arquivo_ui("arquivo_step")),
#             ui.nav_panel(t2, ui.p("Passo 2 virá em seguida.")),
#             ui.nav_panel(t3, ui.p("Passo 3 virá em seguida.")),
#             id="wizard_tabs",
#             selected=selected,
#         )

#     etapa_arquivo_server("arquivo_step", wizard_state=wizard_state)


# app = App(app_ui, server)