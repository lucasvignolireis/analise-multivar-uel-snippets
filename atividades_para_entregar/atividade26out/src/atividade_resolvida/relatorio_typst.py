from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

BASE_DIR = Path(__file__).resolve().parent  # src/atividade_resolvida
SRC_ROOT = BASE_DIR.parent  # src/

_env = Environment(
    loader=FileSystemLoader(BASE_DIR),
    undefined=StrictUndefined,
    keep_trailing_newline=True,
    autoescape=False,
)


def _typ(valor) -> str:
    """Converte um valor em string literal do Typst (com escape)."""
    s = str(valor).replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\r", " ").replace("\n", " ")
    return f'"{s}"'


_env.filters["typ"] = _typ


def _source(rel_path: str, inicio: int | None = None, fim: int | None = None) -> str:
    """
    Lê um arquivo relativo a src/ e devolve o texto (opcionalmente só um trecho).

    inicio, fim: números de linha (base 1, ambos inclusivos).
    - inicio=None -> começa na primeira linha
    - fim=None    -> vai até a última linha
    """
    p = (SRC_ROOT / rel_path).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    linhas = p.read_text(encoding="utf-8").splitlines()
    total = len(linhas)

    ini = 1 if inicio is None else inicio
    end = total if fim is None else fim

    if ini < 1 or end < ini or ini > total:
        raise ValueError(
            f"Intervalo inválido ({inicio}, {fim}) para {rel_path} ({total} linhas)"
        )

    return "\n".join(linhas[ini - 1 : min(end, total)])


def renderizar_relatorio_typst(
    contexto: dict,
    template_name: str = "template_relatorio.typ.j2",
) -> str:
    template = _env.get_template(template_name)
    return template.render(**contexto, source=_source)