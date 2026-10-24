import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cross_decomposition import PLSRegression


def _colunas_x(df_xcalib, df_xvalid):
    cols_valid = {str(c) for c in df_xvalid.columns if str(c) != "Amostra"}
    cols = [
        str(c)
        for c in df_xcalib.columns
        if str(c) != "Amostra" and str(c) in cols_valid
    ]
    if not cols:
        raise ValueError("Nenhuma coluna X em comum entre Xcalib e Xvalid.")
    return cols


def _dados_ajuste(df_xcalib, df_ycalib, df_xvalid, df_yvalid, elemento, agregar):
    cols = _colunas_x(df_xcalib, df_xvalid)

    for nome, df in [("Ycalib", df_ycalib), ("Yvalid", df_yvalid)]:
        if elemento not in df.columns:
            raise ValueError(f"Coluna '{elemento}' não existe em {nome}.")

    Xc = df_xcalib[cols].to_numpy(dtype=float)
    yc = df_ycalib[elemento].to_numpy(dtype=float)
    Xv = df_xvalid[cols].to_numpy(dtype=float)
    yv = df_yvalid[elemento].to_numpy(dtype=float)

    if agregar:
        X = np.vstack([Xc, Xv])
        y = np.concatenate([yc, yv])
    else:
        X = Xc
        y = yc

    return cols, X, y


def n_max_lvs(df_xcalib, df_xvalid, agregar):
    cols = _colunas_x(df_xcalib, df_xvalid)
    n = len(df_xcalib) + (len(df_xvalid) if agregar else 0)
    return max(1, min(n - 1, len(cols)))


def _preprocessar(X, y, centragem="media", autoescalonamento=False):
    if centragem not in ("media", "nenhuma"):
        raise ValueError("centragem deve ser 'media' ou 'nenhuma'.")

    if centragem == "media":
        mx = X.mean(axis=0)
        my = float(np.mean(y))
    else:
        mx = np.zeros(X.shape[1], dtype=float)
        my = 0.0

    Xp = X - mx
    yp = y - my

    if autoescalonamento:
        sx = Xp.std(axis=0, ddof=1)
        sx = np.where(sx == 0, 1.0, sx)
        Xp = Xp / sx
    else:
        sx = np.ones(X.shape[1], dtype=float)

    return Xp, yp, mx, my, sx


def variancia_pls(X, y, n_lvs_max, centragem="media", autoescalonamento=False):
    """
    Retorna variância acumulada explicada (%) em X e Y para k=1..n_lvs_max.
    """
    Xp, yp, _, _, _ = _preprocessar(
        X, y, centragem=centragem, autoescalonamento=autoescalonamento
    )
    yp2 = yp.reshape(-1, 1)

    ss_x = float(np.sum(Xp ** 2))
    ss_y = float(np.sum((yp2 - yp2.mean(axis=0)) ** 2))

    var_x = []
    var_y = []

    for k in range(1, n_lvs_max + 1):
        pls = PLSRegression(n_components=k, scale=False).fit(Xp, yp2)

        T = pls.x_scores_
        P = pls.x_loadings_
        X_rec = T @ P.T
        vx = 100.0 * float(np.sum(X_rec ** 2)) / ss_x if ss_x != 0 else 0.0
        var_x.append(vx)

        y_hat = pls.predict(Xp).reshape(-1, 1)
        ss_res = float(np.sum((yp2 - y_hat) ** 2))
        vy = 100.0 * (1.0 - ss_res / ss_y) if ss_y != 0 else 0.0
        var_y.append(vy)

    return np.array(var_x), np.array(var_y)


def figura_variancia_pls(var_x, var_y, n_lvs=None, titulo="PLS: variância explicada acumulada"):
    x = np.arange(1, len(var_x) + 1)
    fig, ax = plt.subplots(figsize=(6.5, 4))

    if n_lvs:
        ax.axvspan(0.5, n_lvs + 0.5, color="gray", alpha=0.12, label=f"{n_lvs} LV(s)")

    ax.plot(x, var_x, color="tab:blue", marker="o", linewidth=2, label="X (acumulada)")
    ax.plot(x, var_y, color="tab:red", marker="o", linewidth=2, label="Y (acumulada)")

    for xi, vx, vy in zip(x, var_x, var_y):
        ax.annotate(
            f"{vx:.1f}%",
            (xi, vx),
            ha="center",
            va="top",
            fontsize=7,
            xytext=(0, -9),
            textcoords="offset points",
            color="tab:blue",
        )
        ax.annotate(
            f"{vy:.1f}%",
            (xi, vy),
            ha="center",
            va="bottom",
            fontsize=7,
            xytext=(0, 5),
            textcoords="offset points",
            color="tab:red",
        )

    ax.set_xticks(x)
    ax.set_xlabel("Número de variáveis latentes (LVs)")
    ax.set_ylabel("Variância explicada acumulada (%)")
    ax.set_title(titulo)
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


def gerar_pls(
    df_xcalib,
    df_ycalib,
    df_xvalid,
    df_yvalid,
    elemento,
    pasta_saida,
    n_lvs,
    agregar=False,
    centragem="media",
    autoescalonamento=False,
):
    cols, X, y = _dados_ajuste(
        df_xcalib, df_ycalib, df_xvalid, df_yvalid, elemento, agregar
    )

    n_max = max(1, min(X.shape[0] - 1, X.shape[1]))
    if not 1 <= n_lvs <= n_max:
        raise ValueError(f"n_lvs deve estar entre 1 e {n_max} (recebido: {n_lvs}).")

    var_x, var_y = variancia_pls(
        X,
        y,
        n_max,
        centragem=centragem,
        autoescalonamento=autoescalonamento,
    )

    nome_png = f"pls_{elemento}_variancia.png"
    subt = (
        f"{elemento} | agregar={'sim' if agregar else 'não'}, "
        f"centragem={centragem}, "
        f"autoescalonamento={'sim' if autoescalonamento else 'não'}"
    )
    fig = figura_variancia_pls(
        var_x,
        var_y,
        n_lvs=n_lvs,
        titulo=f"PLS: variância explicada acumulada\n{subt}",
    )
    fig.savefig(pasta_saida / nome_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    tab_var = {
        "titulo": "Variância explicada acumulada por LV",
        "colunas": ["LVs", "X acumulada (%)", "Y acumulada (%)"],
        "linhas": [
            [str(i + 1), f"{var_x[i]:.2f}", f"{var_y[i]:.2f}"]
            for i in range(n_max)
        ],
    }

    return {
        "elemento": elemento,
        "agregar": bool(agregar),
        "centragem": centragem,
        "autoescalonamento": bool(autoescalonamento),
        "n_lvs": int(n_lvs),
        "n_max": int(n_max),
        "n_amostras_ajuste": int(X.shape[0]),
        "colunas": cols,
        "grafico_variancia": nome_png,
        "arquivos": [nome_png],
        "var_x_acum": [round(float(v), 2) for v in var_x],
        "var_y_acum": [round(float(v), 2) for v in var_y],
        "tabelas": [tab_var],
    }