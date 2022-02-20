from dataclasses import dataclass
from collections import Counter
from enum import IntEnum
import re
from pathlib import Path
import sys
from typing import Iterator, Optional

from elftools.elf.elffile import ELFFile, RelocationSection
from elftools.elf.relocation import Relocation


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


class BPFRelocType(IntEnum):
    R_BPF_NONE = 0
    R_BPF_64_64 = 1
    R_BPF_64_ABS64 = 2
    R_BPF_64_ABS32 = 3
    R_BPF_64_NODYLD32 = 4
    R_BPF_64_RELATIVE = 8
    R_BPF_64_32 = 10


@dataclass
class Summary:
    pubkey: str
    size: int
    section_sizes: dict[int]
    home_name: Optional[str]
    reloc_counts: Counter
    text_size: int = 0
    rodata_size: int = 0

    @staticmethod
    def fields() -> list:
        return [
            "pubkey",
            "size",
            "home_name",
            "text_size",
            "rodata_size",
            "reloc.R_BPF_64_64",
            "reloc.R_BPF_64_RELATIVE",
            "reloc.R_BPF_64_32",
            "reloc.UNSUPPORTED",
        ]

    def to_csv(self) -> dict:
        return {
            "pubkey": self.pubkey,
            "size": self.size,
            "home_name": self.home_name or "",
            "text_size": self.text_size,
            "rodata_size": self.rodata_size,
            "reloc.R_BPF_64_64": self.reloc_counts[BPFRelocType.R_BPF_64_64],
            "reloc.R_BPF_64_RELATIVE": self.reloc_counts[
                BPFRelocType.R_BPF_64_RELATIVE
            ],
            "reloc.R_BPF_64_32": self.reloc_counts[BPFRelocType.R_BPF_64_32],
            "reloc.UNSUPPORTED": self.count_unsupported_relocs(),
        }

    def count_unsupported_relocs(self) -> int:
        unsupported = self.reloc_counts.copy()
        del unsupported[BPFRelocType.R_BPF_64_64]
        del unsupported[BPFRelocType.R_BPF_64_RELATIVE]
        del unsupported[BPFRelocType.R_BPF_64_32]
        # return unsupported.total() # requires Python 3.10
        return sum(unsupported.values())


class Program:
    def __init__(self, filename: Path):
        self.pubkey = filename.stem
        self.size = filename.stat().st_size
        self.elf_file = open(filename, "rb")
        self.elf = ELFFile(self.elf_file)
        self.rodata = self.elf.get_section_by_name(".rodata")

    def summarize(self) -> Summary:
        section_sizes = self.get_section_sizes()
        return Summary(
            pubkey=self.pubkey,
            size=self.size,
            section_sizes=self.get_section_sizes(),
            home_name=next(self.dox(), None),
            reloc_counts=self.get_reloc_counts(),
            text_size=section_sizes.get(".text", 0),
            rodata_size=section_sizes.get(".rodata", 0),
        )

    def get_section_sizes(self) -> dict[int]:
        return {sec.name: sec.data_size for sec in self.elf.iter_sections()}

    def dox(self) -> Iterator[str]:
        """Returns the compiled-in home directory names."""
        if self.rodata is None:
            return iter(())
        matches = re.finditer(
            rb"\/(?:Users|home)\/([\w]+)\/", self.rodata.data(), re.ASCII | re.MULTILINE
        )
        return iter({match[1].decode("utf-8") for match in matches})

    def iter_relocations(self) -> Iterator[Relocation]:
        """Returns an iterator of all relocations in the .rel.dyn section."""
        rel_dyn: Optional[RelocationSection] = self.elf.get_section_by_name(".rel.dyn")
        if rel_dyn is None:
            return iter([])
        return rel_dyn.iter_relocations()

    def get_reloc_counts(self) -> Counter:
        reloc_counts = Counter()
        for reloc in self.iter_relocations():
            try:
                reloc_type = BPFRelocType(reloc["r_info_type"])
                reloc_counts[reloc_type] += 1
            except ValueError:
                print(f"WARN: Invalid reloc {reloc}", sys.stderr)
        return reloc_counts
