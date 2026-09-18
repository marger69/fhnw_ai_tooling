> **Terminal reference.** This is a terminal-oriented companion to the Jupyter notebook. Run every block in order in the same terminal. Each step extends one project; later steps reuse the files created earlier. The original notebook remains unchanged.

# Module 4 — From Notebook to Production-Ready Package

**Module of:** CAS Data Science · AI Tooling · FHNW
**Time budget:** 60 minutes

This is the spine of the day: take notebook-style code that works and turn it into a package that can be imported, tested, built, and run by someone else.

## Learning objectives

1. Identify notebook state, path, configuration, and reproducibility smells.
2. Extract pure functions and move them into a `src/` package.
3. Add a CLI and external configuration.
4. Add tests and structured logging.
5. Build a wheel and smoke-test it in a clean environment.

## 0. Create one cumulative working project

Start in a disposable course working directory. Run this block once; all later commands assume that the terminal remains inside `.terminal_ref_scripts`.

```bash
mkdir -p .terminal_ref_scripts
cd .terminal_ref_scripts
mkdir -p src/myproject tests configs artifacts
cat > README.md <<'MD'
# myproject

Classroom example for turning notebook-style code into an installable package.
MD
pwd
```

The project will grow in place:

```text
.terminal_ref_scripts/
├── README.md
├── pyproject.toml
├── configs/baseline.yaml
├── src/myproject/
│   ├── __init__.py
│   ├── pipeline.py
│   └── cli.py
├── tests/
└── artifacts/
```

## 1. The “before” notebook

Imagine one notebook that:

- reads data directly,
- mutates global variables across cells,
- trains a model,
- prints one metric,
- saves output in the current directory,
- only works when cells are run in yesterday's order.

That is a useful exploration artifact, not yet an operational artifact.

Create and run a deliberately notebook-like baseline:

```bash
cat > notebook_baseline.py <<'PY'
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
model = LogisticRegression(max_iter=300).fit(X_train, y_train)
print("accuracy", accuracy_score(y_test, model.predict(X_test)))
PY
conda run -n myproject python notebook_baseline.py
```

### TODO 1.1 — Find the smells

List at least five risks if this notebook became the only implementation used by a team. Think about state, importability, configuration, tests, output locations, logging, environment, and reproducibility.

## 2. Step 1 — Restart and run all

Before refactoring, prove the notebook is internally reproducible:

- start a fresh terminal/Python process,
- run the commands top-to-bottom,
- remove hidden dependencies on previous state,
- make randomness explicit.

A notebook that cannot restart cleanly is not ready to be extracted. The command above already starts a fresh Python process, so rerun it and confirm that the result is stable:

```bash
conda run -n myproject python notebook_baseline.py
```

## 3. Step 2 — Extract pure functions

Move the reusable logic into the package directory now. Later steps will import these same functions; they will not create disconnected copies.

```bash
cat > src/myproject/pipeline.py <<'PY'
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split


def load_data():
    return load_iris(return_X_y=True)


def split_data(X, y, *, seed: int = 42, test_size: float = 0.2):
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=seed,
        stratify=y,
    )


def train_model(X_train, y_train, *, C: float = 1.0, max_iter: int = 300):
    return LogisticRegression(C=C, max_iter=max_iter).fit(X_train, y_train)


def evaluate(model, X_test, y_test) -> dict[str, float]:
    accuracy = accuracy_score(y_test, model.predict(X_test))
    return {"accuracy": float(accuracy)}
PY

cat > src/myproject/__init__.py <<'PY'
from myproject.pipeline import evaluate, load_data, split_data, train_model

__all__ = ["evaluate", "load_data", "split_data", "train_model"]
PY

cat > run_pipeline.py <<'PY'
from myproject import evaluate, load_data, split_data, train_model

X, y = load_data()
X_train, X_test, y_train, y_test = split_data(X, y)
model = train_model(X_train, y_train)
metrics = evaluate(model, X_test, y_test)
print(metrics)
PY

PYTHONPATH=src conda run -n myproject python run_pipeline.py
```

`PYTHONPATH=src` is a temporary bridge: it proves that the extracted package can be imported before it is installed.

### TODO 3.1 — Change one parameter

Change one default in `pipeline.py` (`seed`, `test_size`, `C`, or `max_iter`), rerun `run_pipeline.py`, observe the effect, and then restore the original value.

## 4. Step 3 — Make it an installed package

Add package metadata and install the current directory into the Conda environment in editable mode:

```bash
cat > pyproject.toml <<'TOML'
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "myproject"
version = "0.1.0"
description = "Notebook-to-package classroom example"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "PyYAML>=6",
    "scikit-learn>=1.3",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
TOML

conda run -n myproject python -m pip install -e .
conda run -n myproject python -c "import myproject; print(myproject.__file__)"
conda run -n myproject python run_pipeline.py
```

The last command no longer needs `PYTHONPATH`: the editable installation connects the environment to `src/myproject/`.

## 5. Step 4 — Add a CLI entry point

A batch system needs a command, not a notebook UI. Create a real CLI that calls the reusable package functions:

```bash
cat > src/myproject/cli.py <<'PY'
import argparse

from myproject import evaluate, load_data, split_data, train_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myproject")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--C", type=float, default=1.0)
    parser.add_argument("--max-iter", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(
        X,
        y,
        seed=args.seed,
        test_size=args.test_size,
    )
    model = train_model(X_train, y_train, C=args.C, max_iter=args.max_iter)
    print(evaluate(model, X_test, y_test))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

cat >> pyproject.toml <<'TOML'

[project.scripts]
myproject = "myproject.cli:main"
TOML

# Metadata changed, so refresh the editable installation.
conda run -n myproject python -m pip install -e .
conda run -n myproject myproject --help
conda run -n myproject myproject --seed 42 --test-size 0.2
```

### TODO 5.1 — Add a flag

Add `parser.add_argument("--verbose", action="store_true")`, reinstall with `pip install -e .`, and confirm that `myproject --help` lists the new flag. Remove it again before continuing so the following blocks match the reference.

## 6. Step 5 — Externalize configuration

Create the configuration as a project file rather than a temporary file:

```bash
cat > configs/baseline.yaml <<'YAML'
split:
  seed: 42
  test_size: 0.2
model:
  C: 1.0
  max_iter: 300
output_dir: artifacts/baseline
YAML

cat > src/myproject/config.py <<'PY'
from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)

    if not 0 < config["split"]["test_size"] < 1:
        raise ValueError("split.test_size must be between 0 and 1")
    if config["model"]["C"] <= 0:
        raise ValueError("model.C must be positive")
    if config["model"]["max_iter"] <= 0:
        raise ValueError("model.max_iter must be positive")
    return config
PY

cat > src/myproject/cli.py <<'PY'
import argparse
from pathlib import Path

from myproject import evaluate, load_data, split_data, train_model
from myproject.config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myproject")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    split = config["split"]
    model_config = config["model"]

    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y, **split)
    model = train_model(X_train, y_train, **model_config)
    print(evaluate(model, X_test, y_test))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

conda run -n myproject myproject --config configs/baseline.yaml
```

Editable installation means ordinary `.py` changes are immediately visible; reinstall only when package metadata or entry points change.

### TODO 6.1 — Exercise validation

Temporarily change `test_size` in `configs/baseline.yaml` to `1.2`, run the CLI, observe the validation error, and then restore it to `0.2`.

## 7. Step 6 — Add tests

The tests import the installed package and exercise the same CLI used above:

```bash
cat > tests/test_pipeline.py <<'PY'
from myproject import evaluate, load_data, split_data, train_model


def test_split_is_deterministic_and_has_expected_sizes():
    X, y = load_data()
    first = split_data(X, y, seed=42, test_size=0.2)
    second = split_data(X, y, seed=42, test_size=0.2)

    assert (first[0] == second[0]).all()
    assert len(first[0]) == 120
    assert len(first[1]) == 30


def test_training_and_evaluation_contract():
    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)
    model = train_model(X_train, y_train)
    result = evaluate(model, X_test, y_test)

    assert hasattr(model, "coef_")
    assert set(result) == {"accuracy"}
    assert 0.0 <= result["accuracy"] <= 1.0
PY

cat > tests/test_cli.py <<'PY'
from myproject.cli import main


def test_cli_smoke_test(capsys):
    exit_code = main(["--config", "configs/baseline.yaml"])

    assert exit_code == 0
    assert "accuracy" in capsys.readouterr().out
PY

conda run -n myproject python -m pytest
```

Avoid testing scikit-learn itself. Test **your contract** around it.

### TODO 7.1 — Add one assertion

Add one more assertion about the train/test sizes or metric output, then rerun pytest.

## 8. Step 7 — Replace `print` with logging and explicit outputs

Use logs to explain execution, metrics for measured results, and artifacts for files produced by the run. Replace the CLI with its operational version:

```bash
cat > src/myproject/cli.py <<'PY'
import argparse
import json
import logging
import shutil
from pathlib import Path

from myproject import evaluate, load_data, split_data, train_model
from myproject.config import load_config

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myproject")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config = load_config(args.config)
    output_dir = args.output_dir or Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y, **config["split"])
    logger.info("training_started n_train=%d", len(y_train))
    model = train_model(X_train, y_train, **config["model"])
    metrics = evaluate(model, X_test, y_test)

    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(args.config, output_dir / "config.yaml")
    logger.info("run_finished output_dir=%s accuracy=%.3f", output_dir, metrics["accuracy"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > tests/test_cli.py <<'PY'
import json

from myproject.cli import main


def test_cli_writes_reproducible_run_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    exit_code = main(
        [
            "--config",
            "configs/baseline.yaml",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "config.yaml").is_file()
    metrics = json.loads((output_dir / "metrics.json").read_text())
    assert 0.0 <= metrics["accuracy"] <= 1.0
PY

conda run -n myproject myproject --config configs/baseline.yaml
conda run -n myproject python -m pytest
find artifacts/baseline -maxdepth 1 -type f -print
```

The distinction is now visible:

- **logs** explain execution in the terminal,
- **metrics** are stored in `metrics.json`,
- **artifacts** are collected under the configured output directory,
- the copied config records how the run was produced.

## 9. Final gate — Build what you intend to ship

A package that only works in editable mode may still be broken as a distributable artifact. Build it inside the Conda environment:

```bash
conda run -n myproject python -m pip install build
conda run -n myproject python -m build
```

Then smoke-test the wheel in a separate clean Conda environment:

```bash
conda create -n myproject-smoke python=3.12 -y
conda run -n myproject-smoke python -m pip install dist/*.whl
conda run -n myproject-smoke myproject --help
conda run -n myproject-smoke myproject --config configs/baseline.yaml --output-dir artifacts/smoke
```

After the demonstration, remove the temporary smoke environment:

```bash
conda env remove -n myproject-smoke -y
```

### Reflection

The goal was not “turn every notebook into microservices.” The goal was to create a clean seam:

**exploration notebook → reusable package → testable command → build artifact**

**Next:** Module 5 puts that package into a collaborative Git/data/CI workflow.
