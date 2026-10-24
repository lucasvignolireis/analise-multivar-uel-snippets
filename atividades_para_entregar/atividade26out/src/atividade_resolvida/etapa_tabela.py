from copy import deepcopy
from datetime import datetime
from pathlib import Path
import subprocess

import pandas as pd
from shiny import module, ui, render, reactive

from atividade_resolvida.relatorio_typst import renderizar_relatorio_typst
from atividade_resolvida.grafico_visualizacao_inicial_dados import (
    gerar_scatter_elementos,
    gerar_scatter_por_elemento,
)

LIMITE_LINHAS_EXIBICAO = 1000

CONJUNTOS = {
    "xvalid": "Conjunto de validação (X)",
    "xcalib": "Conjunto de calibração (X)",
    "yvalid": "Conjunto de validação (Y)",
    "ycalib": "Conjunto de calibração (Y)",
}

CSS_TABELAS = """
.tabela-scroll {
  max-height: 400px;
  overflow: auto;                 /* rola só aqui dentro */
  background: #f3f4f6;            /* cinza bem claro */
  border: 1px solid #d1d5db;
  border-radius: 8px;
  scrollbar-gutter: stable;       /* reserva espaço, a barra não "pula" */
  scrollbar-width: auto;          /* Firefox: barra normal, não fina */
  scrollbar-color: #6b7280 #e5e7eb;
}

/* Chrome/Edge/Safari: barra mais grossa e visível */
.tabela-scroll::-webkit-scrollbar { width: 14px; height: 14px; }
.tabela-scroll::-webkit-scrollbar-track { background: #e5e7eb; }
.tabela-scroll::-webkit-scrollbar-thumb {
  background: #6b7280;
  border-radius: 8px;
  border: 3px solid #e5e7eb;
}
.tabela-scroll::-webkit-scrollbar-thumb:hover { background: #4b5563; }

.tabela-scroll table {
  --bs-table-bg: transparent;     /* deixa o cinza do container aparecer */
  border-collapse: separate;      /* necessário p/ borda do header sticky */
  border-spacing: 0;
  margin-bottom: 0;
  width: 100%;
  font-size: 0.8rem;              /* fonte menor */
}

/* células mais compactas */
.tabela-scroll th,
.tabela-scroll td {
  padding: 0.25rem 0.5rem;
}

/* cabeçalho fixo: só o tbody rola */
.tabela-scroll thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #e5e7eb;
  border-bottom: 2px solid #9ca3af;
}
"""


@module.ui
def etapa_tabela_ui():
    blocos = []
    for chave, titulo in CONJUNTOS.items():
        blocos.append(ui.h5(titulo))
        blocos.append(ui.output_text(f"status_{chave}"))
        blocos.append(
            ui.div(ui.output_table(f"tabela_{chave}"), class_="tabela-scroll")
        )
        blocos.append(ui.hr())

    return ui.card(
        ui.tags.style(CSS_TABELAS),
        ui.h4("Passo 2: Conferir os dados"),
        ui.output_text("status_geral"),
        *blocos,
        ui.input_action_button("confirmar_tabela", "Confirmar dados e gerar relatório"),
    )


@module.server
def etapa_tabela_server(input, output, session, *, estado_wizard):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # .../atividade26out
    PASTA_OUTPUTS = BASE_DIR / "outputs"

    gerando = reactive.value(False)
    erro_geracao = reactive.value("")

    def _fonte(chave):
        """Devolve (path relativo a dados/, separador, path absoluto) do conjunto."""
        s = estado_wizard()["passos"]["carregamento"]
        d = s["dados"]
        rel = d.get(f"{chave}_path")
        sep = d.get(f"{chave}_sep", ",")
        if not rel:
            return None, sep, None
        pasta = (BASE_DIR / s["conf"].get("path", "dados/")).resolve()
        return rel, sep, (pasta / rel).resolve()

    def _ler(chave):
        _, sep, caminho = _fonte(chave)
        if caminho is None:
            return None
        try:
            return pd.read_csv(caminho, sep=sep)
        except Exception:
            return None

    @reactive.calc
    def _df_xvalid():
        return _ler("xvalid")

    @reactive.calc
    def _df_xcalib():
        return _ler("xcalib")

    @reactive.calc
    def _df_yvalid():
        return _ler("yvalid")

    @reactive.calc
    def _df_ycalib():
        return _ler("ycalib")

    DFS = {
        "xvalid": _df_xvalid,
        "xcalib": _df_xcalib,
        "yvalid": _df_yvalid,
        "ycalib": _df_ycalib,
    }

    def _status(df):
        if df is None:
            return "Não carregado. Confirme os arquivos na etapa anterior."
        n_linhas, n_colunas = df.shape
        if n_linhas > LIMITE_LINHAS_EXIBICAO:
            return (
                f"{n_linhas} linhas, {n_colunas} colunas. "
                f"Exibindo somente as primeiras {LIMITE_LINHAS_EXIBICAO} linhas."
            )
        return f"{n_linhas} linhas, {n_colunas} colunas. Exibindo todas as linhas."

    def _exibicao(df):
        if df is None:
            return pd.DataFrame()
        return df.head(LIMITE_LINHAS_EXIBICAO)

    # --- status por conjunto ---
    @render.text
    def status_xvalid():
        return _status(_df_xvalid())

    @render.text
    def status_xcalib():
        return _status(_df_xcalib())

    @render.text
    def status_yvalid():
        return _status(_df_yvalid())

    @render.text
    def status_ycalib():
        return _status(_df_ycalib())

    # --- tabelas ---
    @render.table
    def tabela_xvalid():
        return _exibicao(_df_xvalid())

    @render.table
    def tabela_xcalib():
        return _exibicao(_df_xcalib())

    @render.table
    def tabela_yvalid():
        return _exibicao(_df_yvalid())

    @render.table
    def tabela_ycalib():
        return _exibicao(_df_ycalib())

    @render.text
    def status_geral():
        if gerando():
            return "Gerando relatório... aguarde."
        if erro_geracao():
            return f"Erro ao gerar relatório: {erro_geracao()}"
        if any(f() is None for f in DFS.values()):
            return "Selecione e confirme os arquivos na etapa anterior."
        return "Os quatro conjuntos foram carregados."

    @reactive.effect
    @reactive.event(input.confirmar_tabela)
    def _confirmar_tabela():
        erro_geracao.set("")

        dfs = {chave: f() for chave, f in DFS.items()}
        if any(df is None for df in dfs.values()):
            erro_geracao.set("Algum conjunto não pôde ser lido.")
            return

        gerando.set(True)
        try:
            nome_pasta = datetime.now().strftime("%Y-%m-%d-%H-%M")
            pasta_saida = PASTA_OUTPUTS / nome_pasta
            pasta_saida.mkdir(parents=True, exist_ok=True)

            # 0) Scatter plot (X vs Y por elemento químico)
            nome_png = "grafico_visualizacao_inicial_dados.png"
            elementos = gerar_scatter_elementos(
                dfs["xcalib"], dfs["ycalib"],
                dfs["xvalid"], dfs["yvalid"],
                pasta_saida / nome_png,
            )

            # 0b) Um scatter por elemento
            graficos_elementos = gerar_scatter_por_elemento(
                dfs["xcalib"], dfs["ycalib"],
                dfs["xvalid"], dfs["yvalid"],
                elementos,
                pasta_saida,
            )

            # 1) Resumo dos conjuntos (estado + contexto do relatório)
            conjuntos = []
            for chave, titulo in CONJUNTOS.items():
                rel, sep, _ = _fonte(chave)
                df = dfs[chave]
                conjuntos.append({
                    "chave": chave,
                    "titulo": titulo,
                    "path": rel,
                    "separador": sep,
                    "n_linhas": int(df.shape[0]),
                    "n_colunas": int(df.shape[1]),
                    "colunas": [str(c) for c in df.columns],
                })

            # dados das tabelas para anexo no Typst
            tabelas = []
            for chave, titulo in CONJUNTOS.items():
                rel, sep, _ = _fonte(chave)
                df = dfs[chave]
                exib = df.head(LIMITE_LINHAS_EXIBICAO).fillna("")
                tabelas.append({
                    "titulo": titulo,
                    "path": rel,
                    "n_linhas": int(df.shape[0]),
                    "n_exibidas": int(exib.shape[0]),
                    "colunas": [str(c) for c in exib.columns],
                    "linhas": exib.astype(str).values.tolist(),
                })

            s = deepcopy(estado_wizard())

            d_tab = s["passos"]["tabela"]["dados"]
            d_tab["conjuntos"] = conjuntos

            d_rel = s["passos"]["relatorio"]["dados"]
            d_rel["pasta_saida"] = str(pasta_saida)

            # 2) Renderiza Typst com Jinja
            contexto_typst = {
                "conjuntos": conjuntos,
                "tabelas": tabelas,
                "scatter_nome": nome_png,
                "elementos": elementos,
                "graficos_elementos": graficos_elementos,
            }

            nome_typ = "relatorio.typ"
            nome_pdf = "relatorio.pdf"
            caminho_typ = pasta_saida / nome_typ
            caminho_pdf = pasta_saida / nome_pdf

            conteudo_typ = renderizar_relatorio_typst(
                contexto_typst,
                template_name="template_relatorio.typ.j2",
            )
            caminho_typ.write_text(conteudo_typ, encoding="utf-8")

            # 3) Compila PDF com Typst
            subprocess.run(
                ["typst", "compile", str(caminho_typ), str(caminho_pdf)],
                check=True,
                cwd=str(pasta_saida),
            )

            d_rel["typ_path"] = str(caminho_typ)
            d_rel["pdf_path"] = str(caminho_pdf)
            d_rel["arquivos"] = (
                [nome_png]
                + [g["nome"] for g in graficos_elementos]
                + [nome_typ, nome_pdf]
            )

            s["passos"]["tabela"]["estado"] = "preenchido"
            s["passos"]["relatorio"]["estado"] = "preenchido"
            s["etapa_atual"] = "relatorio"

            estado_wizard.set(s)

        except Exception as e:
            import traceback
            traceback.print_exc()
            erro_geracao.set(f"{type(e).__name__}: {e}")
        finally:
            gerando.set(False)