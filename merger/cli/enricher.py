
import requests
from followthemoney import model
from qwikidata.linked_data_interface import get_entity_dict_from_api
from qwikidata.entity import WikidataItem
from qwikidata.datavalue import *
import datetime
import logging

log = logging.getLogger(__name__)


SEARCH_ENDPOINT = "https://www.wikidata.org/w/api.php?action=wbgetentities"

P_INSTANCE_OF = "P31"
P_SUBCLASS_OF = "P279"

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
    "Q4830453": "Company", # Business
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


def get_wd_items(ids, lang):
    ids = set([id for id in ids if id.startswith("Q")])
    wd = query_ids(ids, lang)
    ftm_entities = []
    for id, item in wd.items():
        entity = parse(id, item, lang)
        ftm_entities.append(entity)
    return ftm_entities  


def get_mapping(type):
    mapping = {}
    for schema in model.schemata.get(type).schemata:
        mapping |= prop_mapping[schema.name]
    return mapping


def parse_claims(claims, lang):
    vals = []
    for claim in claims:
        datavalue = claim.mainsnak.datavalue
        wtype = type(datavalue)

        if wtype == WikibaseEntityId:
            # Request to entity to get label.
            qid = datavalue.value["id"]
            label = WikidataItem(get_entity_dict_from_api(qid)).get_label(lang)
            vals.append(label)
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


def get_ftm_type(item, prop=P_INSTANCE_OF):
    instance_ofs = item.get_truthy_claim_group(
        prop)

    for instance_of in instance_ofs:
        datavalue = instance_of.mainsnak.datavalue
        if type(datavalue) == WikibaseEntityId:
            id = datavalue.value["id"]
            ftm_type = type_mapping.get(id)
            if ftm_type:
                return ftm_type
    
    # TODO: Handle nested subclasses (via recursion or SPARQL)
    # ÖBB <instanceOf> railway company <instanceOf> business is not detected.


def parse(id, item_dict, lang, quiet=True):
    """
     "Truthy statements represent statements that have the best non-deprecated rank for a
            given property. Namely, if there is a preferred statement for a property P, then only
            preferred statements for P will be considered truthy. Otherwise, all normal-rank
            statements for P are considered truthy."
            https://github.com/kensho-technologies/qwikidata/blob/8438c887c2875973e261e5dede13a0b7bf951e41/qwikidata/entity.py#L170
    """

    item = WikidataItem(item_dict)
    type = get_ftm_type(item)

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

    # Manually parse, as we want aliases from all languages returned.
    aliases = set()
    for _, item_aliases in item_dict["aliases"].items():
        for alias in item_aliases:
            aliases.add(alias["value"])

    mapping = get_mapping(type)

    for pid, ftm_prop in mapping.items():
        claim_group = item.get_truthy_claim_group(pid)
        if claim_group:
            prop_vals = parse_claims(claim_group, lang)
            entity.add(ftm_prop, prop_vals)

    return entity


if __name__ == "__main__":
    wditems = get_wd_items(["Q51533040","Q81526090","Q20752545","Q102353097","Q50843964","NaN","Q102353101","Q1703382","Q15792244","Q1384694","Q54962932","Q1802317","Q1618939","Q25991721","Q102353119","Q102353116"], "de")
