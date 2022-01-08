import click

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """
    Cromwell on MGI Compute
    """
    pass

from cw.printc_cmd import printc_cmd as cmd
cli.add_command(cmd, "printc")

from cw.setup_cmd import setup_cmd as cmd
cli.add_command(cmd, "setup")
