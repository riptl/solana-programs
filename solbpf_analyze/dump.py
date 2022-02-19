import itertools
from pathlib import Path
import subprocess
import sys

import click
from tqdm import trange

from .env import get_solana_rpc
from .program import Loader


@click.command()
@click.argument("network")
def dump(network):
    print()
    rpc = get_solana_rpc()
    print()

    script_dir = Path(sys.argv[0]).parent.parent
    dump_dir = script_dir / "programs" / network
    dump_dir.mkdir(exist_ok=True)
    print(f"Dumping to {dump_dir}")
    print()

    print("Listing BPF Loader Legacy")
    bpf_loader_keys = list(rpc.get_bpf_loader_legacy_keys())
    print(f"Got {len(bpf_loader_keys)} BPF Loader Legacy accounts")

    print("Listing BPF Loader")
    bpf_loader_2_keys = list(rpc.get_bpf_loader_keys())
    print(f"Got {len(bpf_loader_2_keys)} BPF Loader accounts")

    print("Listing BPF Loader (upgradeable)")
    bpf_loader_3_keys = list(rpc.get_bpf_loader_upgradeable_keys())
    print(f"Got {len(bpf_loader_3_keys)} BPF Loader Upgradeable accounts")

    print()
    print("Starting dump")

    # Create dumping iterators.
    progress = iter(
        trange(len(bpf_loader_keys) + len(bpf_loader_2_keys) + len(bpf_loader_3_keys))
    )
    dumpers = itertools.chain(
        rpc.get_multiple_bpf_loader_legacy_programs(bpf_loader_keys),
        rpc.get_multiple_bpf_loader_programs(bpf_loader_2_keys),
        rpc.get_multiple_bpf_loader_upgradeable_programs(bpf_loader_3_keys),
    )

    # Create loader dirs / lists.
    loader_names = {
        Loader.LEGACY: "bpf_loader",
        Loader.V2: "bpf_loader_2",
        Loader.UPGRADEABLE: "bpf_loader_3",
    }
    program_lists = {
        k: open(dump_dir / f"{v}.txt", "w") for (k, v) in loader_names.items()
    }

    # Dump every program one-by-one.
    for program in dumpers:
        loader_name = loader_names[program.loader]
        program_list = program_lists[program.loader]

        program.save(dump_dir / loader_name)
        print(program.pubkey, file=program_list)

        next(progress)

    # Sort program lists.
    for v in program_lists.values():
        path = v.name
        v.close()
        subprocess.run(["sort", "-u", "-o", path, path])
