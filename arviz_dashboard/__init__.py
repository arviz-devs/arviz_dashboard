"""Bayesian Dashboards built on top of Panel"""
__version__ = "0.0.1a"

from .elpd import dashboard_elpd
from .ppc import dashboard_ppc
from arviz_dashboard.marginal.one_d import posterior_marginal1d
from arviz_dashboard.trace.trace import trace
