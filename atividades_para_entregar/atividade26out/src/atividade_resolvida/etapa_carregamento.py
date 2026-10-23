from copy import deepcopy
from pathlib import Path

from shiny import module, ui, render, reactive

SEPARADORES = {
    ",": "Vírgula (,)",
    ";": "Ponto e vírgula (;)",
    "\t": r"Tab (\t)",
    "|": "Pipe (|)",
}


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
            choices=SEPARADORES,
            selected=",",
        ),

        ui.hr(),

        ui.h5("Conjunto de calibração (X)"),
        ui.p("CSV com as 44 amostras simuladas (V, Cr, Fe, Mo, W)."),
        ui.output_ui("seletor_xcalib_ui"),
        ui.input_select(
            "separador_xcalib",
            "Separador:",
            choices=SEPARADORES,
            selected=",",
        ),

        ui.hr(),

        ui.h5("Conjunto de validação (Y)"),
        ui.p("CSV com as concentrações de referência das amostras de validação."),
        ui.output_ui("seletor_yvalid_ui"),
        ui.input_select(
            "separador_yvalid",
            "Separador:",
            choices=SEPARADORES,
            selected=",",
        ),

        ui.hr(),

        ui.h5("Conjunto de calibração (Y)"),
        ui.p("CSV com as concentrações das 44 amostras simuladas."),
        ui.output_ui("seletor_ycalib_ui"),
        ui.input_select(
            "separador_ycalib",
            "Separador:",
            choices=SEPARADORES,
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

    def _seletor(input_id: str, dica: str):
        pasta, arquivos = _listar_arquivos()

        if not arquivos:
            return ui.p(f"A pasta '{pasta}' não tem arquivos do tipo especificado.")

        # tenta pré-selecionar pelo nome, se existir
        selected = next((n for n in arquivos if dica in n.lower()), arquivos[0])

        return ui.input_select(
            input_id,
            "Arquivo:",
            choices=arquivos,
            selected=selected,
        )

    @render.ui
    def seletor_xvalid_ui():
        return _seletor("xvalid_escolhido", "xvalid")

    @render.ui
    def seletor_xcalib_ui():
        return _seletor("xcalib_escolhido", "xcalib")

    @render.ui
    def seletor_yvalid_ui():
        return _seletor("yvalid_escolhido", "yvalid")

    @render.ui
    def seletor_ycalib_ui():
        return _seletor("ycalib_escolhido", "ycalib")

    @render.text
    def status_carregamento():
        s = estado_wizard()
        dados = s["passos"]["carregamento"]["dados"]

        xvalid = dados.get("xvalid_path")
        xcalib = dados.get("xcalib_path")
        yvalid = dados.get("yvalid_path")
        ycalib = dados.get("ycalib_path")

        if not (xvalid and xcalib and yvalid and ycalib):
            return "Nenhum conjunto confirmado ainda."

        return (
            f"Xvalid: {xvalid} | Xcalib: {xcalib} | "
            f"Yvalid: {yvalid} | Ycalib: {ycalib}"
        )

    @reactive.effect
    @reactive.event(input.confirmar_carregamento)
    def _confirmar_carregamento():
        pasta, arquivos = _listar_arquivos()
        if not arquivos:
            return

        nome_xvalid = input.xvalid_escolhido()
        nome_xcalib = input.xcalib_escolhido()
        nome_yvalid = input.yvalid_escolhido()
        nome_ycalib = input.ycalib_escolhido()

        if not (nome_xvalid and nome_xcalib and nome_yvalid and nome_ycalib):
            return

        sep_xvalid = input.separador_xvalid() or ","
        sep_xcalib = input.separador_xcalib() or ","
        sep_yvalid = input.separador_yvalid() or ","
        sep_ycalib = input.separador_ycalib() or ","

        caminho_xvalid = (pasta / nome_xvalid).resolve()
        caminho_xcalib = (pasta / nome_xcalib).resolve()
        caminho_yvalid = (pasta / nome_yvalid).resolve()
        caminho_ycalib = (pasta / nome_ycalib).resolve()

        if not all(
            c.exists()
            for c in (caminho_xvalid, caminho_xcalib, caminho_yvalid, caminho_ycalib)
        ):
            return

        s = deepcopy(estado_wizard())

        d = s["passos"]["carregamento"]["dados"]
        d["xvalid_path"] = caminho_xvalid.relative_to(pasta).as_posix()
        d["xvalid_sep"] = sep_xvalid
        d["xcalib_path"] = caminho_xcalib.relative_to(pasta).as_posix()
        d["xcalib_sep"] = sep_xcalib
        d["yvalid_path"] = caminho_yvalid.relative_to(pasta).as_posix()
        d["yvalid_sep"] = sep_yvalid
        d["ycalib_path"] = caminho_ycalib.relative_to(pasta).as_posix()
        d["ycalib_sep"] = sep_ycalib

        s["passos"]["carregamento"]["estado"] = "preenchido"

        # libera próximo passo
        s["passos"]["tabela"]["estado"] = "em_processo"
        s["etapa_atual"] = "tabela"

        estado_wizard.set(s)