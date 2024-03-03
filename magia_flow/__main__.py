import click

import magia_flow


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
    magia_flow.oss_cad.install(verilator, pnr)


@install.command()
def surfer():
    """Install Surfer"""
    magia_flow.simulation.surfer.install()


@cli.group()
def online():
    """
    Online services

    Elaborated SystemVerilog code will be sent to 3rd-party services.
    Don't use this command if you are developing a proprietary IP or any closed-source project.
    """
    ...


@online.command()
def local_digitaljs():
    """Start a local DigitalJS server"""
    magia_flow.online.digitaljs.start_local_server()


if __name__ == "__main__":
    cli()
