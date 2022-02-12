import argparse
from pathlib import Path
import re
import sys

from elftools.common.exceptions import ELFError
from elftools.elf.elffile import ELFFile


def do_stuff(filename: ELFFile):
    rodata_section = filename.get_section_by_name(".rodata")
    if rodata_section is None:
        return
    rodata = rodata_section.data()

    matches = re.finditer(
        rb"\/(?:Users|home)\/([\w]+)\/", rodata, re.ASCII | re.MULTILINE
    )
    matches = set([match[1].decode("utf-8") for match in matches])
    for match in matches:
        print(match)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()

    with open(args.elf, "rb") as elf_file:
        try:
            elf = ELFFile(elf_file)
        except ELFError:
            print("[!] not an ELF", file=sys.stderr)
            sys.exit(1)
        do_stuff(elf)


if __name__ == "__main__":
    main()
