import csv
from pathlib import Path
import sys
from typing import Iterator

import click
from elftools.common.exceptions import ELFError

from . import env
from .dump import dump
from .program import Program, Summary


@click.group()
@click.option("--rpc", type=str, default="http://localhost:8899", help="RPC URL")
def cli(rpc):
    env.solana_rpc_str = rpc


def iter_elf_paths(dir: Path) -> Iterator[Path]:
    return filter(lambda x: x.suffix == ".elf", dir.iterdir())


def iter_elfs(dir: Path) -> Iterator[Program]:
    for elf_path in iter_elf_paths(dir):
        try:
            yield Program(elf_path)
        except ELFError as e:
            print(f"WARN: {elf_path.name} is invalid: {e.args[0]}", file=sys.stderr)


@cli.command()
@click.argument("elf_dir", type=Path)
def count_sections(elf_dir: Path):
    section_count = {}
    for elf in iter_elfs(elf_dir):
        for section in elf.get_section_sizes().keys():
            section_count[section] = section_count.get(section, 0) + 1
    for (k, v) in section_count.items():
        print(f"{k},{v}")


@cli.command()
@click.argument("elf_dir", type=Path)
def summary(elf_dir: Path):
    writer = csv.DictWriter(sys.stdout, Summary.fields())
    print(",".join(Summary.fields()))
    for elf in iter_elfs(elf_dir):
        writer.writerow(elf.summarize().to_csv())
        sys.stdout.flush()


@cli.command()
@click.argument("elf_dir", type=Path)
def prune(elf_dir: Path):
    for elf_path in iter_elf_paths(elf_dir):
        with open(elf_path, "rb") as elf_file:
            magic = elf_file.read(4)
        if magic != b"\x7fELF":
            print(f"Deleting {elf_path}")
            elf_path.unlink()
    elf_list = list({e.stem for e in iter_elf_paths(elf_dir)})
    elf_list.sort()
    list_path = elf_dir.parent / f"{elf_dir.name}.txt"
    print(f"Refreshing {list_path}")
    with open(list_path, "w") as list_file:
        for pubkey in elf_list:
            print(pubkey, file=list_file)


cli.add_command(dump)


if __name__ == "__main__":
    cli()
