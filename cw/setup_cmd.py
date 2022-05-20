import click, os, sys, yaml

from cw.conf import CromwellConf
from cw import create_db, db

@click.command(short_help="setup cromwell")
def setup_cmd():
    """
    Setup Cromwell

    Run this command without the YAML file to print the configuration to file <cw.yaml> to fill out and save. Then rerun this command with the completed YAML file to create directories and files.
    """
    cc = CromwellConf.safe_load()
    if not cc.is_validated:
        cc.set("CROMWELL_DIR", os.getcwd())
        cc.save()
        sys.stderr.write(f"Saved YAML configuration to <{cc.yaml_fn()}>.\nFill out the 'LSF' attributes, then rerun this command.\n")
        sys.exit(0)
    sys.stdout.write("Setup cromwell: making directories, scripts, and configuration.\n")
    cc.setup()
    create_db()
#-- setup_cmd
