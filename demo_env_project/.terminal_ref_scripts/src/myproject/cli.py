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
