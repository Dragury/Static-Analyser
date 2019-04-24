#!/usr/bin/env python3
import click
from staticanalyser.translator.translate import translate
from staticanalyser.navigator.navigate import navigate
import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="sa_out.log",
    format='%(asctime)s - %(name)s - %(processName)s - %(levelname)s - %(message)s'
)


# The 'main' method for the static analyser, runs with a gui or cli
@click.group()
def cli():
    pass


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
    # TODO probably load all files in the .model folder if I can find any, then search for GID
    navigate(global_id, recursion_depth)


@cli.command("hunt")
@click.argument("file", type=click.Path(exists=True), required=True)
@click.option("-s", "--source-path", "source_paths", multiple=True, type=click.Path(exists=True),
              help="Path(s) for rooting translation, defaults to current working dir")
@click.option("-r", "--recursion-depth", "recursion_depth", type=click.INT,
              help="Recursion depth for finding variable usage", default=10)
def hunt_cmd(file, source_paths: list, recursion_depth: int):
    print("TODO!")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("GUI MODE!!!")  # GUI MODE
    else:
        cli()
    sys.exit(0)
