from copy import deepcopy
from pathlib import Path

from shiny import module, ui, render, reactive


@module.ui
def etapa_carregamento_ui():
    return ui.card(
        ui.h4("Passo 1: Carregamento dos dados (pasta '/dados')"),

        ui.h5("Conjunto de validação (X)"),
        ui.p("CSV com as amostras medidas por dissolução eletrolítica e ICP-AES."),
        ui.output_ui("seletor_xvalid_ui"),
        ui.input_select(
            "separador_xvalid",
            "Separador:",
            choices={
                ",": "Vírgula (,)",
                ";": "Ponto e vírgula (;)",
                "\t": r"Tab (\t)",
                "|": "Pipe (|)",
            },
            selected=",",
        ),

        ui.hr(),

        ui.h5("Conjunto de calibração (X)"),
        ui.p("CSV com as 44 amostras simuladas (V, Cr, Fe, Mo, W)."),
        ui.output_ui("seletor_xcalib_ui"),
        ui.input_select(
            "separador_xcalib",
            "Separador:",
            choices={
                ",": "Vírgula (,)",
                ";": "Ponto e vírgula (;)",
                "\t": r"Tab (\t)",
                "|": "Pipe (|)",
            },
            selected=",",
        ),

        ui.output_text("status_carregamento"),
        ui.input_action_button("confirmar_carregamento", "Usar estes arquivos"),
    )


@module.server
def etapa_carregamento_server(input, output, session, *, estado_wizard):
    # Este arquivo está em src/atividade_resolvida/etapa_carregamento.py
    # parent.parent.parent => .../atividade26out
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    def _listar_arquivos():
        s = estado_wizard()
        conf = s["passos"]["carregamento"]["conf"]

        path_rel = conf.get("path", "dados/")
        extensoes = conf.get("extensoes", ["csv", "tsv"])

        pasta = (BASE_DIR / path_rel).resolve()
        if not pasta.exists():
            return pasta, []

        arquivos = []
        for ext in extensoes:
            ext_limpa = ext[1:] if ext.startswith(".") else ext
            arquivos.extend(pasta.glob(f"*.{ext_limpa}"))

        nomes = sorted([p.name for p in arquivos])
        return pasta, nomes

    @render.ui
    def seletor_xvalid_ui():
        pasta, arquivos = _listar_arquivos()

        if not arquivos:
            return ui.p(f"A pasta '{pasta}' não tem arquivos do tipo especificado.")

        # tenta pré-selecionar Xvalid, se existir
        selected = next((n for n in arquivos if "xvalid" in n.lower()), arquivos[0])

        return ui.input_select(
            "xvalid_escolhido",
            "Arquivo:",
            choices=arquivos,
            selected=selected,
        )

    @render.ui
    def seletor_xcalib_ui():
        pasta, arquivos = _listar_arquivos()

        if not arquivos:
            return ui.p(f"A pasta '{pasta}' não tem arquivos do tipo especificado.")

        # tenta pré-selecionar Xcalib, se existir
        selected = next((n for n in arquivos if "xcalib" in n.lower()), arquivos[0])

        return ui.input_select(
            "xcalib_escolhido",
            "Arquivo:",
            choices=arquivos,
            selected=selected,
        )

    @render.text
    def status_carregamento():
        s = estado_wizard()
        dados = s["passos"]["carregamento"]["dados"]

        xvalid = dados.get("xvalid_path")
        xcalib = dados.get("xcalib_path")

        if not xvalid or not xcalib:
            return "Nenhum conjunto confirmado ainda."

        return f"Xvalid: {xvalid} | Xcalib: {xcalib}"

    @reactive.effect
    @reactive.event(input.confirmar_carregamento)
    def _confirmar_carregamento():
        pasta, arquivos = _listar_arquivos()
        if not arquivos:
            return

        nome_xvalid = input.xvalid_escolhido()
        nome_xcalib = input.xcalib_escolhido()

        if not nome_xvalid or not nome_xcalib:
            return

        sep_xvalid = input.separador_xvalid() or ","
        sep_xcalib = input.separador_xcalib() or ","

        caminho_xvalid = (pasta / nome_xvalid).resolve()
        caminho_xcalib = (pasta / nome_xcalib).resolve()

        if not caminho_xvalid.exists() or not caminho_xcalib.exists():
            return

        s = deepcopy(estado_wizard())

        d = s["passos"]["carregamento"]["dados"]
        d["xvalid_path"] = caminho_xvalid.relative_to(pasta).as_posix()
        d["xvalid_sep"] = sep_xvalid
        d["xcalib_path"] = caminho_xcalib.relative_to(pasta).as_posix()
        d["xcalib_sep"] = sep_xcalib

        s["passos"]["carregamento"]["estado"] = "preenchido"

        # libera próximo passo
        s["passos"]["tabela"]["estado"] = "em_processo"
        s["etapa_atual"] = "tabela"

        estado_wizard.set(s)