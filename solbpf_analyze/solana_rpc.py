from base64 import b64decode
from dataclasses import dataclass
import itertools
from typing import Iterable, Iterator, Generator

from base58 import b58encode

from .rpc import RPCClient
from .program import Loader, OnChainProgram


ELF_MAGIC = b"\x7fELF"


class SolanaRPC(RPCClient):
    BPF_LOADER_PUBKEY = "BPFLoader1111111111111111111111111111111111"
    BPF_LOADER_2_PUBKEY = "BPFLoader2111111111111111111111111111111111"
    BPF_LOADER_3_PUBKEY = "BPFLoaderUpgradeab1e11111111111111111111111"

    # Filter for ELF signature
    BPF_LOADER_FILTER = {
        "memcmp": {"offset": 0, "bytes": b58encode(ELF_MAGIC).decode("utf-8")}
    }
    # Filter for "ProgramData" enum
    BPF_LOADER_3_FILTER = {
        "memcmp": {
            "offset": 0,
            "bytes": b58encode(b"\x03\x00\x00\x00").decode("utf-8"),
        },
        "memcmp": {"offset": 45, "bytes": b58encode(ELF_MAGIC).decode("utf-8")},
    }

    def get_version(self) -> dict:
        return self.request("getVersion")

    def get_bpf_loader_legacy_keys(self) -> Iterator[str]:
        return self.get_program_account_keys(
            SolanaRPC.BPF_LOADER_PUBKEY, [SolanaRPC.BPF_LOADER_FILTER]
        )

    def get_bpf_loader_keys(self) -> Iterator[str]:
        return self.get_program_account_keys(
            SolanaRPC.BPF_LOADER_2_PUBKEY, [SolanaRPC.BPF_LOADER_FILTER]
        )

    def get_bpf_loader_upgradeable_keys(self) -> Iterator[str]:
        return self.get_program_account_keys(
            SolanaRPC.BPF_LOADER_3_PUBKEY, [SolanaRPC.BPF_LOADER_3_FILTER]
        )

    def get_program_account_keys(
        self, pubkey: str, filters: list
    ) -> Generator[str, None, None]:
        opts = {
            "encoding": "base64",
            "dataSlice": {"offset": 0, "length": 0},
            "filters": filters,
        }
        accounts = self.request("getProgramAccounts", pubkey, opts)
        for account in accounts:
            yield account["pubkey"]

    def get_multiple_bpf_loader_legacy_programs(
        self, pubkeys: Iterable[str], **kwargs
    ) -> Iterator[OnChainProgram]:
        return self.get_multiple_programs(pubkeys, Loader.LEGACY, **kwargs)

    def get_multiple_bpf_loader_programs(
        self, pubkeys: Iterable[str], **kwargs
    ) -> Iterator[OnChainProgram]:
        return self.get_multiple_programs(pubkeys, Loader.V2, **kwargs)

    def get_multiple_bpf_loader_upgradeable_programs(
        self, pubkeys: Iterable[str], **kwargs
    ) -> Iterator[OnChainProgram]:
        return self.get_multiple_programs(
            pubkeys, Loader.UPGRADEABLE, offset=45, **kwargs
        )

    def get_multiple_programs(
        self,
        pubkeys: Iterable[str],
        loader: Loader,
        offset: int = 0,
        batch: int = 100,
    ) -> Generator[OnChainProgram, None, None]:
        pubkeys = iter(pubkeys)
        while True:
            chunk = list(itertools.islice(pubkeys, batch))
            if len(chunk) == 0:
                break
            for program in self._get_multiple_programs_batch(chunk, offset):
                program.loader = loader
                yield program

    def _get_multiple_programs_batch(
        self, pubkeys: Iterable[str], offset: int = 0
    ) -> Generator[OnChainProgram, None, None]:
        data_slice = {"offset": offset, "length": 1 << 31}
        result = self.request("getMultipleAccounts", pubkeys, {"dataSlice": data_slice})
        for idx, item in enumerate(result["value"]):
            if item is None:
                continue
            data = b64decode(item["data"][0])
            assert data[:4] == ELF_MAGIC
            yield OnChainProgram(pubkey=pubkeys[idx], data=data)
