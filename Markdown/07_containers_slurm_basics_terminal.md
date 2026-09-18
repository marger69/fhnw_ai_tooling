> **Terminal reference.** Companion to notebook 07. This exercise continues with the wheel produced in Module 4 under `demo_env_project/.terminal_ref_scripts`. Singularity is the main container example; Docker is shown only as a side comparison.

# Module 7 — Containers and Slurm Basics: Package the Real Wheel

By the end you can:

- install the Module 4 wheel in a container image;
- run the packaged `myproject` command with its real YAML configuration;
- bind a writable artifact directory into an otherwise immutable image;
- submit the same containerized command as a CPU-only Slurm job;
- distinguish image contents, runtime mounts, scheduler resources, and tracking services.

## 1. Reuse the Module 4 project boundary

Work from the project that produced the wheel:

```bash
PROJECT_DIR="$PWD/demo_env_project/.terminal_ref_scripts"
cd "$PROJECT_DIR"
mkdir -p containers logs artifacts/singularity artifacts/docker artifacts/slurm
```

Confirm that the package, configuration, and wheel exist:

```bash
test -f pyproject.toml
test -f configs/baseline.yaml
test -f dist/myproject-0.1.0-py3-none-any.whl
ls -lh dist/myproject-0.1.0-py3-none-any.whl
sha256sum dist/myproject-0.1.0-py3-none-any.whl
```

If the wheel is missing, build it from this directory using the active course environment:

```bash
python -m build
```

The package metadata defines the command used throughout this exercise:

```toml
[project.scripts]
myproject = "myproject.cli:main"
```

Check the required tools:

```bash
command -v singularity || echo "Singularity not available on this machine"
command -v docker || echo "Docker not available — side example only"
command -v sbatch || echo "Slurm client not available on this machine"
```

## 2. Create the Singularity definition

The build context is the Module 4 project root, so `%files` can copy the wheel from `dist/` and the configuration from `configs/`.

```bash
cat > containers/myproject.def <<'EOF_DEF'
Bootstrap: docker
From: python:3.12-slim

%labels
    org.opencontainers.image.title myproject
    org.opencontainers.image.version 0.1.0
    org.opencontainers.image.description "CAS notebook-to-package example"

%files
    dist/myproject-0.1.0-py3-none-any.whl /opt/myproject-0.1.0-py3-none-any.whl
    configs/baseline.yaml /app/configs/baseline.yaml

%post
    test -f /opt/myproject-0.1.0-py3-none-any.whl
    chmod 0755 /app /app/configs
    chmod 0644 /app/configs/baseline.yaml
    python -m pip install --no-cache-dir /opt/myproject-0.1.0-py3-none-any.whl

%environment
    export PYTHONUNBUFFERED=1

%runscript
    exec myproject "$@"

%test
    myproject --help
EOF_DEF

cat containers/myproject.def
```

The wheel is copied to `/opt`, not `/tmp`: Singularity can bind the host's temporary directory over the container's `/tmp` while `%post` runs, hiding files placed there by `%files`. The explicit `test -f` gives a clear failure if the build context does not contain the wheel. `%files` can preserve restrictive host permissions, so `%post` also makes the packaged configuration readable by the unprivileged user who runs the image. The wheel declares `PyYAML` and `scikit-learn` as dependencies, so `pip` installs them during the image build. The build machine therefore needs access to the configured Python package index.

### TODO 2.1 — Definition-file roles

Identify the purpose of `From`, `%files`, `%post`, `%environment`, `%runscript`, and `%test` directly in the file.

## 3. Obtain the SIF, then inspect it

Building a definition file is not an ordinary container run: Singularity needs one of the following build mechanisms:

- administrator-configured fakeroot;
- `proot` on `PATH` for a limited unprivileged build;
- an approved remote or privileged build service.

Check the current host before class:

```bash
singularity version
command -v proot || echo "proot is not installed"
ls -l /usr/bin/newuidmap /usr/bin/newgidmap 2>/dev/null || true
```

On the current course host, a plain build reports that `--remote`, `--fakeroot`, or `proot` is required. `--fakeroot` also fails because the installed `newuidmap` and `newgidmap` helpers are not root-owned. This is a host-administration issue; students cannot repair it from their Conda environments.

### Recommended classroom path: distribute a prebuilt SIF

Before class, build from `demo_env_project/.terminal_ref_scripts` on an approved build host where fakeroot is configured:

```bash
singularity build --fakeroot myproject-0.1.0.sif containers/myproject.def
sha256sum myproject-0.1.0.sif
```

An administrator with an approved privileged build host can instead run:

```bash
sudo singularity build myproject-0.1.0.sif containers/myproject.def
sha256sum myproject-0.1.0.sif
```

Copy `myproject-0.1.0.sif` into `demo_env_project/.terminal_ref_scripts` before the exercise. Students then begin with a non-destructive check:

```bash
PROJECT_DIR="$PWD/demo_env_project/.terminal_ref_scripts"
cd "$PROJECT_DIR"
test -f myproject-0.1.0.sif || {
  echo "Missing prebuilt myproject-0.1.0.sif — ask the instructor for the course image."
  return 1 2>/dev/null || exit 1
}
sha256sum myproject-0.1.0.sif
```

This makes the student exercise reproducible: everyone runs the same immutable image, while image construction remains an instructor/platform responsibility.

### Optional local path: `proot`

If the platform team provides `proot` on `PATH`, Singularity detects it automatically. This definition uses a Docker/OCI base and no `%pre` or `%setup` section, so it is suitable for trying the limited unprivileged builder:

```bash
command -v proot
singularity build myproject-0.1.0.sif containers/myproject.def
```

Do not add `--fakeroot` to that command. If `proot` is absent or the emulated build fails, use the prebuilt-image path.

### Optional platform path: repaired fakeroot

After the platform team has correctly installed and configured the UID/GID mapping helpers, a student can build with:

```bash
singularity build --fakeroot myproject-0.1.0.sif containers/myproject.def
```

Do not use a public remote builder for an internal wheel unless company policy explicitly permits uploading the definition, wheel, and build context.

Inspect the image and installed command:

```bash
singularity inspect myproject-0.1.0.sif
singularity exec myproject-0.1.0.sif python --version
singularity exec myproject-0.1.0.sif python -m pip show myproject
singularity run myproject-0.1.0.sif --help
```

## 4. Bind a writable output directory at runtime

The default config says `output_dir: artifacts/baseline`, but a SIF is immutable. Override that setting with a path backed by a writable host bind mount:

```bash
singularity run \
  --bind "$PWD/artifacts:/outputs" \
  myproject-0.1.0.sif \
  --config /app/configs/baseline.yaml \
  --output-dir /outputs/singularity
```

Inspect the files written on the host:

```bash
find artifacts/singularity -maxdepth 1 -type f -print
cat artifacts/singularity/metrics.json
cat artifacts/singularity/config.yaml
```

Expected files:

- `artifacts/singularity/metrics.json` contains the evaluation result;
- `artifacts/singularity/config.yaml` records the configuration used by the run.

The Iris dataset comes from scikit-learn inside the installed package, so this particular demonstration does not require an external data bind mount. A real project would normally bind large or sensitive input data read-only rather than copying it into the image.

### 5. Docker side example

Create an equivalent Docker image from the same wheel:

```bash
cat > containers/Dockerfile <<'EOF_DOCKER'
FROM python:3.12-slim

WORKDIR /app
COPY dist/myproject-0.1.0-py3-none-any.whl /tmp/myproject-0.1.0-py3-none-any.whl
RUN python -m pip install --no-cache-dir /tmp/myproject-0.1.0-py3-none-any.whl
COPY configs/baseline.yaml /app/configs/baseline.yaml
RUN chmod 0644 /app/configs/baseline.yaml

ENTRYPOINT ["myproject"]
EOF_DOCKER
```

If Docker is available, build and test from the project root:

```bash
docker build -f containers/Dockerfile -t myproject:0.1.0 .
docker run --rm myproject:0.1.0 --help
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD/artifacts:/outputs" \
  myproject:0.1.0 \
  --config /app/configs/baseline.yaml \
  --output-dir /outputs/docker
cat artifacts/docker/metrics.json
```

Singularity can also consume a published Docker/OCI image:

```bash
singularity build myproject-0.1.0.sif docker://registry.example.org/myproject:0.1.0
```

### TODO 5.1 — Translate the image recipe

Map Docker's `FROM`, `COPY`, `RUN`, and `ENTRYPOINT` to their Singularity definition-file concepts.

## 6. Slurm: the basic operational loop

Create a tiny CPU-only job first so the scheduler workflow is visible independently of the application:

```bash
cat > hello.slurm <<'EOF_SLURM'
#!/bin/bash
#SBATCH --job-name=hello-ai-tooling
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:02:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
hostname
date
sleep 10
echo "job finished"
EOF_SLURM
```

Submit and monitor:

```bash
JOBID=$(sbatch --parsable hello.slurm)
echo "$JOBID"
squeue -j "$JOBID"
```

After it completes:

```bash
sacct -j "$JOBID" --format=JobID,State,Elapsed,MaxRSS,AllocTRES
cat "logs/hello-ai-tooling-${JOBID}.out"
```

Cancel a running job when needed:

```bash
scancel "$JOBID"
```

## 7. Schedule the actual wheel with Slurm and Singularity

The packaged Iris example uses scikit-learn's CPU implementation. Requesting a GPU would waste a scarce resource and would not accelerate this workload.

```bash
cat > run_myproject.slurm <<'EOF_SLURM'
#!/bin/bash
#SBATCH --job-name=myproject
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"

singularity run \
  --bind "$SLURM_SUBMIT_DIR/artifacts:/outputs" \
  "$SLURM_SUBMIT_DIR/myproject-0.1.0.sif" \
  --config /app/configs/baseline.yaml \
  --output-dir "/outputs/slurm-${SLURM_JOB_ID}"
EOF_SLURM

cat run_myproject.slurm
```

Submit and monitor:

```bash
JOBID=$(sbatch --parsable run_myproject.slurm)
echo "submitted: $JOBID"
squeue -j "$JOBID"
```

Inspect the scheduler record, log, and application outputs after completion:

```bash
sacct -j "$JOBID" --format=JobID,State,Elapsed,MaxRSS,AllocTRES
cat "logs/myproject-${JOBID}.out"
cat "artifacts/slurm-${JOBID}/metrics.json"
cat "artifacts/slurm-${JOBID}/config.yaml"
```

### TODO 7.1 — Resource requests

Change one of `--cpus-per-task`, `--mem`, or `--time`. Explain how the request can affect scheduling latency and failure behavior.

### Optional GPU comparison

A GPU-enabled workload would additionally need a compatible GPU image and scheduler directives such as:

```bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
```

It would normally run with `singularity exec --nv ...`. Do not add these lines to `myproject`: neither the wheel nor scikit-learn's `LogisticRegression` uses CUDA.

## 9. Operational responsibilities

```bash
printf '%-15s %s\n' \
  'Wheel'       'versioned Python application and dependency metadata' \
  'Singularity' 'runtime filesystem and application environment' \
  'Slurm'       'resource allocation and scheduling' \
  'W&B'         'experiment metadata, metrics, artifacts, and lineage'
```

**Take-away:** the wheel defines the Python application; the SIF defines its immutable runtime; the bind mount preserves outputs; Slurm defines where and with which resources it runs; W&B records the experiment only when the application explicitly integrates it.
