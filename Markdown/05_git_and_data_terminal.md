> **Terminal reference.** Companion to notebook 05. This version uses Git and shell utilities directly wherever possible.

# Module 5 - Git, Data/Artifact Versioning, and CI/CD

## 1. Initialize a repository and create a branch

```bash
mkdir -p demo_git_project && cd demo_git_project
git init
git switch -c feature/reproducibility
```

Configure an identity locally if needed:

```bash
git config user.name "Course Student"
git config user.email "student@example.invalid"
```

## 2. Create a tiny package and test

```bash
mkdir -p src/demo_ai tests data .github/workflows
cat > src/demo_ai/__init__.py <<'EOF_PY'
__version__ = "0.1.0"
EOF_PY

cat > src/demo_ai/pipeline.py <<'EOF_PY'
def normalize(values):
    total = sum(values)
    return [v / total for v in values]
EOF_PY

cat > tests/test_pipeline.py <<'EOF_PY'
from demo_ai.pipeline import normalize


def test_normalize_sums_to_one():
    assert abs(sum(normalize([1, 2, 3])) - 1.0) < 1e-12
EOF_PY
```

## 3. Identify a data artifact with a hash

Create a small dataset:

```bash
cat > data/training-v3.csv <<'EOF_CSV'
x1,x2,y
1,2,0
2,1,0
5,5,1
6,5,1
EOF_CSV
```

Compute its identity directly in the terminal:

```bash
sha256sum data/training-v3.csv
```

Store a simple manifest:

```bash
HASH=$(sha256sum data/training-v3.csv | awk '{print $1}')
printf 'name,path,sha256\ntraining-v3,data/training-v3.csv,%s\n' "$HASH" > data/manifest.csv
cat data/manifest.csv
```

### TODO 3.1

Append one row to the CSV and run `sha256sum` again. Why is the new hash useful even if the filename did not change?

## 4. Git workflow

```bash
git add .
git status --short
git commit -m "Add reproducible baseline project"
```

Make a small change:

```bash
printf '\n# TODO: add input validation\n' >> src/demo_ai/pipeline.py
git diff
git add src/demo_ai/pipeline.py
git commit -m "Document validation follow-up"
```

Useful review commands:

```bash
git status
git log --graph --oneline --decorate --all
git diff HEAD~1..HEAD
```

## 5. Pre-commit quality gates

```bash
cat > .pre-commit-config.yaml <<'EOF_PRE'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.13.1
    hooks:
      - id: ruff-check
      - id: ruff-format
EOF_PRE
```

Install and run:

```bash
conda run -n myproject pre-commit install
conda run -n myproject pre-commit run --all-files
```

## 6. CI/CD: create a GitHub Actions workflow

```bash
cat > .github/workflows/ci.yml <<'EOF_CI'
name: ci

on:
  push:
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: conda-incubator/setup-miniconda@v3
        with:
          activate-environment: myproject
          environment-file: environment.yml
          auto-activate-base: false
      - name: Lint
        shell: bash -el {0}
        run: ruff check .
      - name: Test
        shell: bash -el {0}
        run: PYTHONPATH=src pytest -q
      - name: Build
        shell: bash -el {0}
        run: python -m build
EOF_CI

cat .github/workflows/ci.yml
```

### TODO 6.1

Add a formatting check before tests:

```bash
# Add this command to the CI workflow:
ruff format --check .
```

Question: which failures should block a merge?

## 7. Git LFS: know when it applies

Track a model binary pattern:

```bash
git lfs install
git lfs track "*.pt"
cat .gitattributes
```

For very large datasets, prefer immutable object-storage snapshots/manifests rather than treating Git LFS as a universal data lake.

## 8. Secret hygiene

```bash
cat >> .gitignore <<'EOF_IGNORE'
.env
*.pem
*.key
wandb/
EOF_IGNORE

git grep -n -E 'API_KEY|TOKEN|PASSWORD|SECRET' || true
```

If a real secret was committed, **rotate the credential**; deleting the latest line is not sufficient.

## 9. Review checklist

```bash

  '[ ] code change is focused' \
  '[ ] tests updated' \
  '[ ] environment/dependencies updated intentionally' \
  '[ ] data/artifact identity recorded' \
  '[ ] no secrets committed' \
  '[ ] CI passes' \
  '[ ] build artifact can be produced'
```

**Take-away:** Git gives code identity and review history; data/model artifacts need their own identity strategy; CI makes the shared quality gate executable.
