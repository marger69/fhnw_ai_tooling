import argparse
import json
from pathlib import Path

import yaml

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
    metrics = evaluate(model, X_test, y_test)
    output_dir = args.output_dir or Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "config.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    print(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
