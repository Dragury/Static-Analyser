from pathlib import Path

import toml
import sys
from staticanalyser.shared.platform_constants import LANGS_DIR

_CONFIG_ITEMS = {
    "languages": [],
    "filetypes": {},
    "source_dirs": {}
}
__all__ = ['get_languages', 'get_languages_by_extension', 'get_filetypes', 'get_file_extensions']

langs_dir = Path(LANGS_DIR)
for file in langs_dir.iterdir():
    with open(str(file), "r") as lang_file:

        lang_info: dict = toml.load(lang_file).get("info")
        if lang_info:
            _CONFIG_ITEMS.get("languages").append(lang_info.get("name"))
            for extension in lang_info.get("file_extensions"):
                if extension not in _CONFIG_ITEMS.get("filetypes").keys():
                    _CONFIG_ITEMS.get("filetypes")[extension] = [lang_info.get("name")]
                else:
                    _CONFIG_ITEMS.get("filetypes").get(extension).append(lang_info.get("name"))
            _CONFIG_ITEMS.get("source_dirs")[lang_info.get("name")] = lang_info.get("global_sources")


# CONFIG SUBFUNCTIONS
# I've decided this is the best way to be retreiving config items since it means the IDE will catch any typos
# and every config item that can be exposed to the code has to be done so programmatically. Using the sub functions
# to get the calling function name and using this to find the dictionary key makes expanding the available config
# items easier since it requires a single line of code that doesn't change between functions
def _get_config_item_from_dict(item_key):
    return _CONFIG_ITEMS[item_key]


def _get_config_item():
    config_key = sys._getframe(1).f_code.co_name[4:]
    return _get_config_item_from_dict(config_key)


# CONFIG SUBFUNCTIONS END


# START OF CONFIG OPTIONS
def get_languages() -> object:
    return _get_config_item()


def get_languages_by_extension(extension: str) -> list:
    languages: dict = get_filetypes()
    if extension in languages.keys():
        return languages.get(extension)
    else:
        return [None]


def get_filetypes() -> dict:
    return _get_config_item()


def get_file_extensions() -> list:
    return list(get_filetypes().keys())


def get_source_dirs() -> dict:
    return _get_config_item()


def get_language_source_dirs(lang: str) -> dict:
    return get_source_dirs().get(lang) or []
