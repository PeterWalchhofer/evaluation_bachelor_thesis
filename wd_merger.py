import followthemoney as ftm
from followthemoney.exc import InvalidData
import click
from followthemoney.types import IdentifierType
from followthemoney.dedupe import Linker
from followthemoney import model
from followthemoney.cli import aggregate
import followthemoney.cli.dedupe as dedupe
from followthemoney.dedupe import Match
from followthemoney.cli.cli import cli
from followthemoney.cli.util import read_entities, write_object
from followthemoney.exc import InvalidData
from os.path import dirname

# matching file contains match objects
MATCHES_FILE_NAME = "matches.json.temp"
# merged file has unified IDs, but duplicates
MERGED_FILE_NAME = "matched_unaggr.json.temp"


@click.group()
def cli():
    pass


@cli.command("match-wd", help="Match items with common Wikidata ID")
@click.option("-f", "--first", type=click.File("r"), required=True)  # noqa
@click.option("-s", "--second", type=click.File("r"), required=True)  # noqa
@click.option("-o", "--outfile", type=click.File("w"), required=True)  # noqa
@click.option("-p", "--property", required=False, help="Property to match on. Leave empty when matching on all identifiers.")  # noqa
@click.pass_context
def match_wd(ctx, first, second, outfile, property):
    buffer = {}

    try:
        matches = generate_matches(buffer, first, property)
        matches.extend(generate_matches(buffer, second, property))
        click.echo(f"Found {len(matches)} matches")

        if len(matches) == 0:
            return

        matchfile = open(dirname(outfile.name) + f"/{MATCHES_FILE_NAME}", "w")
        for match in matches:
            write_object(matchfile, match)

        merged_id_file_out = open(
            dirname(outfile.name) + f"/{MERGED_FILE_NAME}", "w")
        ctx.invoke(dedupe.link, infile=open(first.name),
                   outfile=merged_id_file_out, matches=open(matchfile.name))
        ctx.invoke(dedupe.link, infile=open(second.name),
                   outfile=merged_id_file_out, matches=open(matchfile.name))

        merged_id_file_in = open(merged_id_file_out.name)
        ctx.invoke(aggregate.aggregate,
                   infile=merged_id_file_in, outfile=outfile)
    except BrokenPipeError:
        raise click.Abort()



 entity
    return matches

def generate_matches(buffer, infile,on):
    matches = []
    
    for entity in read_entities(infile):
        props = entity.properties
        if on:
            if entity.has(on, True):
                props = [on] 
            else:
                continue
            

        for prop in props:
            if entity.schema.properties[prop].type == IdentifierType:
                id = entity.first(prop)
                if not prop in buffer:
                    buffer[prop] = {}

                if id in buffer[prop]:
                    hit = buffer[prop][id]
                    match = make_match(hit, entity)
                    not match or matches.append(match)
                else:
                    buffer[prop][id] = entity
    
    
    return matches


def make_match(entity, other):
    # similar to https://github.com/alephdata/followthemoney/blob/master/enrich/followthemoney_enrich/enricher.py
    try:
        model.common_schema(entity.schema, other.schema)
    except InvalidData:
        # Do not match unmatchable types.
        return 
    
    match = Match(model, {})
    match.entity=  entity
    match.canonical =  other
    match.decision = match.SAME
    return match

if __name__ == "__main__":
    cli()
