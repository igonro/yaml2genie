# yaml2genie

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat)](https://docs.astral.sh/ruff/)
[![uv](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FOnyx-Nostalgia%2Fuv%2Frefs%2Fheads%2Ffix%2Flogo-badge%2Fassets%2Fbadge%2Fv0.json&style=flat)](https://docs.astral.sh/uv/)
![Bitbucket Pipelines](https://img.shields.io/badge/CI-Bitbucket%20Pipelines-0052CC?style=flat&logo=bitbucket&logoColor=white)
[![License](https://img.shields.io/github/license/igonro/yaml2genie?style=flat)](LICENSE)
<!--
Once configured, add dynamic project badges such as:
![Coverage](https://img.shields.io/codecov/...)]
-->

> One-paragraph description of what this project does and who it's for.

---

## 🚀 Overview

Explanation of this project, motivation, etc.

### ✨ Project Features

* **Awesome Feature 1**: ...
* **Awesome Feature 2**: ...

---

## 🔧 Installation

```
# with pip
pip install git+https://github.com/igonro/genie2yaml

# with uv
uv tool install --from git+https://github.com/igonro/genie2yaml
```

Then run it:
```
genie2yaml ...
```

You can also run it directly without installation with uv:
```
uvx --from git+https://github.com/igonro/genie2yaml genie2yaml
```

<!-- Once we publish the package to Pypi replace with:
```
# with pip
pip install genie2yaml

# with uv
uv tool install genie2yaml
```

Then run it:
```
genie2yaml ...
```

You can also run it directly without installation with uv:
```
uvx genie2yaml
```
-->

---

## 🛠️ Getting Started: Local Environment Setup

Follow these steps to get the project running on your machine.

### 1. Prerequisites

Before you begin, make sure you have the following tools installed:

* **`uv`**: The package installer. If you don't have it, install it [here](https://docs.astral.sh/uv/getting-started/installation/).
* **`git`**: To clone the repository.
* **`make`**: To run the project's development commands.

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <REPOSITORY_URL>
    cd yaml2genie
    ```

2.  **Set up the project:**
    The Makefile creates the `.venv` environment, installs all development and test dependencies, and installs the `prek` Git hooks.
    ```bash
    make setup
    ```

    Activate the environment if you want commands available directly in your shell:
    ```bash
    # macOS / Linux
    source .venv/bin/activate

    # Windows
    .venv\Scripts\activate
    ```

3.  **Configure environment variables:**
    The project uses a `.env` file to manage secrets and local configurations.
    ```bash
    # Copy the example file to create your local configuration
    cp .env.example .env
    ```
    Open the `.env` file and fill in the necessary variables. **This file should never be committed to the repository** (it's already included in `.gitignore`).

You're all set! Your development environment is now fully configured.

---

## 💻 Development Workflow

### Makefile Commands

The Makefile provides the main commands for day-to-day development. Run `make help` to see the available targets.

```bash
# Run all configured prek hooks against every file
make check

# Run tests with coverage
make test

# Lint, format, or type-check the project
make lint
make format
make typecheck

# Check formatting without changing files
make format-check

# Build the package distributions
make build

# Remove generated artifacts and caches without touching .venv
make clean

# Upgrade dependencies and prek hook versions
make upgrade
```

Individual tools can also be run through the project environment, for example `uv run prek run --all-files` or `uv run ruff check .`.

---

## ⚙️ Continuous Integration (CI/CD)

This project uses **Bitbucket Pipelines** for automation. The configuration file is `bitbucket-pipelines.yaml`.

The pipeline is automatically triggered on every `push` to any branch and performs the following tasks:

1.  **Installs dependencies** in a clean environment.
2.  **Runs `ruff format --check`** to verify that the code is formatted.
3.  **Runs `ruff check`** to look for linting errors.
4.  **Runs `pytest`** to pass the entire test suite.

If any of these steps fail, the pipeline will fail, and you will be notified. This prevents broken or low-quality code from being merged into the main branch.
