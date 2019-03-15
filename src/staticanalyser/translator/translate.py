from pathlib import Path
import queue
import staticanalyser.shared.config as config
import staticanalyser.translator.descriptor as descriptor
from staticanalyser.shared.platform_constants import MODEL_DIR
from os import path, getcwd, name
import multiprocessing as mp
import re


def lookup_parser(extension: str) -> list:
    return config.get_languages_by_extension(extension)


def get_file_extension(entity: str) -> str:
    return re.split(r'\.', str(entity))[-1]  # TODO compile regex pattern for better performance


def parse(file_queue: mp.Queue, local_dir, source_paths, force):
    try:
        file = file_queue.get_nowait()
        while file is not None:
            parser_options = lookup_parser(get_file_extension(file))
            if parser_options[0] is not None:
                selected_parser = descriptor.Descriptor(parser_options[0])
                selected_parser.parse(file, get_file_extension(file), local_dir, source_paths, force)
            file = file_queue.get_nowait()
    except queue.Empty:
        pass


def get_files(src: path) -> list:
    res: list = [src]
    if path.isdir(src):
        res = []
        for file in Path(src).iterdir():
            res += get_files(file)
    return res


def spawn_processes(pid_count: int, input_files: mp.Queue, output_dir: path, source_paths: list, force: bool) -> list:
    processes: list = []
    for pid in range(pid_count):
        process = mp.Process(target=parse, args=(input_files, output_dir, source_paths, force))
        processes.append(process)
        process.start()
    return processes


def translate(input_files: list, options: dict = None) -> int:
    if not options:
        options = {}

    local_dir_name: str = options.get("output_dir")
    local_dir: path = path.join(getcwd(), ".model")
    if local_dir_name:
        local_dir = path.abspath(local_dir_name)

    if not path.exists(local_dir):
        Path(local_dir).mkdir(parents=True, exist_ok=True)

    number_of_processes = options.get("jobs") or 1

    source_paths: list = options.get("source_paths") or []
    if getcwd() not in source_paths:
        source_paths.append(getcwd())

    force: bool = options.get("force") is True or False
    lazy: bool = options.get("lazy") is True or False

    # TODO create file list to iterate through
    mp.set_start_method('spawn')
    file_list: list = input_files

    if not lazy:
        print("Performing non-lazy translation of source dirs")
        extensions: list = []
        for f in file_list:
            if get_file_extension(f) not in extensions:
                extensions.append(get_file_extension(f))
        langs: list = []
        for e in extensions:
            if config.get_languages_by_extension(e)[0] not in langs:
                langs.append(config.get_languages_by_extension(e)[0])
        source_dirs: list = []
        for l in langs:
            for d in config.get_language_source_dirs(l).get(name):
                if d not in source_dirs:
                    source_dirs.append(d)
        fq: mp.Queue = mp.Queue()
        for file in source_dirs:
            contents: list = get_files(file)
            for f in contents:
                fq.put(f)
        for process in spawn_processes(number_of_processes, fq, MODEL_DIR, source_dirs, force):
            process.join()
        print("Done source translation")

    file_queue: mp.Queue = mp.Queue()
    for file in file_list:
        contents: list = get_files(file)
        for f in contents:
            file_queue.put(f)

    for process in spawn_processes(number_of_processes, file_queue, local_dir, source_paths, force):
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
