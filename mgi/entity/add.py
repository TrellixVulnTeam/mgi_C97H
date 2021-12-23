import click

from mgi.models import db, Entity

add_help = """
    Add Entites Into MGI

    \b
    Add via command line:

    Give comma separated names and features as name=value pairs.

    NAME1 F1=V1 F2=V2 ...

    NAME1,NAME2 F1=V1 F2=V2 ...


    Add via TSV:
    
    Give a TSV file of with columns and one entity per row. Column 'name' is required.

    NAME\tF1\tF2
    NAME1\tV1\tV2
    NAME2\tV3\tV4

    """

def add_entities(names, kind):
    created, existed = set(), set()
    for name in names:
        entity = Entity.query.filter(Entity.name == name, Entity.kind == kind).one_or_none()
        if entity is not None:
            existed.add(name)
            continue
        entity = Entity(name=name, kind=kind)
        db.session.add(entity)
        created.add(name)
    db.session.commit()
    return created, existed
#-- add_entities
