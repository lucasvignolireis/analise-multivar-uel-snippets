from copy import deepcopy
from pathlib import Path

from shiny import module, ui, render, reactive


@module.ui
def etapa_arquivo_ui():
    return ui.card(
        ui.h4("Passo 1: Escolha um dos arquivos que está na pasta '/dados'"),
        ui.output_ui("seletor_arquivo_ui"),
        ui.input_select(
            "separador",
            "Separador:",
            choices={
                ",": "Vírgula (,)",
                ";": "Ponto e vírgula (;)",
                "\t": r"Tab (\t)",
                "|": "Pipe (|)",
            },
            selected=",",
        ),
        ui.output_text("status_arquivo"),
        ui.input_action_button("escolher_arquivo", "Usar este arquivo"),
    )

@module.server
def etapa_arquivo_server(input, output, session, *, estado_wizard):
    # Este arquivo está em src/atividade_resolvida/etapa_arquivo.py
    # parent.parent => src/
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    def _listar_arquivos():
        s = estado_wizard()
        conf = s["passos"]["arquivo"]["conf"]

        path_rel = conf.get("path", "dados/")
        extensoes = conf.get("extensoes", ["csv"])

        pasta = (BASE_DIR / path_rel).resolve()
        if not pasta.exists():
            return pasta, []

        arquivos = []
        for ext in extensoes:
            # normaliza "csv" ou ".csv"
            ext_limpa = ext[1:] if ext.startswith(".") else ext
            arquivos.extend(pasta.glob(f"*.{ext_limpa}"))

        nomes = sorted([p.name for p in arquivos])
        return pasta, nomes
    
    @render.ui
    def seletor_arquivo_ui():
        pasta, arquivos = _listar_arquivos()

        if not arquivos:
            return ui.p(f"A pasta '{pasta}' não tem arquivos do tipo especificado.")

        return ui.input_select(
            "arquivo_escolhido",
            "Arquivo:",
            choices=arquivos,
            selected=arquivos[0],
        )

    @render.text
    def status_arquivo():
        s = estado_wizard()
        path_arquivo_salvo = s["passos"]["arquivo"]["dados"].get("path_arquivo")

        if not path_arquivo_salvo:
            return "Nenhum arquivo escolhido ainda."
        return f"Arquivo escolhido: {path_arquivo_salvo}"

    @reactive.effect
    @reactive.event(input.escolher_arquivo)
    def _escolher_arquivo():
        pasta, arquivos = _listar_arquivos()
        if not arquivos:
            return

        nome = input.arquivo_escolhido()
        if not nome:
            return

        separador = input.separador()
        if separador is None:
            separador = ","

        caminho = (pasta / nome).resolve()
        if not caminho.exists():
            return

        s = deepcopy(estado_wizard())
        s["passos"]["arquivo"]["dados"]["path_arquivo"] = str(caminho)
        s["passos"]["arquivo"]["dados"]["separador"] = separador
        s["passos"]["arquivo"]["estado"] = "preenchido"

        # libera próximo passo
        s["passos"]["tabela"]["estado"] = "em_processo"
        s["etapa_atual"] = "tabela"

        estado_wizard.set(s)