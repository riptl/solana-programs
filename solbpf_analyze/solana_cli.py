import subprocess


class SolanaCLI:
    """Solana CLI wrapper."""

    def __init__(self, sol_bin: str = "solana", rpc: str = ""):
        self.sol_bin = sol_bin
        self.rpc = rpc

    def print_version(self):
        subprocess.run(self.cmd("--version"), check=True, text=True)

    def cmd(self, *args):
        base = [self.sol_bin]
        if self.rpc != "":
            base += ["--url", self.rpc]
        return base + list(args)
