from pathlib import Path
import _queue
import staticanalyser.shared.config as config
import staticanalyser.translator.descriptor as descriptor
from os import path, getcwd, environ
import multiprocessing as mp
import re


def lookup_parser(extension: str) -> list:
    return config.get_languages_by_extension(extension)


def get_file_extension(entity: str) -> str:
    return re.split(r'\.', entity)[-1]  # TODO compile regex pattern for better performance


def parse(file_queue: mp.Queue, local_dir, source_paths):
    try:
        file = file_queue.get_nowait()
        while file is not None:
            parser_options = lookup_parser(get_file_extension(file))
            if parser_options[0] is not None:
                selected_parser = descriptor.Descriptor(parser_options[0])
                selected_parser.parse(file, get_file_extension(file), local_dir, source_paths)
            file = file_queue.get_nowait()
    except _queue.Empty:
        pass


def translate(input_files: list, options: dict) -> int:
    extension_set: set = set()
    selected_parsers: set = set()

    local_dir_name: str = environ.get("LOCAL_DIR", default=None)
    local_dir: path = path.join(getcwd(), ".model")
    if local_dir_name:
        local_dir = path.abspath(local_dir_name)

    if not path.exists(local_dir):
        Path(local_dir).mkdir(parents=True, exist_ok=True)

    number_of_processes = options.get("jobs")

    source_paths: list = environ.get("SOURCE_PATHS", default=getcwd()).split(";")
    if getcwd() not in source_paths:
        source_paths.append(getcwd())


    # TODO create file list to iterate through
    file_list: list = input_files
    file_queue: mp.Queue = mp.Queue()
    for file in file_list:
        file_queue.put(file)

    processes: list = []
    for pid in range(number_of_processes):
        process = mp.Process(target=parse, args=(file_queue, local_dir, source_paths))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    # TODO load descriptors
    # for f in file_list:
    #     parser_options = lookup_parser(get_file_extension(f))
    #     if parser_options[0] is not None:
    #         selected_parser = descriptor.Descriptor(parser_options[0])
    #         selected_parser.parse(f, get_file_extension(f), local_dir, source_paths)
    #         # print("Using {} to translate {}".format(selected_parser, f.name)) # TODO switch to python logger
    #     else:
    #         # print("No parser found for {}".format(f.name))
    #         pass

    # TODO check current model
    return 0
