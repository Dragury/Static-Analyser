#!/usr/bin/env python3
import click
from staticanalyser.translator.translate import translate
from staticanalyser.navigator.navigate import navigate
from staticanalyser.hunter import hunt
import sys
import logging
from pathlib import Path, PosixPath
from os import path

logging.basicConfig(
    level=logging.DEBUG,
    filename="sa_out.log",
    format='%(asctime)s - %(name)s - %(processName)s - %(levelname)s - %(message)s'
)


# The 'main' method for the static analyser, runs with a gui or cli
@click.group()
def cli():
    pass


def get_files(src: path) -> list:
    res: list = [src]
    if path.isdir(src):
        res = []
        for file in Path(src).iterdir():
            res += get_files(file)
    return res


@cli.command("translate")
@click.argument("file", nargs=-1, type=click.Path(exists=True), required=True, metavar="[file ...]")
@click.option("-j", "--jobs", default=4, type=click.INT, help="Use N threads for translation process", metavar="[N]")
@click.option("-s", "--source-path", "source_paths", multiple=True, type=click.Path(exists=True),
              help="Path(s) for rooting translation, defaults to current working dir")
@click.option("-o", "--output-dir", "output_dir", type=click.Path(exists=True),
              help="Location to store models, default is current dir")
@click.option("-f", "--force", "force", is_flag=True, help="Force translation of files, even if models exist")
@click.option("-l/-L", "--lazy/--not-lazy", "lazy", default=True,
              help="Lazy translation. Translate global sources on demand. Disabling lazy is not recommended")
def translate_cmd(file: list, jobs: int, source_paths: list, force, lazy, output_dir):
    """Translate files and directory contents ready for static analysis"""
    # setup_logger()
    options: dict = {
        "jobs": jobs,
        "source_paths": list(source_paths),
        "force": force,
        "lazy": lazy,
        "output_dir": output_dir
    }
    translate(file, options)


@cli.command("find")
@click.argument("global_id", nargs=1, type=click.STRING, required=True, metavar="[global id]")
@click.option("-r", "--recursion-depth", "recursion_depth", type=click.INT,
              help="Recursion depth for finding variable usage", default=10)
def navigate_cmd(global_id: str, recursion_depth: int):
    files_to_load = get_files(".model/")
    path: PosixPath
    logging.debug("trying to load: {}".format("\n\t".join([str(path) for path in files_to_load])))
    print(navigate(global_id, recursion_depth, files_to_load))


@cli.command("hunt")
@click.option("-r", "--recursion-depth", "recursion_depth", type=click.INT,
              help="Recursion depth for finding variable usage", default=10)
@click.option("-s", "--sink-function", "sink_functions", multiple=True, type=click.STRING,
              help="Specify the global id of a function considered to be vulnerable")
@click.option("-d", "--danger", "dangers", multiple=True, type=click.STRING,
              help="Specify the id of something considered to be a dangerous data source")
@click.option("-c", "--clean-function", "clean_funcs", multiple=True, type=click.STRING,
              help="Specify the global id of a function that cleans data")
@click.option("-l", "--language", "language", type=click.STRING, help="Language to use for standard searching",
              default="")
def hunt_cmd(recursion_depth: int, sink_functions: list, dangers: list, clean_funcs: list, language: str):
    files_to_load = get_files(".model/")
    print(hunt(recursion_depth, list(sink_functions), list(dangers), list(clean_funcs), files_to_load, language))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("GUI MODE!!!")  # GUI MODE
    else:
        cli()
    sys.exit(0)
