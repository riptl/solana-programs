from pathlib import Path
from typing import Iterator

import click
from elftools.common.exceptions import ELFError

from . import env
from .dump import dump
from .program import Program


@click.group()
@click.option("--rpc", type=str, default="http://localhost:8899", help="RPC URL")
def cli(rpc):
    env.solana_rpc_str = rpc


def iter_elfs(dir: Path) -> Iterator[Path]:
    return filter(lambda x: x.suffix == ".elf", dir.iterdir())


@cli.command()
@click.argument("elf_dir", type=Path)
def summary(elf_dir: Path):
    for elf_path in iter_elfs(elf_dir):
        try:
            program = Program(elf_path)
        except ELFError as e:
            print(f"WARN: {elf_path.name} is invalid: {e.args[0]}")
        summary = program.summarize()


@cli.command()
@click.argument("elf_dir", type=Path)
def prune(elf_dir: Path):
    for elf_path in iter_elfs(elf_dir):
        with open(elf_path, "rb") as elf_file:
            magic = elf_file.read(4)
        if magic != b"\x7fELF":
            print(f"Deleting {elf_path}")
            elf_path.unlink()
    elf_list = list({e.stem for e in iter_elfs(elf_dir)})
    elf_list.sort()
    list_path = elf_dir.parent / f"{elf_dir.name}.txt"
    print(f"Refreshing {list_path}")
    with open(list_path, "w") as list_file:
        for pubkey in elf_list:
            print(pubkey, file=list_file)


cli.add_command(dump)


if __name__ == "__main__":
    cli()
