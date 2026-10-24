import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def gerar_scatter_elementos(df_xcalib, df_ycalib, df_xvalid, df_yvalid, caminho_png):
    """
    Scatter X (eixo x) vs Y (eixo y), com 2 séries por elemento:
      - calibração: bolinhas
      - validação: cruzinhas
    Mesma cor para o mesmo elemento.
    Retorna a lista de elementos plotados.
    """
    dfs = (df_xcalib, df_ycalib, df_xvalid, df_yvalid)

    comuns = set(map(str, dfs[0].columns))
    for df in dfs[1:]:
        comuns &= set(map(str, df.columns))
    comuns.discard("Amostra")
    elementos = [c for c in map(str, df_xcalib.columns) if c in comuns]

    if not elementos:
        raise ValueError(
            "Nenhuma coluna de elemento em comum entre Xcalib, Ycalib, Xvalid e Yvalid."
        )

    cmap = plt.get_cmap("tab10")

    fig, ax = plt.subplots(figsize=(9, 6))
    for i, el in enumerate(elementos):
        cor = cmap(i % 10)

        ax.scatter(
            df_xcalib[el], df_ycalib[el],
            marker="o", s=28, color=cor, alpha=0.75,
            label=f"{el} (calibração)",
        )
        ax.scatter(
            df_xvalid[el], df_yvalid[el],
            marker="x", s=48, linewidths=1.8, color=cor,
            label=f"{el} (validação)",
        )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Scatter X vs Y por elemento")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=2, fontsize=8, loc="center left", bbox_to_anchor=(1.01, 0.5))
    fig.tight_layout()
    fig.savefig(caminho_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return elementos