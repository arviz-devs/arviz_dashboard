# Declarative Dashboard for Arviz

## Project Overview
This project intends to incorporate all sorts of ArviZ graphs in the dashboard as a separate Python library or ArviZ module which enable users compare different visualizations in the same view and interact with different visualizations at the same time. 

We have successfully implemented the first dashboard on ELPD and model comparison,which you can find in the `examples/elpd_dashboard.ipynb`. In the ear future, more dashboards will be added to this repo.

## Installation
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/yilinxia/arviz_dashboard/elpd_dashboard)

```
conda env create -f environment.yml
conda activate arviz_dashboard
jupyter lab
```

## Development
Please configure the environment in accordance with the installation procedure and it is also essential to become acquainted with the following materials:

### Dashboard Related
Currently, we implement our dashboard using Panel + Matplotlib / Bokeh, but it is still worth discussing whether we should try other frameworks.

- Dashboard Frameworks [Dashboard Frameworks](https://cdsdashboards.readthedocs.io/en/stable/chapters/userguide/frameworks.html)
- Dashboard Components [Panel Widgets](https://panel.holoviz.org/user_guide/Widgets.html)
- Dashboard Interaction [Panel Depends](https://panel.holoviz.org/user_guide/APIs.html) , [Panel Interact](https://panel.holoviz.org/user_guide/Interact.html), [Panel Link](https://panel.holoviz.org/user_guide/Links.html)
- Jupyter Widget [ipywidget](https://ipywidgets.readthedocs.io/en/stable/) 

We should think about transforming the entire dashboard into a template to process various inputs for future development. However, we haven't figured out how to achieve that and it would be advisable to attempt the following options.

- Containerize the whole dashboard as a class and different models with inference data as the input
- Derive ideas from [Panel Templates](https://panel.holoviz.org/user_guide/Templates.html)

Additionally, we need to consider how the dashboard will be shown. We currently have a dashboard embedded within a Jupyter lab (notebook). However, it is important to consider if the dashboard should be used as an extension to Jupyter or as a standalone website.

### ArviZ Dashboard

Implementing Dashboard is usually need-oriented. In other words, we should get familiar with the ArviZ visualizations and their purpose. It is highly recommended to read [Bayesian Modeling and Computation in Python](https://bayesiancomputationbook.com/welcome.html) and play with the code