
class ModelList(list):
    def __getitem__(self, index):
        item = super().__getitem__(index)

        if type(item) is dict:
            return Model(item)

        elif type(item) is list:
            return ModelList(item)

        else:
            return item


class Model(dict):

    def __getattr__(self, name):
        item = self[name]

        if type(item) is dict:
            return Model(item)

        elif type(item) is list:
            return ModelList(item)

        else:
            return item