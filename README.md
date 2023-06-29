# ArviZ Dashboard

Exploratory analysis of Bayesian models with dashboards.

## Project Overview

This project brings dashboards to ArviZ enabling users to compare different visualizations in the
same view and interact with them.

## Installation

### Contributor installation

We will use `mamba` to create a virtual environment where we will install a development version of
ArviZ Dashboard. The first step is to follow the instructions here
[https://github.com/conda-forge/miniforge#mambaforge](https://github.com/conda-forge/miniforge#mambaforge)
to install the correct version of `mamba` for your operating system. **Note** that if you have
`conda` installed already, you can exchange the command `mamba` for `conda` with the same results.

```bash
mamba create --name arviz-dashboard pip python
mamba activate arviz-dashboard
```

Once the virtual environment has been created, and you have activated it with the above commands,
you can install the development requirements for `arviz_dashboard` with the following commands.

```bash
git clone the https://github.com/arviz-devs/arviz_dashboard
cd arviz_dashboard
pip install --editable .[dev,examples]
```

### Contributor installation test

TBD

```bash
pytest
```

## Usage

Dashboard usually includes multiple visualizations with different purposes. If you have any problems
with certain visualization, you can find more explanations for the ArviZ visualizations in
[ArvZ](https://arviz-devs.github.io/arviz/examples/index.html) and
[Bayesian Modeling and Computation in Python](https://bayesiancomputationbook.com/welcome.html)

## Sponsors

[![NumFOCUS](https://www.numfocus.org/wp-content/uploads/2017/07/NumFocus_LRG.png)](https://numfocus.org)
