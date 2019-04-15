from typing import Dict, Union
from os import path
from staticanalyser.shared.model import *


class Navigator:
    _loaded_models: Dict[str, Union[Dict[str, Union[
        DependencyModel,
        FunctionModel,
        ClassModel
    ]], str]] = None

    def __init__(self):
        self._loaded_models = {}

    def lookup_entity(self, global_id: str):
        # TODO find entity in loaded model
        # Otherwise load it!
        self.load_entity(global_id)

    def load_entity(self, global_id: str):
        # TODO differentiate between builtins and source files
        model_file = ModelOperations.get_model_file(global_id)
        with open(model_file, "r") as fp:
            model_data:dict = json.load(fp)
        model: dict = {"classes": [], "functions": [], "dependencies": []}
        for klazz in model_data.get("classes"):
            c = ModelOperations.load_model_from_dict(klazz)
            model["classes"].append(c)
        for func in model_data.get("functions"):
            f = ModelOperations.load_model_from_dict(func)
            model["functions"].append(f)
        for dependency in model_data.get("dependencies"):
            d = ModelOperations.load_model_from_dict(dependency)
            model["dependencies"].append(d)
        self._loaded_models[ModelOperations.get_base_global_id(global_id)] = model

    def __str__(self):
        return str(self._loaded_models)


def navigate(global_id):
    n = Navigator()
    n.load_entity(global_id)
    print(n)
