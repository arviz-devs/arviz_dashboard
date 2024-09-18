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
git clone https://github.com/arviz-devs/arviz_dashboard
cd arviz_dashboard
pip install --editable '.[dev,examples]'
```

Once the package has been installed, we need to install the `pre-commit` hooks used for maintaining
code hygiene. Run the following commands to set up the required `pre-commit` hooks for development.

```bash
pre-commit install
```

When you commit your changes to your branch, `pre-commit` will install the tools defined in the
config file, and check give feedback about required changes in order for the push to pass linting
and formatting tests.

If you add a new hook to the `.pre-commit-config.yaml` file, run the following command in order to
check if your hook is working against all the files.

```bash
pre-commit run --all-files
```

### Contributor installation test

TBD

```bash
pytest
```

## Usage

Dashboard usually includes multiple visualizations with different purposes. If you have any problems
with certain visualizations, you can find more explanations for the ArviZ visualizations in
[ArviZ](https://arviz-devs.github.io/arviz/examples/index.html) and
[Bayesian Modeling and Computation in Python](https://bayesiancomputationbook.com/welcome.html)

## Sponsors

[![NumFOCUS](https://www.numfocus.org/wp-content/uploads/2017/07/NumFocus_LRG.png)](https://numfocus.org)
