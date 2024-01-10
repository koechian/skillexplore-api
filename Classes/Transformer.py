import pickle as pk


class TransformerModel:
    def __init__(self) -> None:
        with open(
            "/Users/koechian/Documents/skillexplore-api/Classes/model.pk", "rb"
        ) as raw:
            self.model = pk.load(raw)

    def predict(self, input):
        return self.model.predict(input)
