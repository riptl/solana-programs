from dataclasses import dataclass
from enum import IntEnum
import re
from pathlib import Path
from typing import Iterable, Optional

from elftools.elf.elffile import ELFFile


class Loader(IntEnum):
    LEGACY = 1
    V2 = 2
    UPGRADEABLE = 3


@dataclass
class OnChainProgram:
    pubkey: str
    data: bytes
    loader: Optional[Loader] = None

    def save(self, dir: Path):
        dir.mkdir(parents=True, exist_ok=True)
        file_name = dir / f"{self.pubkey}.elf"
        with open(file_name, "wb") as program_file:
            program_file.write(self.data)


class Program:
    def __init__(self, filename: str):
        self.elf_file = open(filename, "rb")
        self.elf = ELFFile(self.elf_file)
        self.rodata = self.elf.get_section_by_name(".rodata")

    def dox(self) -> Iterable[str]:
        """Returns the compiled-in home directory names."""
        if self.rodata is None:
            return iter(())
        matches = re.finditer(
            rb"\/(?:Users|home)\/([\w]+)\/", self.rodata.data(), re.ASCII | re.MULTILINE
        )
        return iter({match[1].decode("utf-8") for match in matches})
