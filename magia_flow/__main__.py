import click

from magia_flow import oss_cad
from magia_flow.simulation import surfer


@click.group()
def cli():
    """Magia Flow CLI tool"""
    ...


@cli.command()
def init():
    """Create a new Magia project"""
    ...


@cli.group()
def install():
    """Install tools and binaries"""
    ...


@install.command()
@click.option("--verilator", is_flag=True, help="Install Verilator")
@click.option("--pnr", is_flag=True, help="Install PnR Tools")
def oss_cad(verilator, pnr):
    """Install OSS-CAD Suite"""
    oss_cad.install(
        verilator=verilator,
        pnr=pnr,
    )


@install.command()
def surfer():
    """Install Surfer"""
    surfer.install()


if __name__ == "__main__":
    cli()
