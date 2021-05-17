
import requests
from followthemoney import model
from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.entity import WikidataItem
from qwikidata.datavalue import *
import datetime
import logging

log = logging.getLogger(__name__)


SEARCH_ENDPOINT = "https://www.wikidata.org/w/api.php?action=wbgetentities"
API_LIMIT = 50
P_INSTANCE_OF = "P31"
P_SUBCLASS_OF = "P279"

CACHE = {}

prop_mapping = {
    "Person": {
        "P512": "title",
        "P735": "firstName",
        "P734": "lastName",
        "P569": "birthDate",
        "P19": "birthPlace",
        "P570": "deathDate",
        "P27": "nationality",
        "P21": "gender",
        "P172": "ethnicity",
        "P140": "religion"
    },
    "Thing": {
        "P6375": "address",
    },
    "LegalEntity": {
        'P968': 'email',
        'P1329': 'phone',
        'P856': 'website',
        'P1454': 'legalForm',
        'P571': 'incorporationDate',
        'P576': 'dissolutionDate',
        'P452': 'sector',
        'P3608': 'vatCode',
        'P1001': 'jurisdiction',
        'P495': 'mainCountry',
        'P2391': 'okpoCode',
        'P2771': 'dunsCode',
        'P2627': 'swiftBic',
        'P749': 'parent'},
    "Company": {
        "P1297": "irsCode",
        "P5531": "clkCode",
        "P3246": "okvedCode"
    }
}
type_mapping = {
    "Q35120": "Thing",
    "Q5": "Person",
    "Q43229": "Organization",
    "Q3778211": "LegalEntity",
    "Q783794": "Company",  # Company
    "Q4830453": "Company",  # Business
    "Q2659904": "PublicBody"
}


def query_ids(ids, lang):

    params = {
        "ids": "|".join(ids),
        "language": lang,
        "format": "json"
    }

    results = requests.get(SEARCH_ENDPOINT, params=params)
    dicts = results.json()
    return dicts.get("entities") or {}


def get_wd_items(entities, lang, quiet=True):
    entitymap = {}
    for entity in entities:
        wd = entity.first("wikidataId", quiet)
        if wd and wd.startswith("Q"):
            entitymap[wd] = entity

    ids = entitymap.keys()

    if len(ids) > API_LIMIT:
        raise ValueError("Can only handle max {API_LIMIT} ids.")

    wd = query_ids(ids, lang)
    ftm_entities = []
    for id, item in wd.items():
        schema = entitymap[id].schema.name
        entity = parse(id, item, schema, lang, quiet)
        if entity:
            ftm_entities.append(entity)
    return ftm_entities


def get_prop_mapping(type):
    """This handles type inheritances of the FtM model by merging the mapping objects of each supertype."""
    mapping = {}
    for schema in model.schemata.get(type).schemata:
        mapping |= prop_mapping.get(schema.name, {})
    return mapping


def parse_claims(claims, lang):
    """Here, property claims/statements are are parsed."""
    vals = []
    for claim in claims:
        datavalue = claim.mainsnak.datavalue
        wtype = type(datavalue)

        if wtype == WikibaseEntityId:
            # Request to entity to get label.
            qid = datavalue.value["id"]
            if qid in CACHE:
                vals.append(CACHE[qid])
            else:
                label = WikidataItem(
                    get_entity_dict_from_api(qid)).get_label(lang)
                vals.append(label)
                CACHE[qid] = label
        elif wtype == String:
            vals.append(datavalue.value)
        elif wtype == MonolingualText:
            vals.append(datavalue.value["text"])
        elif wtype == Quantity:
            vals.append(datavalue.value["amount"])
        elif wtype == Time:
            time = datavalue.get_parsed_datetime_dict()
            try:
                ptime = datetime.datetime(**time)
            except:
                ptime = datavalue.value["time"]
            vals.append(ptime)
    return vals


def parse_aliases(item_dict):
    # Manually parse, as we want aliases from all languages returned.
    aliases = set()
    for _, item_aliases in item_dict["aliases"].items():
        for alias in item_aliases:
            aliases.add(alias["value"])
    return aliases


def parse(id, item_dict, type, lang, quiet=True):
    item = WikidataItem(item_dict)

    if not type:
        if quiet:
            log.warning(f"Item with id '{id}' not matchable to FtM")
            return
        else:
            raise Exception(f"Item with id '{id}' not matchable to FtM")

    entity = model.make_entity(type)
    entity.add("name", item.get_label(lang))
    entity.add("description",  item.get_description(lang))
    entity.make_id(id)
    entity.add("alias", parse_aliases(item_dict))
    entity.add("wikidataId", id)

    mapping = get_prop_mapping(type)

    for pid, ftm_prop in mapping.items():
        claim_group = item.get_truthy_claim_group(pid)
        if claim_group:
            prop_vals = parse_claims(claim_group, lang)
            entity.add(ftm_prop, prop_vals)

    return entity
