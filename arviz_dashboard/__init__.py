"""Bayesian Dashboards built on top of Panel"""
import importlib.metadata

from arviz_dashboard.elpd import dashboard_elpd
from arviz_dashboard.marginal.one_d import posterior_marginal1d

__version__ = importlib.metadata.version(__package__ or __name__)
