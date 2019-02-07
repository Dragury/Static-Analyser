from staticanalyser.shared.platform_constants import GLOBAL_DATA_DIR, CONFIG_LOCATION, LANGS_DIR, MODEL_DIR
from os import path, mkdir


def setup() -> None:
    if not path.exists(GLOBAL_DATA_DIR):
        mkdir(GLOBAL_DATA_DIR)

        with open(path.join(path.dirname(__file__), "default_config.toml"), "r") as default_config_file:
            with open(CONFIG_LOCATION, "w") as global_config_file:
                global_config_file.writelines(default_config_file.readlines())
                print("written config!")

        mkdir(LANGS_DIR)
        mkdir(MODEL_DIR)


