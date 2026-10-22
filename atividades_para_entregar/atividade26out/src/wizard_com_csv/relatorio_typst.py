from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).resolve().parent

_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    autoescape=False,  # template Typst (texto), não HTML
)


def renderizar_relatorio_typst(
    contexto: dict,
    template_name: str = "relatorio.typ.j2",
) -> str:
    """
    Renderiza o template Typst com Jinja2.
    Exemplo de uso:
        conteudo = renderizar_relatorio_typst(
            {"arquivo_path": "...", "n_linhas": 10, ...}
        )
    """
    template = _env.get_template(template_name)
    return template.render(**contexto)