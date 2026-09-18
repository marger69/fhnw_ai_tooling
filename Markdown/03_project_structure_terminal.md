> **Terminal reference.** Companion to notebook 03. The emphasis here is filesystem structure and documentation, so nearly everything can be done with standard shell commands.

# Module 3 - Project Structure and Documentation

## 1. Create the baseline repository layout

```bash
mkdir -p demo_structure_project/{src/myproject,tests,configs,notebooks,data,artifacts,docs/adr}
cd demo_structure_project
touch src/myproject/__init__.py
```

Inspect it:

```bash
find . -maxdepth 3 -type d -o -type f | sort
```

A useful baseline is:

```text
.
├── environment.yml
├── conda-lock.yml
├── pyproject.toml
├── README.md
├── src/myproject/
├── tests/
├── configs/
├── notebooks/
├── data/
├── artifacts/
└── docs/adr/
```

## 2. README = runbook

```bash
cat > README.md <<'EOF_README'
# demo-structure-project

Small AI-tooling teaching repository.

## Quickstart
1. `conda-lock install -n myproject conda-lock.yml`
2. `conda run -n myproject pytest`
3. `conda run -n myproject myproject --config configs/baseline.yaml`

## Outputs
Generated artifacts go under `artifacts/` and are not committed by default.
EOF_README

cat README.md
```

## 3. Add an ADR

```bash
cat > docs/adr/0001-src-layout.md <<'EOF_ADR'
# ADR-0001: Use a src/ layout

**Status:** Accepted

**Context:** We want tests and notebooks to import the installed package rather than local sibling files.

**Decision:** Put reusable Python code under `src/myproject/`.

**Consequences:** The package must be installed before import, which exposes packaging mistakes earlier.
EOF_ADR

cat docs/adr/0001-src-layout.md
```

## 4. Configuration hierarchy

```bash
cat > configs/baseline.yaml <<'EOF_CFG'
seed: 42
model:
  type: baseline
  learning_rate: 0.001
output_dir: artifacts/baseline
EOF_CFG

cat configs/baseline.yaml
```

The conceptual precedence is:

```text
safe defaults in Git
      ↓
experiment config
      ↓
CLI overrides
      ↓
environment/deployment overrides
      ↓
secrets injected separately
```

## 5. Data and artifact policy

Document rather than commit large/generated content:

```bash
cat > data/README.md <<'EOF_DATA'
# Data

Raw data are stored outside Git.
Each training run must reference an immutable dataset identifier or manifest.
EOF_DATA

cat > artifacts/README.md <<'EOF_ART'
# Artifacts

Generated models, reports, plots, and temporary outputs belong here locally.
Production artifacts should be stored in an artifact/object store and referenced by identity.
EOF_ART
```

Add ignore rules:

```bash
cat > .gitignore <<'EOF_IGNORE'
.env
__pycache__/
.pytest_cache/
.ruff_cache/
artifacts/*
!artifacts/README.md
data/*
!data/README.md
EOF_IGNORE
```

Check what Git would see:

```bash
git init
git status --short
```

## 6. Structure sanity check

```bash
for p in README.md src/myproject tests configs notebooks data artifacts docs/adr; do
  test -e "$p" && echo "OK   $p" || echo "MISS $p"
done
```

**Take-away:** project structure is a communication mechanism. A collaborator should know where code, configuration, tests, data references, and generated artifacts belong without asking you.
