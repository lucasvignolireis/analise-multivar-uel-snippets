import json
from pathlib import Path
import pandas as pd
from shiny import App, ui, reactive, render

from wizard_com_csv.estado_wizard import (
    estado_inicial_wizard
)
from wizard_com_csv.etapa_arquivo import (
    etapa_arquivo_ui, etapa_arquivo_server
)
from wizard_com_csv.etapa_tabela import (
    etapa_tabela_ui, etapa_tabela_server
)
from wizard_com_csv.etapa_relatorio import (
    etapa_relatorio_server, etapa_relatorio_ui
)

app_ui = ui.page_fluid(
    ui.h2("Teste: abrir CSV e gerar relatório"),
    ui.tags.style("""
      .table td, .table th {
        text-align: left !important;
      }
    """),
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
            ui.nav_panel(t1, etapa_arquivo_ui("etapa_arquivo")),
            ui.nav_panel(t2, etapa_tabela_ui("etapa_tabela")),
            ui.nav_panel(t3, etapa_relatorio_ui("etapa_relatorio")),
            id="wizard_tabs",
            selected=selected,
       )

    @render.code
    def estado_wizard_json():
        return json.dumps(estado_wizard(), indent=2, ensure_ascii=False)

    etapa_arquivo_server("etapa_arquivo", estado_wizard=estado_wizard)
    etapa_tabela_server("etapa_tabela", estado_wizard=estado_wizard)
    etapa_relatorio_server("etapa_relatorio", estado_wizard=estado_wizard)


app = App(app_ui, server)

