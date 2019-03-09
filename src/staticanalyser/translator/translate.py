from pathlib import Path

from staticanalyser.shared.model import *
import staticanalyser.shared.config as config
import staticanalyser.translator.descriptor as descriptor
from os import path, getcwd, environ, mkdir
from _io import TextIOWrapper
import re


def lookup_parser(extension: str) -> str:
    return config.get_languages_by_extension(extension)


def get_file_extension(entity: TextIOWrapper) -> str:
    return re.split(r'\.', entity.name)[-1]  # TODO compile regex pattern for better performance


def translate(input_files: list) -> int:
    extension_set: set = set()
    selected_parsers: set = set()

    local_dir_name: str = environ.get("LOCAL_DIR", default=None)
    local_dir: path = path.join(getcwd(), ".model")
    if local_dir_name:
        local_dir = path.abspath(local_dir_name)

    if not path.exists(local_dir):
        Path(local_dir).mkdir(parents=True, exist_ok=True)

    source_paths: list = environ.get("SOURCE_PATHS", default=getcwd()).split(";")
    if getcwd() not in source_paths:
        source_paths.append(getcwd())

    f: TextIOWrapper
    for f in input_files:
        extension: str = get_file_extension(f)
        extension_set.add(extension)
        selected_parsers = selected_parsers.union(set(lookup_parser(extension)))

    # TODO create file list to iterate through
    file_list: list = input_files

    # TODO load descriptors
    for f in file_list:
        parser_options = lookup_parser(get_file_extension(f))
        if parser_options[0] is not None:
            selected_parser = descriptor.Descriptor(parser_options[0])
            selected_parser.parse(f, get_file_extension(f), local_dir, source_paths)
            # print("Using {} to translate {}".format(selected_parser, f.name)) # TODO switch to python logger
        else:
            # print("No parser found for {}".format(f.name))
            pass

    # TODO check current model
    return 0
