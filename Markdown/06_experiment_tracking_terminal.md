> **Terminal reference.** This is a terminal-oriented companion to the Jupyter notebook. Run the blocks in order from the same disposable course working directory. Each Python file can run in a fresh process because shared paths and helpers live in one importable module. The original notebook remains unchanged.

# Notebook 06 — Weights & Biases online tracking, artifacts, and lineage

**Purpose.** Use W&B in online mode so runs, metrics, artifacts, and lineage are uploaded to the W&B web application and can be inspected during class.

By the end you can:

- authenticate with W&B without putting an API key in source code;
- start a W&B run in online mode;
- log configuration and metrics;
- record dataset and model identities;
- create dataset and model artifacts with input/output lineage;
- query completed runs through the W&B Public API;
- explain the lineage graph: dataset → training run → model.

> This exercise requires internet access, a W&B account, and the `wandb` package. Online mode sends run metadata and the small demonstration artifacts to W&B.

## 0. Install, authenticate, and create the shared setup

Install W&B if it is not already part of the `myproject` environment:

```bash
conda run -n myproject python -m pip install wandb
```

Authenticate interactively against the public W&B cloud. The explicit `--cloud` flag prevents a stale self-hosted or company-server setting from redirecting the login. Do not paste an API key into a Python file, notebook, shell script, or Git repository.

```bash
conda run --no-capture-output -n myproject wandb login --cloud --relogin --verify
unset WANDB_MODE
conda run -n myproject wandb online
conda run -n myproject python -c "import wandb; print(wandb.Settings().base_url)"
```

If your organization requires its own W&B deployment, use its approved URL instead of `--cloud`, for example `wandb login --host https://your-wandb-server.example.com --relogin --verify`. A `403` from a private deployment means that the account or API key is not authorized there; contact that deployment's administrator rather than bypassing the restriction.

`wandb online` clears a directory-level offline setting. Each run below also declares `mode="online"` explicitly. The default project is `aitooling-demo`. To log to a team entity, set it before running the remaining blocks:

```bash
export WANDB_PROJECT="aitooling-demo"
# Optional for a team account:
# export WANDB_ENTITY="your-team-name"
```

Create one shared module for paths, hashes, W&B settings, and persisted run references:

```bash
mkdir -p .terminal_ref_scripts
cat > .terminal_ref_scripts/wandb_demo_common.py <<'PY'
import hashlib
import json
import os
from pathlib import Path

WORK = Path("demo_wandb")
DATA = WORK / "data"
OUT = WORK / "outputs"
STATE = WORK / "state"

PROJECT = os.environ.get("WANDB_PROJECT", "aitooling-demo")
ENTITY = os.environ.get("WANDB_ENTITY") or None


def prepare_directories() -> None:
    for directory in (DATA, OUT, STATE):
        directory.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def wandb_init_kwargs() -> dict:
    settings = {"project": PROJECT, "mode": "online"}
    if ENTITY:
        settings["entity"] = ENTITY
    return settings


def save_run_reference(run, filename: str = "latest_run.json") -> dict:
    reference = {
        "entity": run.entity,
        "project": run.project,
        "id": run.id,
        "name": run.name,
        "url": run.url,
        "path": f"{run.entity}/{run.project}/{run.id}",
        "project_path": f"{run.entity}/{run.project}",
    }
    (STATE / filename).write_text(json.dumps(reference, indent=2) + "\n")
    return reference


def load_run_reference(filename: str = "latest_run.json") -> dict:
    return json.loads((STATE / filename).read_text())


prepare_directories()
PY

cat > .terminal_ref_scripts/06_experiment_tracking_terminal_01.py <<'PY'
from wandb_demo_common import DATA, ENTITY, OUT, PROJECT, STATE, WORK

print("work directory:", WORK.resolve())
print("data directory:", DATA.resolve())
print("output directory:", OUT.resolve())
print("state directory:", STATE.resolve())
print("W&B project:", PROJECT)
print("W&B entity:", ENTITY or "account default")
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_01.py
```

The run should also be traceable to the Conda environment used to execute it. In a real project, log the hash or version of `conda-lock.yml` alongside the code and data identities.

## 1. Create a small dataset and identity record

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_02.py <<'PY'
import json

from wandb_demo_common import DATA, sha256

dataset = DATA / "training-v3.csv"
dataset.write_text("x1,x2,y\n1,2,0\n2,1,0\n5,5,1\n6,5,1\n")

data_id = {
    "name": "training-v3",
    "sha256": sha256(dataset),
    "path": str(dataset),
}
(DATA / "training-v3.identity.json").write_text(json.dumps(data_id, indent=2) + "\n")
print(json.dumps(data_id, indent=2))
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_02.py
```

## 2. Start W&B runs in online mode

First, verify that the SDK can authenticate with the W&B server:

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_03.py <<'PY'
import wandb

from wandb_demo_common import ENTITY, PROJECT

if not wandb.login(verify=True):
    raise RuntimeError("W&B authentication failed. Run: wandb login")

print("W&B SDK version:", wandb.__version__)
print("online destination:", f"{ENTITY or 'account default'}/{PROJECT}")
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_03.py
```

Create the baseline run. Because the run uses a context manager, it is finished and uploaded before the script exits.

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_04.py <<'PY'
import json

import wandb

from wandb_demo_common import DATA, save_run_reference, wandb_init_kwargs

data_id = json.loads((DATA / "training-v3.identity.json").read_text())
config = {"model": "toy-threshold", "threshold": 3.5, "seed": 42}

with wandb.init(
    **wandb_init_kwargs(),
    config=config,
    name="baseline-threshold",
    tags=["online", "classroom"],
    job_type="evaluation",
) as run:
    run.summary["dataset_name"] = data_id["name"]
    run.summary["dataset_sha256"] = data_id["sha256"]
    run.log({"train_acc": 0.75, "val_acc": 0.70})
    reference = save_run_reference(run, "baseline_run.json")
    print("run id:", run.id)
    print("run URL:", run.url)

print("saved reference:", reference["path"])
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_04.py
```

Open the printed URL and locate the configuration, summary, metrics, and tags.

### TODO 6.1 — Compare two online runs

Change the threshold value, create a second run, and compare the two run configurations and metrics in the W&B project.

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_05.py <<'PY'
import json

import wandb

from wandb_demo_common import DATA, save_run_reference, wandb_init_kwargs

data_id = json.loads((DATA / "training-v3.identity.json").read_text())
baseline_threshold = 3.5
config = {
    "model": "toy-threshold",
    "threshold": 4.5,  # TODO 6.1: try 2.5 instead.
    "seed": 42,
}
val_acc = 0.80 if config["threshold"] > baseline_threshold else 0.68

with wandb.init(
    **wandb_init_kwargs(),
    config=config,
    name="comparison-threshold",
    tags=["online", "comparison"],
    job_type="evaluation",
) as run:
    run.summary["dataset_name"] = data_id["name"]
    run.summary["dataset_sha256"] = data_id["sha256"]
    run.log({"val_acc": val_acc})
    reference = save_run_reference(run, "comparison_run.json")
    print("run URL:", run.url)

print("Compare fairly using: dataset hash + config + evaluation definition + metric.")
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_05.py
```

## 3. Log artifacts with real input/output lineage

Create a tiny model file and record its content hash:

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_06.py <<'PY'
import pickle

from wandb_demo_common import OUT, sha256

model_path = OUT / "model.pkl"
with model_path.open("wb") as stream:
    pickle.dump({"kind": "toy-threshold", "threshold": 3.5}, stream)

print("model:", model_path)
print("sha256:", sha256(model_path))
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_06.py
```

The first run publishes the dataset artifact. The second run explicitly consumes that dataset and produces the model artifact. This creates the lineage edge `dataset → training run → model`.

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_07.py <<'PY'
import json

import wandb

from wandb_demo_common import DATA, OUT, save_run_reference, sha256, wandb_init_kwargs

dataset = DATA / "training-v3.csv"
model_path = OUT / "model.pkl"
data_id = json.loads((DATA / "training-v3.identity.json").read_text())
config = {"model": "toy-threshold", "threshold": 3.5, "seed": 42}

with wandb.init(
    **wandb_init_kwargs(),
    name="publish-training-data",
    tags=["online", "artifact-demo"],
    job_type="data-preparation",
) as data_run:
    dataset_artifact = wandb.Artifact(
        "training-v3",
        type="dataset",
        metadata=data_id,
    )
    dataset_artifact.add_file(str(dataset))
    logged_dataset = data_run.log_artifact(dataset_artifact)
    logged_dataset.wait()
    dataset_version = logged_dataset.version
    print("dataset artifact:", f"training-v3:{dataset_version}")
    print("data run URL:", data_run.url)

with wandb.init(
    **wandb_init_kwargs(),
    config=config,
    name="train-from-versioned-data",
    tags=["online", "artifact-demo"],
    job_type="training",
) as training_run:
    training_run.use_artifact(f"training-v3:{dataset_version}")

    model_artifact = wandb.Artifact(
        "toy-threshold",
        type="model",
        metadata={"model_sha256": sha256(model_path)},
    )
    model_artifact.add_file(str(model_path))
    logged_model = training_run.log_artifact(model_artifact)
    logged_model.wait()
    training_run.log({"val_acc": 0.70})

    reference = save_run_reference(training_run)
    print("model artifact:", f"toy-threshold:{logged_model.version}")
    print("training run URL:", training_run.url)

print("saved lineage run:", reference["path"])
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_07.py
```

Open the training run URL, select its Artifacts or Lineage view, and identify the consumed dataset and produced model.

## 4. Inspect online runs through the Public API

List the five newest runs in the project. This reads data back from the W&B server rather than inspecting local offline folders.

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_08.py <<'PY'
from itertools import islice

import wandb

from wandb_demo_common import load_run_reference

reference = load_run_reference()
api = wandb.Api()
runs = api.runs(reference["project_path"], order="-created_at", per_page=5)

print("project:", reference["project_path"])
for run in islice(runs, 5):
    print(
        run.id,
        run.name,
        run.state,
        "val_acc=", run.summary.get("val_acc"),
        run.url,
    )
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_08.py
```

### TODO 6.2 — Inspect the lineage programmatically

Fetch the exact training run saved in step 3 and inspect its configuration, summary, consumed artifacts, and produced artifacts:

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_09.py <<'PY'
import json

import wandb

from wandb_demo_common import load_run_reference

reference = load_run_reference()
run = wandb.Api().run(reference["path"])

config = {key: value for key, value in run.config.items() if not key.startswith("_")}
summary = {
    key: value
    for key, value in run.summary._json_dict.items()
    if not key.startswith("_")
}

print("run URL:", run.url)
print("config:", json.dumps(config, indent=2))
print("summary:", json.dumps(summary, indent=2))
print("consumed artifacts:")
for artifact in run.used_artifacts():
    print(" -", artifact.name, artifact.type)
print("produced artifacts:")
for artifact in run.logged_artifacts():
    print(" -", artifact.name, artifact.type)


conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_09.py
```

## 5. Optional online sweep

This creates a sweep definition in the same online W&B project. It does not start agents or training runs.

```bash
cat > .terminal_ref_scripts/06_experiment_tracking_terminal_10.py <<'PY'
import wandb

from wandb_demo_common import ENTITY, PROJECT

sweep_config = {
    "method": "grid",
    "metric": {"name": "val_acc", "goal": "maximize"},
    "parameters": {
        "threshold": {"values": [2.5, 3.5, 4.5]},
        "seed": {"values": [1, 2]},
    },
}

sweep_id = wandb.sweep(sweep=sweep_config, project=PROJECT, entity=ENTITY)
print("created online sweep:", sweep_id)
print("No agent was started, so this step creates no sweep runs.")
PY

conda run -n myproject python .terminal_ref_scripts/06_experiment_tracking_terminal_10.py
```

## Reflection

If you only save `model.pkl`, which parts of the reproducibility contract are missing?

How does online tracking change the privacy and data-governance questions you must answer before logging real project data?

## Reference

- [W&amp;B login](https://docs.wandb.ai/models/ref/python/functions/login)
- [W&amp;B online mode](https://docs.wandb.ai/models/ref/cli/wandb-online)
- [Create and log artifacts](https://docs.wandb.ai/models/artifacts/construct-an-artifact)
- [Query runs with the Public API](https://docs.wandb.ai/models/ref/python/public-api/api)
