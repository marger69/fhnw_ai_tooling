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
