from staticanalyser.shared.model import *
import staticanalyser.shared.config as config
from argparse import Namespace
from os import path, getcwd
from _io import TextIOWrapper
import re


def lookup_parser(extension: str) -> str:
    return config.get_languages_by_extension(extension)


def get_file_extension(entity: TextIOWrapper) -> str:
    return re.split(r'\.', entity.name)[-1] # TODO compile regex pattern for better performance


def translate(translate_args: Namespace) -> int:
    # TODO lookup filetypes
    extension_set: set = set()
    selected_parsers: set = set()

    entity: TextIOWrapper
    for entity in translate_args.input_files:
        extension: str = get_file_extension(entity)
        extension_set.add(extension)
        for parser in lookup_parser(extension):
            selected_parsers.add(parser)


    # TODO check current model
    return 0
