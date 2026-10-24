from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _colunas_elementos(df_xcalib, df_xvalid=None):
    """Retorna colunas de elementos (ignora 'Amostra') preservando ordem de Xcalib."""
    cols_calib = [str(c) for c in df_xcalib.columns if str(c) != "Amostra"]
    if df_xvalid is None:
        return cols_calib

    cols_valid = {str(c) for c in df_xvalid.columns if str(c) != "Amostra"}
    return [c for c in cols_calib if c in cols_valid]


def _rotulos_amostras(df, prefixo):
    """
    Retorna rótulos de amostra:
    - se coluna 'Amostra' existir: prefixo + valor da coluna (ex: C12, V3)
    - senão: prefixo + índice 1..n (ex: C1, C2, ...)
    """
    if "Amostra" in df.columns:
        vals = [str(v).strip() for v in df["Amostra"].tolist()]
        return [f"{prefixo}{v}" for v in vals]
    return [f"{prefixo}{i+1}" for i in range(len(df))]


def _anotar_pontos(ax, xs, ys, labels, cor, dx=4, dy=4, fs=7):
    for x, y, lab in zip(xs, ys, labels):
        ax.annotate(
            lab,
            (x, y),
            textcoords="offset points",
            xytext=(dx, dy),
            ha="left",
            va="bottom",
            fontsize=fs,
            color=cor,
            alpha=0.9,
        )


def gerar_scatter_elementos(
    df_xcalib: pd.DataFrame,
    df_ycalib: pd.DataFrame,
    df_xvalid: pd.DataFrame,
    df_yvalid: pd.DataFrame,
    caminho_saida: Path,
):
    """
    Gera scatter X vs Y para cada elemento em um único gráfico.
    Salva em caminho_saida e retorna a lista de elementos usados.
    """
    elementos = _colunas_elementos(df_xcalib, df_xvalid)
    if not elementos:
        raise ValueError("Nenhum elemento em comum entre Xcalib e Xvalid.")

    fig, ax = plt.subplots(figsize=(8, 5))

    rot_cal = _rotulos_amostras(df_xcalib, "C")
    rot_val = _rotulos_amostras(df_xvalid, "V")

    primeira_cal = True
    primeira_val = True

    for el in elementos:
        if el not in df_ycalib.columns or el not in df_yvalid.columns:
            # ignora elemento sem Y correspondente
            continue

        x_cal = df_xcalib[el].astype(float).to_numpy()
        y_cal = df_ycalib[el].astype(float).to_numpy()
        x_val = df_xvalid[el].astype(float).to_numpy()
        y_val = df_yvalid[el].astype(float).to_numpy()

        ax.scatter(
            x_cal,
            y_cal,
            marker="o",
            s=30,
            alpha=0.75,
            label="calibração" if primeira_cal else None,
        )
        ax.scatter(
            x_val,
            y_val,
            marker="x",
            s=55,
            linewidths=1.6,
            label="validação" if primeira_val else None,
        )

        # labels C1.. e V1..
        _anotar_pontos(ax, x_cal, y_cal, rot_cal, cor="tab:blue", dx=3, dy=3, fs=6.5)
        _anotar_pontos(ax, x_val, y_val, rot_val, cor="tab:red", dx=3, dy=3, fs=6.5)

        primeira_cal = False
        primeira_val = False

    ax.set_xlabel("Intensidade (X)")
    ax.set_ylabel("Concentração (Y)")
    ax.set_title("Visualização inicial dos dados (todos os elementos)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return elementos


def gerar_scatter_por_elemento(
    df_xcalib: pd.DataFrame,
    df_ycalib: pd.DataFrame,
    df_xvalid: pd.DataFrame,
    df_yvalid: pd.DataFrame,
    elementos,
    pasta_saida: Path,
):
    """
    Gera um scatter por elemento.
    Retorna lista de dicts: [{"elemento": "...", "nome": "scatter_elemento_....png"}, ...]
    """
    resultados = []
    pasta_saida.mkdir(parents=True, exist_ok=True)

    rot_cal = _rotulos_amostras(df_xcalib, "C")
    rot_val = _rotulos_amostras(df_xvalid, "V")

    for el in elementos:
        if el not in df_xcalib.columns:
            continue
        if el not in df_xvalid.columns:
            continue
        if el not in df_ycalib.columns:
            continue
        if el not in df_yvalid.columns:
            continue

        x_cal = df_xcalib[el].astype(float).to_numpy()
        y_cal = df_ycalib[el].astype(float).to_numpy()
        x_val = df_xvalid[el].astype(float).to_numpy()
        y_val = df_yvalid[el].astype(float).to_numpy()

        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.scatter(x_cal, y_cal, marker="o", s=34, alpha=0.8, label="calibração", color="tab:blue")
        ax.scatter(x_val, y_val, marker="x", s=60, linewidths=1.8, label="validação", color="tab:red")

        # labels C1.. e V1..
        _anotar_pontos(ax, x_cal, y_cal, rot_cal, cor="tab:blue", dx=4, dy=4, fs=7)
        _anotar_pontos(ax, x_val, y_val, rot_val, cor="tab:red", dx=4, dy=4, fs=7)

        ax.set_xlabel(f"Intensidade de {el} (X)")
        ax.set_ylabel(f"Concentração de {el} (Y)")
        ax.set_title(f"Scatter X vs Y - {el}")
        ax.grid(True, alpha=0.3)
        ax.legend()

        fig.tight_layout()
        nome = f"scatter_elemento_{el}.png"
        fig.savefig(pasta_saida / nome, dpi=150, bbox_inches="tight")
        plt.close(fig)

        resultados.append({"elemento": el, "nome": nome})

    return resultados