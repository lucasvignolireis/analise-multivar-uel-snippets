import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA


def _colunas_x(df_xcalib):
    """Colunas numéricas de Xcalib (ignora 'Amostra')."""
    cols = [str(c) for c in df_xcalib.columns if str(c) != "Amostra"]
    if not cols:
        raise ValueError("Xcalib não tem colunas para o PCA.")
    return cols


def gerar_pca_variancia(df_xcalib, pasta_saida):
    """
    PCA ajustado em Xcalib, apenas com centragem na média (sem escalonamento).
    Gera o gráfico de variância explicada (individual e acumulada) com todas
    as componentes possíveis e devolve nome do PNG e valores.
    """
    cols = _colunas_x(df_xcalib)
    Xc = df_xcalib[cols].to_numpy(dtype=float)

    n_comp = min(Xc.shape)
    pca = PCA(n_components=n_comp)  # centra na média, não escalona
    pca.fit(Xc)

    var = pca.explained_variance_ratio_ * 100
    var_acum = np.cumsum(var)
    pcs = [f"PC{i + 1}" for i in range(n_comp)]

    nome_png = "pca_variancia.png"

    fig, ax = plt.subplots(figsize=(6.5, 4))

    # linha da variância individual (scree)
    ax.plot(
        pcs, var,
        color="tab:blue",
        marker="o",
        linewidth=2,
        label="individual",
    )

    # linha da variância acumulada
    ax.plot(
        pcs, var_acum,
        color="tab:red",
        marker="o",
        linewidth=2,
        label="acumulada",
    )

    # rótulos nos pontos da variância individual
    for x, v in zip(pcs, var):
        ax.annotate(
            f"{v:.1f}%",
            (x, v),
            ha="center", va="bottom",
            fontsize=8,
            xytext=(0, 4), textcoords="offset points",
        )

    ax.set_ylabel("Variância explicada (%)")
    ax.set_title("PCA: variância explicada (Xcalib, centrado na média)")
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="center right")
    fig.tight_layout()
    fig.savefig(pasta_saida / nome_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "variancia": nome_png,
        "colunas": cols,
        "n_componentes": n_comp,
        "variancia_pct": [round(float(v), 2) for v in var],
        "variancia_acum_pct": [round(float(v), 2) for v in var_acum],
    }