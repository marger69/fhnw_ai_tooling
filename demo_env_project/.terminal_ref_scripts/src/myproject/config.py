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
