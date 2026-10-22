from pathlib import Path
from shiny import module, ui, render

@module.ui
def etapa_relatorio_ui():
    return ui.card(
        ui.h4("Passo 3: Relatório"),
        ui.output_text("status_relatorio"),
        ui.output_ui("pdf_link_ui"),
        ui.hr(),
        ui.output_ui("pdf_embed_ui"),
    )

@module.server
def etapa_relatorio_server(input, output, session, *, estado_wizard):
    @render.text
    def status_relatorio():
        d = estado_wizard()["passos"]["relatorio"]["dados"]
        if not d.get("pdf_path"):
            return "Relatório ainda não foi gerado."
        return "Relatório pronto."

    def _pdf_url():
        d = estado_wizard()["passos"]["relatorio"]["dados"]
        pdf_path = d.get("pdf_path")
        if not pdf_path:
            return None

        p = Path(pdf_path).resolve()
        outputs_dir = (Path(__file__).resolve().parent.parent.parent / "outputs").resolve()

        try:
            rel = p.relative_to(outputs_dir)  # ex: 2026-10-22-10-30/relatorio.pdf
        except ValueError:
            return None  # pdf fora de outputs -> não servir

        return "/outputs/" + rel.as_posix()

    @render.ui
    def pdf_link_ui():
        url = _pdf_url()
        if not url:
            return ui.p("PDF indisponível.")
        return ui.a("⬇️ Baixar relatório PDF", href=url, target="_blank")

    @render.ui
    def pdf_embed_ui():
        url = _pdf_url()
        if not url:
            return ui.p("Nada para exibir.")
        return ui.tags.iframe(
            src=url,
            width="100%",
            height="900px",
            style="border:1px solid #ddd;border-radius:8px;"
        )