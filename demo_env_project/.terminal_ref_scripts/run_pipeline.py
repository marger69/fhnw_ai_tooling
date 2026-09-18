from myproject import evaluate, load_data, split_data, train_model

X, y = load_data()
X_train, X_test, y_train, y_test = split_data(X, y)
model = train_model(X_train, y_train)
metrics = evaluate(model, X_test, y_test)
print(metrics)
