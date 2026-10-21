from pathlib import Path
from shiny import module, ui, render

@module.ui
def etapa_relatorio_ui():
    return ui.card(
        ui.h4("Passo 3: Relatório"),
        ui.output_text("status_relatorio"),
        ui.output_image("img_scatter"),
    )

@module.server
def etapa_relatorio_server(input, output, session, *, estado_wizard):
    @render.text
    def status_relatorio():
        d = estado_wizard()["passos"]["relatorio"]["dados"]
        pasta = d.get("pasta_saida")
        arqs = d.get("arquivos", [])
        if not pasta:
            return "Relatório ainda não foi gerado."
        return f"Relatório gerado em: {pasta} | arquivos: {', '.join(arqs)}"

    @render.image
    def img_scatter():
        d = estado_wizard()["passos"]["relatorio"]["dados"]
        p = d.get("scatter_path")
        if not p or not Path(p).exists():
            return None
        return {"src": p, "alt": "Scatter plot gerado"}