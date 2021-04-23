import followthemoney as ftm
import click
from followthemoney import model
from followthemoney.dedupe import Match
from followthemoney.cli.cli import cli
from followthemoney.cli.util import read_entities, write_object
from followthemoney.exc import InvalidData

@click.group()
def cli():
    pass

@cli.command("match-wd", help="Match items with common Wikidata ID")
@click.option("-f", "--first", type=click.File("r"), default="-")  # noqa
@click.option("-s", "--second", type=click.File("r"), default="-")  # noqa
@click.option("-o", "--outfile", type=click.File("w"), default="-")  # noqa
def match_wd(first, second, outfile):
    buffer = {}
    #enricher = Enrichter()
    try:
        matches = generate_matches(buffer, first)
        matches.extend(generate_matches(buffer, second))
        click.echo(f"Found {len(matches)} matches")
        for match in matches:
            write_object(outfile, match)
           
    except BrokenPipeError:
        raise click.Abort()
    


def generate_matches(buffer, infile)
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
        click.echo("EXC")
        return # Do not match unmatchable types.
    
    match = Match(model, {})
    match.entity=  entity
    match.canonical =  other
    match.decision = match.SAME
    return match

if __name__ == "__main__":
    cli()