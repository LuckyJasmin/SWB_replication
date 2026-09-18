"""
olstools.py — OLS with cluster-robust (CR1) standard errors.

Reproduces Stata's `regress y x..., vce(cluster id)`:
  - CR1 finite-sample adjustment  c = (G/(G-1)) * ((N-1)/(N-k))
  - cluster-robust ("sandwich") covariance matrix.

Provides:
  ols_cluster(y, X, cluster, colnames) -> (results_df, meta_dict)
  stars(p) -> significance stars
  show(results_df) -> pretty print
"""
import numpy as np
import pandas as pd
from scipy import stats


def ols_cluster(y, X, cluster, colnames=None):
    """
    OLS of y on X (X must already include a constant column if wanted),
    with CR1 cluster-robust standard errors clustered on `cluster`.

    Parameters
    ----------
    y : array-like, shape (N,)
    X : array-like, shape (N, k)   -- include a column of ones for an intercept
    cluster : array-like, shape (N,)  -- cluster identifier
    colnames : list of str, optional -- names for the k columns

    Returns
    -------
    results : pandas.DataFrame indexed by colnames with columns
              ['coef','se','t','p']
    meta : dict with 'N','G','k','r2','r2_adj'
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    N, k = X.shape
    cl = pd.Series(np.asarray(cluster)).reset_index(drop=True)
    uniq = pd.unique(cl)
    G = len(uniq)

    XtX = X.T @ X
    XtX_inv = np.linalg.inv(XtX)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta

    # cluster-robust "meat"
    meat = np.zeros((k, k))
    cl_arr = cl.values
    for g in uniq:
        idx = np.where(cl_arr == g)[0]
        Xg = X[idx]
        ug = resid[idx]
        sg = Xg.T @ ug
        meat += np.outer(sg, sg)

    # CR1 finite-sample correction (Stata default)
    c = (G / (G - 1.0)) * ((N - 1.0) / (N - k))
    V = c * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(V))

    tstat = beta / se
    # Stata uses t(G-1) for cluster-robust inference
    pval = 2 * stats.t.sf(np.abs(tstat), df=G - 1)

    # R-squared
    ss_tot = np.sum((y - y.mean()) ** 2)
    ss_res = np.sum(resid ** 2)
    r2 = 1 - ss_res / ss_tot
    r2_adj = 1 - (1 - r2) * (N - 1) / (N - k)

    if colnames is None:
        colnames = [f"x{i}" for i in range(k)]
    results = pd.DataFrame(
        {"coef": beta, "se": se, "t": tstat, "p": pval}, index=colnames
    )
    meta = {"N": N, "G": G, "k": k, "r2": r2, "r2_adj": r2_adj, "V": V}
    return results, meta


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


def show(results, meta=None, digits=3):
    df = results.copy()
    df["sig"] = df["p"].apply(stars)
    with pd.option_context("display.float_format", lambda v: f"{v:.{digits}f}"):
        print(df)
    if meta:
        print(f"N={meta['N']}  clusters={meta['G']}  R2={meta['r2']:.3f}")
