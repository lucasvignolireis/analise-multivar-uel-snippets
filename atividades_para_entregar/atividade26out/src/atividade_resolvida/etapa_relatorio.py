from pathlib import Path
from shiny import module, ui, render

@module.ui
def etapa_relatorio_ui():
    return ui.card(
        ui.h4("Passo 3: Relatório"),
        ui.output_text("status_relatorio"),
        ui.output_ui("pdf_links_ui"),
        ui.hr(),
        ui.output_ui("pdf_embeds_ui"),
    )

@module.server
def etapa_relatorio_server(input, output, session, *, estado_wizard):
    @render.text
    def status_relatorio():
        d = estado_wizard()["passos"]["relatorio"]["dados"]
        if not d.get("pdf_final_path") and not d.get("pdf_path"):
            return "Relatórios ainda não foram gerados."
        if d.get("pdf_final_path") and d.get("pdf_path"):
            return "Relatórios prontos (final e bruto)."
        if d.get("pdf_final_path"):
            return "Relatório final pronto."
        return "Relatório bruto pronto."

    def _pdf_url_from_path(pdf_path: str | None):
        if not pdf_path:
            return None

        p = Path(pdf_path).resolve()
        outputs_dir = (Path(__file__).resolve().parent.parent.parent / "outputs").resolve()

        try:
            rel = p.relative_to(outputs_dir)  # ex: 2026-10-22-10-30/relatorio_final.pdf
        except ValueError:
            return None  # pdf fora de outputs -> não servir

        return "/outputs/" + rel.as_posix()

    @render.ui
    def pdf_links_ui():
        d = estado_wizard()["passos"]["relatorio"]["dados"]

        url_final = _pdf_url_from_path(d.get("pdf_final_path"))
        url_bruto = _pdf_url_from_path(d.get("pdf_path"))

        itens = []

        if url_final:
            itens.append(
                ui.tags.li(
                    ui.a("⬇️ Baixar relatório FINAL (PDF)", href=url_final, target="_blank")
                )
            )

        if url_bruto:
            itens.append(
                ui.tags.li(
                    ui.a("⬇️ Baixar relatório BRUTO (PDF)", href=url_bruto, target="_blank")
                )
            )

        if not itens:
            return ui.p("PDFs indisponíveis.")

        return ui.TagList(
            ui.h5("Downloads"),
            ui.tags.ul(*itens),
        )

    @render.ui
    def pdf_embeds_ui():
        d = estado_wizard()["passos"]["relatorio"]["dados"]

        url_final = _pdf_url_from_path(d.get("pdf_final_path"))
        url_bruto = _pdf_url_from_path(d.get("pdf_path"))

        blocos = []

        if url_final:
            blocos.append(ui.h5("Preview — Relatório FINAL"))
            blocos.append(
                ui.tags.iframe(
                    src=url_final,
                    width="100%",
                    height="900px",
                    style="border:1px solid #ddd;border-radius:8px;margin-bottom:16px;",
                )
            )

        if url_bruto:
            blocos.append(ui.h5("Preview — Relatório BRUTO"))
            blocos.append(
                ui.tags.iframe(
                    src=url_bruto,
                    width="100%",
                    height="900px",
                    style="border:1px solid #ddd;border-radius:8px;",
                )
            )

        if not blocos:
            return ui.p("Nada para exibir.")

        return ui.TagList(*blocos)