from staticanalyser.shared.model import *
import staticanalyser.shared.config as config
import staticanalyser.translator.descriptor as descriptor
from argparse import Namespace
from os import path, getcwd
from _io import TextIOWrapper
import re


def lookup_parser(extension: str) -> str:
    return config.get_languages_by_extension(extension)


def get_file_extension(entity: TextIOWrapper) -> str:
    return re.split(r'\.', entity.name)[-1] # TODO compile regex pattern for better performance


def translate(translate_args: Namespace) -> int:
    extension_set: set = set()
    selected_parsers: set = set()

    f: TextIOWrapper
    for f in translate_args.input_files:
        extension: str = get_file_extension(f)
        extension_set.add(extension)
        selected_parsers = selected_parsers.union(set(lookup_parser(extension)))

    # TODO create file list to iterate through
    file_list: list = translate_args.input_files

    # TODO load descriptors
    for f in file_list:
        parser_options = lookup_parser(get_file_extension(f))
        if parser_options[0] is not None:
            selected_parser = descriptor.Descriptor(parser_options[0])
            selected_parser.parse(f)
            print("Using {} to translate {}".format(selected_parser, f.name))
        else:
            print("No parser found for {}".format(f.name))
    # TODO save models

    # TODO check against schema

    # TODO check current model
    return 0
