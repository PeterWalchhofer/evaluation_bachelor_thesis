import followthemoney as ftm
import click
from followthemoney.dedupe import Linker
from followthemoney import model
from followthemoney.cli import aggregate
import followthemoney.cli.dedupe as dedupe
from followthemoney.dedupe import Match
from followthemoney.cli.cli import cli
from followthemoney.cli.util import read_entities, write_object
from followthemoney.exc import InvalidData
from os.path import dirname

MATCHES_FILE_NAME = "matches.json.temp" # matching file contains match objects
MERGED_FILE_NAME = "matched_unaggr.json.temp" # merged file has unified IDs, but duplicates
MATCHED_FILE_NAME = "matched.json" # final matched

@click.group()
def cli():
    pass

@cli.command("match-wd", help="Match items with common Wikidata ID")
@click.option("-f", "--first", type=click.File("r"), required=True)  # noqa
@click.option("-s", "--second", type=click.File("r"), required=True)  # noqa
@click.option("-o", "--outfile", type=click.File("w"), required=True)  # noqa
@click.pass_context
def match_wd(ctx, first, second, outfile):
    buffer = {}
   
    try:
        matches = generate_matches(buffer, first)
        matches.extend(generate_matches(buffer, second))
        click.echo(f"Found {len(matches)} matches")

        matchfile = open(dirname(outfile.name) + f"/{MATCHES_FILE_NAME}", "w")
        for match in matches:
            write_object(matchfile, match)

        merged_id_file_out = open(dirname(outfile.name) + f"/{MERGED_FILE_NAME}", "w")
        ctx.invoke(dedupe.link, infile = open(first.name), outfile = merged_id_file_out, matches=open(matchfile.name))
        ctx.invoke(dedupe.link, infile = open(second.name), outfile = merged_id_file_out, matches=open(matchfile.name))
        
        merged_id_file_in = open(merged_id_file_out.name)
        ctx.invoke(aggregate.aggregate, infile = merged_id_file_in, outfile=outfile)
    except BrokenPipeError:
        raise click.Abort()
    


def generate_matches(buffer, infile):
    """Fill buffer and create match. This also finds duplicates within a file. """
    matches = []
    
    for entity in read_entities(infile):
        wd = entity.first("wikidataId", True)
        if wd and wd in buffer:
            hit = buffer[wd]
            match = make_match(hit, entity)
            not match or matches.append(match)
        if wd: 
            buffer[wd] = entity
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