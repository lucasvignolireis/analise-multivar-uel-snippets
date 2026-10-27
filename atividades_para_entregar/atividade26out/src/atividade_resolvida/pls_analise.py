import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from sklearn.cross_decomposition import PLSRegression


def _fmt(v, casas=4):
    return f"{v:.{casas}f}"


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


def _rotulos(df, prefixo):
    if "Amostra" in df.columns:
        return [f"{prefixo}{str(v).strip()}" for v in df["Amostra"]]
    return [f"{prefixo}{int(i) + 1}" for i in df.index]


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
    """Variância acumulada explicada (%) em X e Y para k=1..n_lvs_max."""
    Xp, yp, _, _, _ = _preprocessar(
        X, y, centragem=centragem, autoescalonamento=autoescalonamento
    )
    yp2 = yp.reshape(-1, 1)

    ss_x = float(np.sum(Xp ** 2))
    ss_y = float(np.sum((yp2 - yp2.mean(axis=0)) ** 2))

    var_x, var_y = [], []
    for k in range(1, n_lvs_max + 1):
        pls = PLSRegression(n_components=k, scale=False).fit(Xp, yp2)

        X_rec = pls.x_scores_ @ pls.x_loadings_.T
        var_x.append(100.0 * float(np.sum(X_rec ** 2)) / ss_x if ss_x != 0 else 0.0)

        y_hat = pls.predict(Xp).reshape(-1, 1)
        ss_res = float(np.sum((yp2 - y_hat) ** 2))
        var_y.append(100.0 * (1.0 - ss_res / ss_y) if ss_y != 0 else 0.0)

    return np.array(var_x), np.array(var_y)


def figura_variancia_pls(var_x, var_y, n_lvs=None, titulo="PLS: variância explicada acumulada"):
    x = np.arange(1, len(var_x) + 1)
    fig, ax = plt.subplots(figsize=(6.5, 4))

    if n_lvs:
        ax.axvspan(0.5, n_lvs + 0.5, color="gray", alpha=0.12, label=f"{n_lvs} LV(s)")

    ax.plot(x, var_x, color="tab:blue", marker="o", linewidth=2, label="X (acumulada)")
    ax.plot(x, var_y, color="tab:red", marker="o", linewidth=2, label="Y (acumulada)")

    for xi, vx, vy in zip(x, var_x, var_y):
        ax.annotate(f"{vx:.1f}%", (xi, vx), ha="center", va="top", fontsize=7,
                    xytext=(0, -9), textcoords="offset points", color="tab:blue")
        ax.annotate(f"{vy:.1f}%", (xi, vy), ha="center", va="bottom", fontsize=7,
                    xytext=(0, 5), textcoords="offset points", color="tab:red")

    ax.set_xticks(x)
    ax.set_xlabel("Número de variáveis latentes (LVs)")
    ax.set_ylabel("Variância explicada acumulada (%)")
    ax.set_title(titulo)
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig


def _classificar_rpd(rpd):
    if rpd < 1.5:
        return "inadequado"
    if rpd < 2.0:
        return "triagem grosseira"
    if rpd < 2.5:
        return "quantificação aproximada"
    if rpd < 3.0:
        return "boa"
    return "excelente"


def _anotar(ax, xs, ys, labs, cor):
    for x, y, lab in zip(xs, ys, labs):
        ax.annotate(lab, (x, y), textcoords="offset points",
                    xytext=(4, 4), fontsize=6.5, color=cor)


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
    prefixo="",
):
    pref = f"{prefixo}_" if prefixo else ""

    cols, X, y = _dados_ajuste(
        df_xcalib, df_ycalib, df_xvalid, df_yvalid, elemento, agregar
    )

    n_max = max(1, min(X.shape[0] - 1, X.shape[1]))
    if not 1 <= n_lvs <= n_max:
        raise ValueError(f"n_lvs deve estar entre 1 e {n_max} (recebido: {n_lvs}).")

    arquivos = []

    # ---------- variância explicada ----------
    var_x, var_y = variancia_pls(
        X, y, n_max, centragem=centragem, autoescalonamento=autoescalonamento
    )

    nome_var = f"{pref}pls_{elemento}_variancia.png"
    subt = (
        f"{elemento} | agregar={'sim' if agregar else 'não'}, "
        f"centragem={centragem}, "
        f"autoescalonamento={'sim' if autoescalonamento else 'não'}"
    )
    fig = figura_variancia_pls(
        var_x, var_y, n_lvs=n_lvs,
        titulo=f"PLS: variância explicada acumulada\n{subt}",
    )
    fig.savefig(pasta_saida / nome_var, dpi=150, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(nome_var)

    # ---------- modelo final e previsões ----------
    Xp, yp, mx, my, sx = _preprocessar(X, y, centragem, autoescalonamento)
    pls = PLSRegression(n_components=n_lvs, scale=False).fit(Xp, yp.reshape(-1, 1))

    cols_idx = cols
    Xc = df_xcalib[cols_idx].to_numpy(dtype=float)
    Xv = df_xvalid[cols_idx].to_numpy(dtype=float)
    y_cal = df_ycalib[elemento].to_numpy(dtype=float)
    y_val = df_yvalid[elemento].to_numpy(dtype=float)  # valores certificados

    def prever(Xn):
        return pls.predict((Xn - mx) / sx).ravel() + my

    yh_cal = prever(Xc)
    yh_val = prever(Xv)

    res_cal = yh_cal - y_cal
    res_val = yh_val - y_val

    rot_cal = _rotulos(df_xcalib, "C")
    rot_val = _rotulos(df_xvalid, "V")

    n_fit = X.shape[0]
    n_val = len(y_val)

    # ---------- métricas ----------
    gl_c = max(n_fit - n_lvs - 1, 1)
    rmsec = float(np.sqrt(np.sum(res_cal ** 2) / gl_c))
    rmsep = float(np.sqrt(np.mean(res_val ** 2)))
    bias = float(np.mean(res_val))
    sep = float(np.std(res_val, ddof=1))
    sd_ref = float(np.std(y_val, ddof=1))
    rpd = sd_ref / sep if sep != 0 else float("inf")
    rpd_rmsep = sd_ref / rmsep if rmsep != 0 else float("inf")

    r2_cal = 1 - float(np.sum(res_cal ** 2)) / float(np.sum((y_cal - y_cal.mean()) ** 2))
    r2_val = 1 - float(np.sum(res_val ** 2)) / float(np.sum((y_val - y_val.mean()) ** 2))

    # ---------- exatidão / veracidade ----------
    erro_rel = res_val / y_val * 100.0
    recuperacao = yh_val / y_val * 100.0

    # teste t pareado do bias (H0: bias = 0)
    t_bias = bias / (sep / np.sqrt(n_val)) if sep != 0 else float("inf")
    t_crit_bias = float(stats.t.ppf(0.975, n_val - 1))
    bias_signif = abs(t_bias) > t_crit_bias

    # regressão previsto = a + b * certificado
    lr = stats.linregress(y_val, yh_val)
    b, a = float(lr.slope), float(lr.intercept)
    t_crit_reg = float(stats.t.ppf(0.975, n_val - 2))
    t_incl = (b - 1.0) / float(lr.stderr)
    t_int = a / float(lr.intercept_stderr)
    incl_signif = abs(t_incl) > t_crit_reg
    int_signif = abs(t_int) > t_crit_reg

    # ---------- gráfico: medido (certificado) vs previsto ----------
    nome_mp = f"{pref}pls_{elemento}_medido_previsto.png"
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.scatter(y_cal, yh_cal, marker="o", s=34, alpha=0.8,
               color="tab:blue", label="calibração")
    ax.scatter(y_val, yh_val, marker="x", s=62, linewidths=1.8,
               color="tab:red", label="validação")
    _anotar(ax, y_val, yh_val, rot_val, "tab:red")
    lo = float(min(y_cal.min(), y_val.min(), yh_cal.min(), yh_val.min()))
    hi = float(max(y_cal.max(), y_val.max(), yh_cal.max(), yh_val.max()))
    ax.plot([lo, hi], [lo, hi], color="black", lw=1.4, label="ideal (1:1)")
    xs = np.linspace(lo, hi, 100)
    ax.plot(xs, a + b * xs, color="tab:red", lw=1.2, ls="--",
            label=f"validação: Ŷ = {a:.3f} + {b:.3f}·Y")
    ax.set_xlabel(f"{elemento} certificado/medido (Y)")
    ax.set_ylabel(f"{elemento} previsto (Ŷ)")
    ax.set_title(f"PLS ({n_lvs} LVs): medido vs previsto - {elemento}")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(pasta_saida / nome_mp, dpi=150, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(nome_mp)

    # ---------- gráfico: resíduos ----------
    nome_res = f"{pref}pls_{elemento}_residuos.png"
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    ax1.scatter(yh_cal, res_cal, marker="o", s=34, alpha=0.8,
                color="tab:blue", label="calibração")
    ax1.scatter(yh_val, res_val, marker="x", s=62, linewidths=1.8,
                color="tab:red", label="validação")
    _anotar(ax1, yh_cal, res_cal, rot_cal, "tab:blue")
    _anotar(ax1, yh_val, res_val, rot_val, "tab:red")
    ax1.axhline(0, color="black", lw=1)
    ax1.set_xlabel(f"{elemento} previsto (Ŷ)")
    ax1.set_ylabel("Resíduo (Ŷ - Y)")
    ax1.set_title("Resíduos vs previsto")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.scatter(range(1, len(res_cal) + 1), res_cal, marker="o", s=34,
                alpha=0.8, color="tab:blue", label="calibração")
    ax2.scatter(range(1, len(res_val) + 1), res_val, marker="x", s=62,
                linewidths=1.8, color="tab:red", label="validação")
    ax2.axhline(0, color="black", lw=1)
    ax2.set_xlabel("Número da amostra (dentro do conjunto)")
    ax2.set_ylabel("Resíduo (Ŷ - Y)")
    ax2.set_title("Resíduos por amostra")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    fig.suptitle(f"PLS ({n_lvs} LVs): resíduos - {elemento}")
    fig.tight_layout()
    fig.savefig(pasta_saida / nome_res, dpi=150, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(nome_res)

    # ---------- tabelas ----------
    tab_var = {
        "titulo": "Variância explicada acumulada por LV",
        "colunas": ["LVs", "X acumulada (%)", "Y acumulada (%)"],
        "linhas": [[str(i + 1), f"{var_x[i]:.2f}", f"{var_y[i]:.2f}"] for i in range(n_max)],
    }

    tab_metricas = {
        "titulo": "Figuras de mérito do modelo PLS",
        "colunas": ["Métrica", "Valor"],
        "linhas": [
            ["R² (calibração)", _fmt(r2_cal)],
            ["R² (validação)", _fmt(r2_val)],
            ["RMSEC", _fmt(rmsec)],
            ["RMSEP", _fmt(rmsep)],
            ["Bias (validação)", _fmt(bias)],
            ["SEP", _fmt(sep)],
            ["DP dos valores certificados (validação)", _fmt(sd_ref)],
            ["RPD = DP / SEP", _fmt(rpd, 2)],
            ["RPD = DP / RMSEP", _fmt(rpd_rmsep, 2)],
        ],
    }

    tab_testes = {
        "titulo": "Testes de exatidão (95%)",
        "colunas": ["Teste", "Estatística t", "t crítico", "Conclusão"],
        "linhas": [
            ["Bias = 0", _fmt(t_bias, 3), _fmt(t_crit_bias, 3),
             "bias significativo" if bias_signif else "sem bias significativo"],
            ["Inclinação = 1", _fmt(t_incl, 3), _fmt(t_crit_reg, 3),
             "difere de 1" if incl_signif else "não difere de 1"],
            ["Intercepto = 0", _fmt(t_int, 3), _fmt(t_crit_reg, 3),
             "difere de 0" if int_signif else "não difere de 0"],
        ],
    }

    tab_exatidao = {
        "titulo": "Validação: certificado vs previsto",
        "colunas": ["Amostra", "Certificado", "Previsto", "Erro", "Erro rel. (%)", "Recuperação (%)"],
        "linhas": [
            [r, _fmt(c), _fmt(p), _fmt(e), _fmt(er, 2), _fmt(rec, 2)]
            for r, c, p, e, er, rec in zip(rot_val, y_val, yh_val, res_val, erro_rel, recuperacao)
        ],
    }

    tab_res_cal = {
        "titulo": "Resíduos: calibração",
        "colunas": ["Amostra", "Y", "Previsto", "Resíduo"],
        "linhas": [
            [r, _fmt(c), _fmt(p), _fmt(e)]
            for r, c, p, e in zip(rot_cal, y_cal, yh_cal, res_cal)
        ],
    }

    return {
        "elemento": elemento,
        "agregar": bool(agregar),
        "centragem": centragem,
        "autoescalonamento": bool(autoescalonamento),
        "n_lvs": int(n_lvs),
        "n_max": int(n_max),
        "n_amostras_ajuste": int(n_fit),
        "colunas": cols,
        "grafico_variancia": nome_var,
        "grafico_medido_previsto": nome_mp,
        "grafico_residuos": nome_res,
        "arquivos": arquivos,
        "var_x_acum": [round(float(v), 2) for v in var_x],
        "var_y_acum": [round(float(v), 2) for v in var_y],
        "r2_calib": _fmt(r2_cal),
        "r2_valid": _fmt(r2_val),
        "rmsec": _fmt(rmsec),
        "rmsep": _fmt(rmsep),
        "bias": _fmt(bias),
        "sep": _fmt(sep),
        "rpd": _fmt(rpd, 2),
        "rpd_classe": _classificar_rpd(rpd),
        "bias_signif": bool(bias_signif),
        "incl_signif": bool(incl_signif),
        "int_signif": bool(int_signif),
        "inclinacao_pv": _fmt(b),
        "intercepto_pv": _fmt(a),
        "tabelas": [tab_var, tab_metricas, tab_testes, tab_exatidao, tab_res_cal],
    }