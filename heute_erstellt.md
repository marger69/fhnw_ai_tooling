# Heute erstellt

**Datum:** 18. September 2026

Heute wurden im Repository die folgenden Inhalte erstellt oder bearbeitet.

## Projektgrundlagen

- `README.md`
- `environment.yml`
- `conda-lock.yml`
- `demo_env_project/pyproject.toml`
- `demo_env_project/src/myproject/`
- `demo_env_project/tests/test_version.py`

## Kursdokumentation

- `Markdown/02_tools_environment_terminal.md`
- `Markdown/03_project_structure_terminal.md`
- `Markdown/04_notebook_to_package_terminal.md`
- `Markdown/05_git_and_data_terminal.md`
- `Markdown/06_experiment_tracking_terminal.md`
- `Markdown/07_containers_slurm_basics_terminal.md`

## Python-Beispielprojekt

Im Verzeichnis `demo_env_project/.terminal_ref_scripts/` wurden unter anderem erstellt:

- `README.md`
- `configs/baseline.yaml`
- `notebook_baseline.py`
- `run_pipeline.py`
- `pyproject.toml`
- `src/myproject/__init__.py`
- `src/myproject/cli.py`
- `src/myproject/config.py`
- `src/myproject/pipeline.py`
- `src/myproject.egg-info/` mit Paketmetadaten
- Python-Paketdateien (`.whl` und `.tar.gz`)

## Container und SLURM

- `containers/Dockerfile`
- `containers/myproject.def`
- `hello.slurm`
- `run_myproject.slurm`

Zusätzlich wurden Beispielkonfigurationen und Metriken für Docker und Singularity erstellt:

- `artifacts/docker/config.yaml`
- `artifacts/docker/metrics.json`
- `artifacts/singularity/config.yaml`
- `artifacts/singularity/metrics.json`

## Demo-Git-Projekt

Zeitweise erstellt wurden:

- `.github/workflows/ci.yml`
- `.pre-commit-config.yaml`
- `data/training-v3.csv`
- `src/demo_ai/__init__.py`
- `src/demo_ai/pipeline.py`
- `tests/test_pipeline.py`

Diese sechs Dateien wurden später am selben Tag wieder aus dem Repository entfernt.

## Git-Aufräumarbeiten

- `.gitignore` wurde erstellt.
- Generierte Singularity-Images (`*.sif`) werden künftig ignoriert.
- Der Git-Verlauf wurde bereinigt, damit das große Image nicht zu GitHub hochgeladen wird.

## Heutige Commits

1. Initiales Repository und Projektstruktur
2. Dokumentation zu Umgebung, Projekten, Notebooks, Git, Experiment-Tracking, Containern und SLURM
3. Aktualisierung der Paketmetadaten und Versionsnummer
4. Container-Definition und aktualisierte Terminalreferenz
5. Docker-/SLURM-Skripte sowie Experiment-Tracking-Artefakte
6. Entfernen nicht mehr benötigter Dateien
7. Ignorieren generierter Singularity-Images
