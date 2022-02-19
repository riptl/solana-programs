from .solana_cli import SolanaCLI
from .solana_rpc import SolanaRPC

solana_cli_str = None
solana_rpc_str = None


def get_solana_cli() -> SolanaCLI:
    client = SolanaCLI(solana_cli_str, solana_rpc_str)
    client.print_version()
    return client


def get_solana_rpc() -> SolanaRPC:
    rpc = SolanaRPC(solana_rpc_str)
    rpc_version = rpc.get_version()
    print(
        f"solana-core {rpc_version['solana-core']} (feat: {rpc_version['feature-set']})"
    )
    return rpc
