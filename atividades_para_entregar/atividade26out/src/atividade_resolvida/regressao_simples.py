import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _fmt(v, casas=4):
    return f"{v:.{casas}f}"


def _rotulos(df, prefixo):
    if "Amostra" in df.columns:
        return [f"{prefixo}{str(v).strip()}" for v in df["Amostra"]]
    return [f"{prefixo}{int(i) + 1}" for i in df.index]


def gerar_regressao_simples(
    df_xcalib, df_ycalib, df_xvalid, df_yvalid, elemento, pasta_saida, prefixo=""
):
    for nome, df in [
        ("Xcalib", df_xcalib),
        ("Ycalib", df_ycalib),
        ("Xvalid", df_xvalid),
        ("Yvalid", df_yvalid),
    ]:
        if elemento not in df.columns:
            raise ValueError(f"Coluna '{elemento}' não existe em {nome}.")

    pref = f"{prefixo}_" if prefixo else ""

    x_cal = df_xcalib[elemento].to_numpy(dtype=float)
    y_cal = df_ycalib[elemento].to_numpy(dtype=float)
    x_val = df_xvalid[elemento].to_numpy(dtype=float)
    y_val = df_yvalid[elemento].to_numpy(dtype=float)

    n_cal = len(x_cal)
    n_val = len(x_val)
    if n_cal < 3:
        raise ValueError("Amostras insuficientes para regressão (mínimo 3).")

    b1, b0 = np.polyfit(x_cal, y_cal, 1)
    y_hat_cal = b0 + b1 * x_cal
    resid_cal = y_cal - y_hat_cal

    # ANOVA
    ss_reg = float(np.sum((y_hat_cal - y_cal.mean()) ** 2))
    ss_res = float(np.sum(resid_cal ** 2))
    ss_tot = ss_reg + ss_res
    gl_reg, gl_res, gl_tot = 1, n_cal - 2, n_cal - 1
    ms_reg = ss_reg / gl_reg
    ms_res = ss_res / gl_res
    f_val = ms_reg / ms_res if ms_res != 0 else float("inf")
    r2 = ss_reg / ss_tot if ss_tot != 0 else 0.0
    rmsec = float(np.sqrt(ms_res))

    y_hat_val = b0 + b1 * x_val
    resid_val = y_val - y_hat_val
    # Resíduo relativo em validação (%): (Y - Ŷ) / Y * 100
    resid_rel_val = np.where(y_val != 0, (resid_val / y_val) * 100.0, np.nan)

    rmsep = float(np.sqrt(np.mean(resid_val ** 2)))

    rot_cal = _rotulos(df_xcalib, "C")
    rot_val = _rotulos(df_xvalid, "V")

    # gráfico da regressão
    nome_png = f"{pref}regressao_{elemento}.png"
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.scatter(x_cal, y_cal, marker="o", s=34, alpha=0.82,
               color="tab:blue", label="calibração")
    ax.scatter(x_val, y_val, marker="x", s=62, linewidths=1.8,
               color="tab:red", label="validação")
    xs = np.linspace(min(x_cal.min(), x_val.min()),
                     max(x_cal.max(), x_val.max()), 200)
    ax.plot(xs, b0 + b1 * xs, color="black", linewidth=1.8,
            label=f"Y = {b0:.4f} + {b1:.4f}·X  (R²={r2:.4f})")
    ax.set_xlabel(f"Intensidade de {elemento} (X)")
    ax.set_ylabel(f"Concentração de {elemento} (Y)")
    ax.set_title(f"Regressão linear simples - {elemento}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(pasta_saida / nome_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # gráfico de resíduos (vs valor previsto)
    nome_res = f"{pref}residuos_{elemento}.png"
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.scatter(y_hat_cal, resid_cal, marker="o", s=34, alpha=0.82,
               color="tab:blue", label="calibração")
    ax.scatter(y_hat_val, resid_val, marker="x", s=62, linewidths=1.8,
               color="tab:red", label="validação")
    for xx, yy, lab in zip(y_hat_cal, resid_cal, rot_cal):
        ax.annotate(lab, (xx, yy), textcoords="offset points",
                    xytext=(4, 4), fontsize=6.5, color="tab:blue")
    for xx, yy, lab in zip(y_hat_val, resid_val, rot_val):
        ax.annotate(lab, (xx, yy), textcoords="offset points",
                    xytext=(4, 4), fontsize=6.5, color="tab:red")
    ax.axhline(0, color="black", lw=1)
    ax.set_xlabel(f"Concentração prevista de {elemento}")
    ax.set_ylabel("Resíduo (Y - Ŷ)")
    ax.set_title(f"Resíduos - {elemento}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(pasta_saida / nome_res, dpi=150, bbox_inches="tight")
    plt.close(fig)

    tab_anova = {
        "titulo": "ANOVA da regressão",
        "colunas": ["Fonte", "SQ", "GL", "MQ", "F"],
        "linhas": [
            ["Regressão", _fmt(ss_reg), str(gl_reg), _fmt(ms_reg), _fmt(f_val)],
            ["Resíduo", _fmt(ss_res), str(gl_res), _fmt(ms_res), ""],
            ["Total", _fmt(ss_tot), str(gl_tot), "", ""],
        ],
    }

    tab_res_calib = {
        "titulo": "Resíduos: calibração",
        "colunas": ["Amostra", "X", "Y", "Y previsto", "Resíduo"],
        "linhas": [
            [r, _fmt(x), _fmt(y), _fmt(yh), _fmt(e)]
            for r, x, y, yh, e in zip(rot_cal, x_cal, y_cal, y_hat_cal, resid_cal)
        ],
    }
    tab_res_valid = {
        "titulo": "Resíduos: validação",
        "colunas": ["Amostra", "X", "Y", "Y previsto", "Resíduo", "Resíduo rel. (%)"],
        "linhas": [
            [r, _fmt(x), _fmt(y), _fmt(yh), _fmt(e), _fmt(er, 2)]
            for r, x, y, yh, e, er in zip(rot_val, x_val, y_val, y_hat_val, resid_val, resid_rel_val)
        ],
    }

    return {
        "elemento": elemento,
        "grafico": nome_png,
        "grafico_residuos": nome_res,
        "arquivos": [nome_png, nome_res],
        "n_calib": int(n_cal),
        "n_valid": int(n_val),
        "intercepto": float(b0),
        "inclinacao": float(b1),
        "equacao": f"Y = {b0:.4f} + {b1:.4f}·X",
        "r2": _fmt(r2),
        "rmsec": _fmt(rmsec),
        "rmsep": _fmt(rmsep),
        "tabelas": [tab_anova, tab_res_calib, tab_res_valid],
    }