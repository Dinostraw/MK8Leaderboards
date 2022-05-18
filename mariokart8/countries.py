import json
from dataclasses import dataclass
from os import path
from typing import Dict


@dataclass
class Subregion:
    id_: int
    names: Dict[str, str]
    lat: float
    long: float

    @classmethod
    def unknown(cls, id_: int):
        return Subregion(names={"jp": "???", "en": "???", "de": "???", "fr": "???",
                                "es": "???", "it": "???", "nl": "???"},
                         id_=id_, lat=0.0, long=0.0)


@dataclass
class Country:
    id_: int
    names:  Dict[str, str]
    alpha2: str
    alpha3: str
    subregions: Dict[int, Subregion]

    @classmethod
    def unknown(cls, id_: int):
        return Country(names={"jp": "???", "en": "???", "de": "???", "fr": "???",
                              "es": "???", "it": "???", "nl": "???"},
                       subregions={0: Subregion.unknown(0), 1: Subregion.unknown(1)},
                       id_=id_, alpha2="??", alpha3="???")


def subregion_decoder(k, v) -> Subregion:
    return Subregion(k, v["names"], v["lat"], v["long"])


def country_decoder(k, v) -> Country:
    subregions = {int(k_sub): subregion_decoder(k_sub, v_sub)
                  for k_sub, v_sub in v["subregions"].items()}
    subregions[0] = Subregion.unknown(0)

    return Country(k, v["names"], v["alpha2"], v["alpha3"], subregions)


def load_countries(filename: str = path.join(path.dirname(__file__), "countries.json")) -> Dict[int, Country]:
    with open(filename, encoding="utf-8") as f:
        countries = json.load(f)
    countries = {int(k): country_decoder(int(k), v) for k, v in countries.items()}
    countries[0] = Country.unknown(0)
    return countries


COUNTRY_MAP = load_countries()
