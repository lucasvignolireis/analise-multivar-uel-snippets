from copy import deepcopy
from pathlib import Path
from shiny import ui, module, render, reactive


@module.ui
def etapa_arquivo_ui():
    return ui.card(
        ui.h4("Passo 1: Escolha um dos arquivos que está na pasta '/dados'"),
    )


# @module.server
# def etapa_arquivo_server(input, output, session, *, wizard_state):
#     BASE_DIR = Path(__file__).resolve().parent.parent  # src/

#     def _listar_arquivos():
#         s = wizard_state()
#         conf = s["passos"]["arquivo"]["conf"]
#         path_rel = conf.get("path", "dados/")
#         extensoes = conf.get("extensoes", ["csv"])

#         pasta = (BASE_DIR / path_rel).resolve()
#         if not pasta.exists():
#             return pasta, []

#         arquivos = []
#         for ext in extensoes:
#             arquivos.extend(pasta.glob(f"*.{ext}"))

#         return pasta, sorted(p.name for p in arquivos)

#     @render.ui
#     def seletor_arquivo_ui():
#         pasta, arquivos = _listar_arquivos()
#         if not arquivos:
#             return ui.p(f"Nenhum arquivo encontrado em {pasta}")
#         return ui.input_select("arquivo_escolhido", "Arquivo:", choices=arquivos)

#     @render.text
#     def status_arquivo():
#         s = wizard_state()
#         path_salvo = s["passos"]["arquivo"]["dados"].get("path_arquivo")
#         if not path_salvo:
#             return "Nenhum arquivo confirmado ainda."
#         return f"Arquivo confirmado: {path_salvo}"

#     @reactive.effect
#     @reactive.event(input.confirmar_arquivo)
#     def _confirmar_arquivo():
#         pasta, arquivos = _listar_arquivos()
#         if not arquivos:
#             return

#         nome = input.arquivo_escolhido()
#         if not nome:
#             return

#         caminho = (pasta / nome).resolve()
#         if not caminho.exists():
#             return

#         s = deepcopy(wizard_state())
#         s["passos"]["arquivo"]["dados"]["path_arquivo"] = str(caminho)
#         s["passos"]["arquivo"]["estado"] = "preenchido"
#         s["passos"]["tabela"]["estado"] = "em_processo"
#         s["etapa_atual"] = "tabela"

#         wizard_state.set(s)