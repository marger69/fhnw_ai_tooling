def normalize(values):
    total = sum(values)
    return [v / total for v in values]
