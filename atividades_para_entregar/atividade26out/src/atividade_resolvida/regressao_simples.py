import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def gerar_regressao_simples(
    df_xcalib, df_ycalib, df_xvalid, df_yvalid, elemento, pasta_saida
):
    for nome, df in [
        ("Xcalib", df_xcalib),
        ("Ycalib", df_ycalib),
        ("Xvalid", df_xvalid),
        ("Yvalid", df_yvalid),
    ]:
        if elemento not in df.columns:
            raise ValueError(f"Coluna '{elemento}' não existe em {nome}.")

    x_cal = df_xcalib[elemento].to_numpy(dtype=float)
    y_cal = df_ycalib[elemento].to_numpy(dtype=float)
    x_val = df_xvalid[elemento].to_numpy(dtype=float)
    y_val = df_yvalid[elemento].to_numpy(dtype=float)

    n_cal = len(x_cal)
    n_val = len(x_val)
    if n_cal < 3:
        raise ValueError("Amostras insuficientes para regressão (mínimo 3 no calibração).")

    # Ajuste linear: y = b0 + b1*x
    b1, b0 = np.polyfit(x_cal, y_cal, 1)
    y_hat_cal = b0 + b1 * x_cal
    resid = y_cal - y_hat_cal

    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((y_cal - y_cal.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0
    rmsec = float(np.sqrt(ss_res / max(n_cal - 2, 1)))

    y_hat_val = b0 + b1 * x_val
    rmsep = float(np.sqrt(np.mean((y_val - y_hat_val) ** 2)))

    # gráfico
    nome_png = f"regressao_{elemento}.png"
    fig, ax = plt.subplots(figsize=(7.0, 5.0))

    ax.scatter(
        x_cal, y_cal,
        marker="o", s=34, alpha=0.82, color="tab:blue",
        label="calibração"
    )
    ax.scatter(
        x_val, y_val,
        marker="x", s=62, linewidths=1.8, color="tab:red",
        label="validação"
    )

    x_min = float(min(x_cal.min(), x_val.min()))
    x_max = float(max(x_cal.max(), x_val.max()))
    xs = np.linspace(x_min, x_max, 200)
    ys = b0 + b1 * xs
    ax.plot(
        xs, ys,
        color="black", linewidth=1.8,
        label=f"Y = {b0:.4f} + {b1:.4f}·X  (R²={r2:.4f})"
    )

    ax.set_xlabel(f"Intensidade de {elemento} (X)")
    ax.set_ylabel(f"Concentração de {elemento} (Y)")
    ax.set_title(f"Regressão linear simples - {elemento}")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(pasta_saida / nome_png, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "elemento": elemento,
        "grafico": nome_png,
        "arquivos": [nome_png],
        "n_calib": int(n_cal),
        "n_valid": int(n_val),
        "intercepto": float(b0),
        "inclinacao": float(b1),
        "equacao": f"Y = {b0:.4f} + {b1:.4f}·X",
        "r2": float(r2),
        "rmsec": float(rmsec),
        "rmsep": float(rmsep),
    }