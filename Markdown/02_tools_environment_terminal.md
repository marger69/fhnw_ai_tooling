> **Terminal reference.** Companion to notebook 02. Run the Bash blocks in order. The notebook remains unchanged.

# Module 2 - Reproducible Environments and Python Tooling

**Course:** CAS Data Science - AI Tooling - FHNW
**Time:** ~50 min

## Learning objectives

- Use Conda as the environment contract.
- Separate `environment.yml`, `conda-lock.yml`, `pyproject.toml`, and the runtime image.
- Run quality tools from the terminal.
- Keep secrets outside version control.

## 1. Verify the tools

```bash
conda --version
command -v conda
command -v conda-lock || echo "conda-lock not installed yet"
```

If needed:

```bash
conda install -n base -c conda-forge conda-lock
```

## 2. Create a small project

```bash
mkdir -p demo_env_project/src/myproject demo_env_project/tests
cd demo_env_project
```

Create the environment specification:

```bash
cat > environment.yml <<'EOF_ENV'
name: myproject
channels:
  - conda-forge
dependencies:
  - python=3.12
  - numpy
  - pandas
  - scikit-learn
  - pyyaml
  - pip
  - pip:
      - pytest
      - ruff
      - build
EOF_ENV
```

Create package/tool configuration:

```bash
cat > pyproject.toml <<'EOF_TOML'
[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
EOF_TOML

printf '__version__ = "0.1.0"\n' > src/myproject/__init__.py
```

Inspect them:

```bash
cat environment.yml
cat pyproject.toml
```

### TODO 2.1

Change **one** version constraint in `environment.yml` and explain whether that is an environment concern or a package concern.

## 3. Lock the environment

Pick the platform used in class, for example Linux:

```bash
conda-lock -f environment.yml -p linux-64
ls -lh conda-lock.yml
```

Create the locked environment:

```bash
conda-lock install -n myproject conda-lock.yml
conda list -n myproject
```

Check one package without entering Python:

```bash
conda list -n myproject scikit-learn
```

## 4. Run quality tools directly

Create a tiny test:

```bash
cat > tests/test_version.py <<'EOF_PY'
from myproject import __version__


def test_version():
    assert __version__ == "0.1.0"
EOF_PY
```

Run the tools:

```bash
conda run -n myproject ruff check .
conda run -n myproject ruff format --check .
PYTHONPATH=src conda run -n myproject pytest
```

## 5. Conda can manage native dependencies too

Add a native tool to the environment specification:

```bash
sed -n '1,30p' environment.yml
```

For example, add `ffmpeg` under `dependencies`, then re-lock:

```bash
conda-lock -f environment.yml -p linux-64
```

Check whether it is in the environment:

```bash
conda list -n myproject ffmpeg
```

## 6. Configuration is not secrets

Safe configuration can be committed:

```bash
mkdir -p configs
cat > configs/base.yaml <<'EOF_CFG'
seed: 42
model: baseline
output_dir: outputs
EOF_CFG
```

Secrets should come from the environment or a secret store:

```bash
export WANDB_API_KEY="example"
printenv WANDB_API_KEY | sed 's/./*/g'
unset WANDB_API_KEY
```

Add common secret/local files to `.gitignore`:

```bash
cat >> .gitignore <<'EOF_GITIGNORE'
.env
*.key
outputs/
wandb/
EOF_GITIGNORE
```

## 7. Reproducibility layers

Use the terminal to identify the files representing each layer:

```bash
printf '%-22s %s\n' \
  "Environment intent" "environment.yml" \
  "Exact resolution" "conda-lock.yml" \
  "Python package" "pyproject.toml" \
  "Runtime boundary" "Singularity .sif (Module 7)"
```

**Take-away:** Conda defines the development/runtime dependencies; `pyproject.toml` defines the installable Python package; Singularity later captures the OS/runtime boundary.
