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
from os.path import dirname, join
import logging
import os

log = logging.getLogger(__name__)


@click.group()
def cli():
    pass

def getJsons(path):
    return [file for file in os.listdir(path) if file.endswith("json")]

@cli.command("id-match", help="Match items with common identifier")
@click.option("-i", "--path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="Path containing one or more FtM files in json.", default="-")
@click.option("-m", "--matchfile", type=click.File("w"), required=False , help="Optional match file name", default="-")
@click.option("-p", "--property", required=False, help="Property to match on. Leave empty when matching on all identifiers.")  # noqa
def match_on_id(path, matchfile, property):
    buffer = {}

    if property and not any(property == prop.name for prop in model.properties):
        raise InvalidData(f"Property '{property}' not in model")

    try:
        matches = []
        for file in getJsons(path):
            stream = open(join(path, file), "r")
            matches.extend(generate_matches(buffer, stream, property))

        log.info(f"Found {len(matches)} matches")

        if len(matches) == 0:
            return

        
        for match in matches:
            write_object(matchfile, match)

       
    except BrokenPipeError:
        raise click.Abort()


@cli.command("merger", help="Merge items from path and mapfile")
@click.option("-i", "--path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="Path containing one or more FtM files in json.")
@click.option("-m", "--matchfile", type=click.File("r") , help="Match file", default="-")
@click.option("-o", "--outfile", type=click.File("w"), help="Match file", default="-")
def unify_id(path, matchfile, outfile):
    try:
        linker = Linker(model)
        
        for match in Match.from_file(model, matchfile):
            linker.add(match)

        log.info("Linker: %s clusters.", len(linker.lookup))

        for file in getJsons(path):
            link(open(join(path, file), "r"), outfile, linker)
            
    except BrokenPipeError:
        raise click.Abort()


def link(infile, outfile, linker):
    # Similar to https://github.com/alephdata/followthemoney/blob/master/followthemoney/cli/dedupe.py

    for entity in read_entities(infile):
        entity = linker.apply(entity)
        write_object(outfile, entity)

def generate_matches(buffer, infile, on):
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
        log.warning(
            f"Warning: Entity '{entity.id}'' and '{other.id}' cannot be matched. Incompatible types <{entity.schema.name}, {other.schema.name}>")
        return

    match = Match(model, {})
    match.entity = entity
    match.canonical = other
    match.decision = match.SAME
    return match


if __name__ == "__main__":
    cli()
