import click, sys, tabulate

from mgi.entity.add import add_help, add_entities
from mgi.entity.list import list_help, list_entities
from mgi.helpers import resolve_features

@click.group(short_help="work with samples")
def samples_cli():
    """
    Samples!
    """
    pass

@click.command(help=add_help, short_help="add samples into mgi")
@click.argument("names", required=True, nargs=-1)
def add_cmd(names):
    created, existed = add_entities(names=set(names), kind="sample")
    sys.stdout.write(f"Added {len(created)} of {len(created) - len(existing)}, with these {len(existed)} existing:\n{''.join(existed)}\n")
samples_cli.add_command(add_cmd, name="add")

@click.command(help=list_help, short_help="list samples and features")
@click.argument("filter-by", nargs=-1)
def list_cmd(filter_by):
    known_features = ["name", "sets"]
    features = resolve_features(filter_by, known_features)
    features["kind"] = "sample"
    rows = list_entities(features)
    if rows:
        sys.stdout.write(tabulate.tabulate(rows, list(map(lambda s: s.upper(), known_features)), tablefmt="simple", numalign="left"))
    else:
        sys.stderr.write("No entities found for given fitlers.\n")
samples_cli.add_command(list_cmd, name="list")
