import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA


def _colunas_x(df_xcalib, df_xvalid=None):
    cols_calib = [str(c) for c in df_xcalib.columns if str(c) != "Amostra"]
    if df_xvalid is None:
        if not cols_calib:
            raise ValueError("Xcalib não tem colunas para o PCA.")
        return cols_calib

    cols_valid = {str(c) for c in df_xvalid.columns if str(c) != "Amostra"}
    cols = [c for c in cols_calib if c in cols_valid]
    if not cols:
        raise ValueError("Nenhuma coluna em comum entre Xcalib e Xvalid para o PCA.")
    return cols


def _fmt(v, casas=4):
    return f"{v:.{casas}f}"


def _rotulos_amostras(df, prefixo):
    if "Amostra" in df.columns:
        vals = [str(v).strip() for v in df["Amostra"].tolist()]
        return [f"{prefixo}{v}" for v in vals]
    return [f"{prefixo}{i+1}" for i in range(len(df))]


def _anotar_scores(ax, T, labels, cor, dx=4, dy=4, fs=7):
    for (x, y), lab in zip(T[:, :2], labels):
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


def _preprocessar(Xc, Xv, centragem="media", autoescalonamento=False):
    if centragem not in ("media", "nenhuma"):
        raise ValueError("centragem deve ser 'media' ou 'nenhuma'.")

    media = Xc.mean(axis=0) if centragem == "media" else np.zeros(Xc.shape[1])
    Xc_p = Xc - media
    Xv_p = Xv - media

    if autoescalonamento:
        std = Xc_p.std(axis=0, ddof=1)
        std = np.where(std == 0, 1.0, std)
        Xc_p = Xc_p / std
        Xv_p = Xv_p / std
    else:
        std = np.ones(Xc.shape[1])

    return Xc_p, Xv_p, media, std


def variancia_explicada(df_xcalib, centragem="media", autoescalonamento=False):
    cols = _colunas_x(df_xcalib)
    Xc = df_xcalib[cols].to_numpy(dtype=float)
    Xc_p, _, _, _ = _preprocessar(Xc, Xc, centragem, autoescalonamento)

    pca = PCA(n_components=min(Xc_p.shape), svd_solver="full").fit(Xc_p)
    var = pca.explained_variance_ratio_ * 100
    return cols, var, np.cumsum(var)


def figura_variancia(var, var_acum, n_pcs=None, titulo="PCA: variância explicada"):
    x = np.arange(1, len(var) + 1)
    fig, ax = plt.subplots(figsize=(6.5, 4))

    if n_pcs:
        ax.axvspan(0.5, n_pcs + 0.5, color="gray", alpha=0.12, label=f"{n_pcs} PC(s)")

    ax.plot(x, var, color="tab:blue", marker="o", linewidth=2, label="individual")
    ax.plot(x, var_acum, color="tab:red", marker="o", linewidth=2, label="acumulada")

    for xi, v in zip(x, var):
        ax.annotate(
            f"{v:.1f}%",
            (xi, v),
            ha="center",
            va="bottom",
            fontsize=8,
            xytext=(0, 4),
            textcoords="offset points",
        )

    ax.set_xticks(x)
    ax.set_xticklabels([f"PC{i}" for i in x])
    ax.set_ylabel("Variância explicada (%)")
    ax.set_title(titulo)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="center right")
    fig.tight_layout()
    return fig


def gerar_pca(
    df_xcalib,
    df_xvalid,
    pasta_saida,
    n_pcs,
    centragem="media",
    autoescalonamento=False,
    prefixo="pca",
    agregar=False,
):
    cols = _colunas_x(df_xcalib, df_xvalid)
    Xc = df_xcalib[cols].to_numpy(dtype=float)
    Xv = df_xvalid[cols].to_numpy(dtype=float)

    X_modelo = np.vstack([Xc, Xv]) if agregar else Xc
    n_max = min(X_modelo.shape)
    if not 1 <= n_pcs <= n_max:
        raise ValueError(f"n_pcs deve estar entre 1 e {n_max} (recebido: {n_pcs}).")

    X_modelo_p, Xv_p, media, std = _preprocessar(
        X_modelo,
        Xv,
        centragem=centragem,
        autoescalonamento=autoescalonamento,
    )

    if agregar:
        Xall_p = X_modelo_p
        n_cal = Xc.shape[0]
        Xc_proj = Xall_p[:n_cal, :]
        Xv_proj = Xall_p[n_cal:, :]
    else:
        Xall_p = X_modelo_p
        Xc_proj = X_modelo_p
        Xv_proj = Xv_p

    pca_full = PCA(n_components=n_max, svd_solver="full").fit(Xall_p)
    var = pca_full.explained_variance_ratio_ * 100
    var_acum = np.cumsum(var)
    autovalores = pca_full.explained_variance_

    P = pca_full.components_[:n_pcs]
    T_calib = Xc_proj @ P.T
    T_valid = Xv_proj @ P.T
    pcs = [f"PC{i + 1}" for i in range(n_pcs)]
    arquivos = []

    # 1) variância
    nome_variancia = f"{prefixo}_variancia.png"
    subt = (
        f"centragem={centragem}, "
        f"autoescalonamento={'sim' if autoescalonamento else 'não'}, "
        f"agregar={'sim' if agregar else 'não'}"
    )
    fig = figura_variancia(var, var_acum, n_pcs=n_pcs, titulo=f"PCA: variância explicada\n{subt}")
    fig.savefig(pasta_saida / nome_variancia, dpi=150, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(nome_variancia)

    # 2) scores PC1 x PC2
    nome_scores = None
    if n_pcs >= 2:
        nome_scores = f"{prefixo}_scores.png"
        fig, ax = plt.subplots(figsize=(6.5, 5))

        ax.scatter(
            T_calib[:, 0], T_calib[:, 1],
            marker="o", s=32, alpha=0.75, color="tab:blue", label="calibração",
        )
        ax.scatter(
            T_valid[:, 0], T_valid[:, 1],
            marker="x", s=55, linewidths=1.8, color="tab:red", label="validação",
        )

        # labels C1.. e V1..
        labs_cal = _rotulos_amostras(df_xcalib, "C")
        labs_val = _rotulos_amostras(df_xvalid, "V")
        _anotar_scores(ax, T_calib, labs_cal, cor="tab:blue", dx=4, dy=4, fs=7)
        _anotar_scores(ax, T_valid, labs_val, cor="tab:red", dx=4, dy=4, fs=7)

        ax.axhline(0, color="gray", lw=0.6)
        ax.axvline(0, color="gray", lw=0.6)
        ax.set_xlabel(f"PC1 ({var[0]:.1f}%)")
        ax.set_ylabel(f"PC2 ({var[1]:.1f}%)")
        ax.set_title("PCA: scores")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(pasta_saida / nome_scores, dpi=150, bbox_inches="tight")
        plt.close(fig)
        arquivos.append(nome_scores)

    # 3) loadings
    nome_loadings = f"{prefixo}_loadings.png"
    x = np.arange(len(cols))
    largura = 0.8 / n_pcs
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for k in range(n_pcs):
        ax.bar(
            x + (k - (n_pcs - 1) / 2) * largura,
            P[k],
            width=largura,
            label=pcs[k],
        )
    ax.set_xticks(x)
    ax.set_xticklabels(cols)
    ax.axhline(0, color="gray", lw=0.6)
    ax.set_ylabel("Loading")
    ax.set_title("PCA: loadings")
    ax.grid(True, alpha=0.3, axis="y")
    ax.legend()
    fig.tight_layout()
    fig.savefig(pasta_saida / nome_loadings, dpi=150, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(nome_loadings)

    def amostras(df):
        if "Amostra" in df.columns:
            return [str(a) for a in df["Amostra"]]
        return [str(i + 1) for i in range(len(df))]

    tab_variancia = {
        "titulo": "Variância explicada por componente",
        "colunas": ["PC", "Autovalor", "Variância (%)", "Acumulada (%)"],
        "linhas": [
            [f"PC{i + 1}", _fmt(autovalores[i]), _fmt(var[i], 2), _fmt(var_acum[i], 2)]
            for i in range(n_max)
        ],
    }

    tab_loadings = {
        "titulo": "Loadings das componentes escolhidas",
        "colunas": ["Variável"] + pcs,
        "linhas": [
            [cols[j]] + [_fmt(P[k, j]) for k in range(n_pcs)]
            for j in range(len(cols))
        ],
    }

    tab_scores_calib = {
        "titulo": "Scores: conjunto de calibração",
        "colunas": ["Amostra"] + pcs,
        "linhas": [
            [a] + [_fmt(v) for v in linha]
            for a, linha in zip(amostras(df_xcalib), T_calib)
        ],
    }

    tab_scores_valid = {
        "titulo": "Scores: conjunto de validação",
        "colunas": ["Amostra"] + pcs,
        "linhas": [
            [a] + [_fmt(v) for v in linha]
            for a, linha in zip(amostras(df_xvalid), T_valid)
        ],
    }

    return {
        "variancia": nome_variancia,
        "scores": nome_scores,
        "loadings": nome_loadings,
        "arquivos": arquivos,
        "prefixo": prefixo,
        "colunas": cols,
        "n_pcs": n_pcs,
        "n_max": n_max,
        "centragem": centragem,
        "autoescalonamento": autoescalonamento,
        "agregar": agregar,
        "media": [float(m) for m in media],
        "desvio": [float(s) for s in std],
        "variancia_pct": [round(float(v), 2) for v in var],
        "variancia_acum_pct": [round(float(v), 2) for v in var_acum],
        "tabelas": [tab_variancia, tab_loadings, tab_scores_calib, tab_scores_valid],
    }