from followthemoney.exc import InvalidData
import click
from followthemoney.types import IdentifierType
from followthemoney.dedupe import Linker
from followthemoney import model
from followthemoney.dedupe import Match
from followthemoney.cli.util import read_entities, write_object, ensure_list
from followthemoney.exc import InvalidData
from os.path import join
import json
import logging
import os
from . import enricher

log = logging.getLogger(__name__)


@click.group()
def cli():
    pass


def getJsons(path):
    if os.path.isfile(path):
        return [path]

    return [join(path, file) for file in os.listdir(path) if file.endswith("json")]


def isProperty(property):
    return property and any(property == prop.name for prop in model.properties)


@cli.command("pmatch", help="Match items with common identifier")
@click.option("-i", "--path",
              type=click.Path(exists=True, file_okay=True),
              required=True,
              help="Path to directory or file of JSON FtM entities")
@click.option("-m", "--matchfile", type=click.File("w"), required=False, help="Optional match file name", default="-")
@click.option("-p", "--property", required=False, help="Property to match on. Leave empty when matching on all identifiers.")  
def match_on_id(path, matchfile, property):
    buffer = {}

    if property is not None and not isProperty(property):
        raise InvalidData(f"Property '{property}' not in model")

    try:
        matches = []
        for file in getJsons(path):
            stream = open(file, "r")
            matches.extend(generate_matches(buffer, stream, property))

        log.info(f"Found {len(matches)} matches")

        if len(matches) == 0:
            return

        for match in matches:
            write_object(matchfile, match)

    except BrokenPipeError:
        raise click.Abort()


@cli.command("pmerge", help="Merge items from path and mapfile")
@click.option("-i", "--path",
              type=click.Path(exists=True, file_okay=True),
              required=True,
              help="Path to directory or file of JSON FtM entities")
@click.option("-m", "--matchfile", type=click.File("r"), help="Match file", default="-")
@click.option("-o", "--outfile", type=click.File("w"), help="Output file", default="-")
def unify_id(path, matchfile, outfile):
    try:
        linker = Linker(model)

        for match in Match.from_file(model, matchfile):
            linker.add(match)

        log.info("Linker: %s clusters.", len(linker.lookup))

        for file in getJsons(path):
            link(open(file, "r"), outfile, linker)

    except BrokenPipeError:
        raise click.Abort()


def link(infile, outfile, linker):
    # This is similar to https://github.com/alephdata/followthemoney/blob/master/followthemoney/cli/dedupe.py

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
    # This is similar to https://github.com/alephdata/followthemoney/blob/master/enrich/followthemoney_enrich/enricher.py
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


@cli.command("extract", help="Extract property values")
@click.option("-i", "--path",
              type=click.Path(exists=True, file_okay=True),
              required=True,
              help="Path to directory or file of JSON FtM entities")
@click.option("-o", "--outfile", type=click.File("w"), help="Output file", default="-")
@click.option("-p", "--property", required=False, help="Property name")
def getPropVals(path, outfile, property):
    if not isProperty(property):
        raise InvalidData(f"Property '{property}' not in model")

    for file in getJsons(path):
        stream = open(file, "r")

        for entity in read_entities(stream):
            if entity.has(property, quiet=True):
                write_object(outfile, entity)


@cli.command("enrich", help="Enrich a set of entities using Wikidata")
@click.option("-i", "--infile",
              type=click.File("r"),
              required=True,
              help="FtM entities with Wikidata IDs", default="-")
@click.option("-o", "--outfile", type=click.File("w"), help="Output file", default="-")
@click.option("-l", "--lang", help="Language to enrich. Default: 'en'", default="en")
def enrich_wd(infile, outfile, lang):
    batch = []
    for entity in read_entities(infile):
        batch.append(entity)
        if len(batch) >= enricher.API_LIMIT:
            batch_query_wd(outfile, lang, batch)
            batch.clear()

    batch_query_wd(outfile, lang, batch)


def batch_query_wd(outfile, lang, batch):
    for entity in enricher.get_wd_items(batch, lang):
        write_object(outfile, entity)


if __name__ == "__main__":
    cli()
