import json
from dataclasses import dataclass
from os import path
from typing import Dict, Union


@dataclass
class Subregion:
    id_: int
    names: Dict[str, str]
    lat: float
    long: float

    @classmethod
    def unknown(cls, id_: int):
        return cls(names={"jp": "???", "en": "???", "de": "???", "fr": "???",
                          "es": "???", "it": "???", "nl": "???"},
                   id_=id_, lat=0.0, long=0.0)


@dataclass
class Country:
    id_: int
    names: Dict[str, str]
    alpha2: str
    alpha3: str
    subregions: Dict[int, Subregion]

    @classmethod
    def unknown(cls, id_: int):
        return cls(names={"jp": "???", "en": "???", "de": "???", "fr": "???",
                          "es": "???", "it": "???", "nl": "???"},
                   subregions={0: Subregion.unknown(0)},
                   id_=id_, alpha2="??", alpha3="???")


class CountryMap:
    # Class variable to hold country and region info
    _map: Dict[int, Country] = None

    @staticmethod
    def subregion_json_decoder(k, v) -> Subregion:
        return Subregion(k, v["names"], v["lat"], v["long"])

    @staticmethod
    def country_json_decoder(k, v) -> Country:
        subregions = {int(k_sub): CountryMap.subregion_json_decoder(k_sub, v_sub)
                      for k_sub, v_sub in v["subregions"].items()}
        return Country(k, v["names"], v["alpha2"], v["alpha3"], subregions)

    @classmethod
    def reload(cls, filename: str = path.join(path.dirname(__file__), "countries.json")):
        with open(filename, encoding="utf-8") as f:
            countries = json.load(f)
        countries = {int(k): CountryMap.country_json_decoder(int(k), v)
                     for k, v in countries.items()}
        cls._map = countries

    @classmethod
    def get_country(cls, id_: int, return_unknown: bool = True) -> Union[Country, None]:
        if id_ in cls._map:
            return cls._map[id_]
        return Country.unknown(id_) if return_unknown else None

    @classmethod
    def get_subregion(cls, country_id: int, subregion_id: int, return_unknown: bool = True) \
            -> Union[Subregion, None]:
        country = cls.get_country(country_id, return_unknown=False)
        if country is not None and subregion_id in country.subregions:
            return country.subregions[subregion_id]
        return Subregion.unknown(subregion_id) if return_unknown else None


CountryMap.reload()
