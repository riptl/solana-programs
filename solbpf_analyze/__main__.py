import click

from . import env
from .dump import dump


@click.group()
@click.option("--rpc", type=str, default="http://localhost:8899")
def cli(rpc):
    env.solana_rpc_str = rpc


cli.add_command(dump)


if __name__ == "__main__":
    cli()
