"""
This module contains functionality for retrieving json-ld data from our 
maintained HSSI vocabulary repository at 
https://github.com/Heliophysics-Software-Search-Interface/HSSI-vocab/
"""

import requests
import json

from ..models import (
    ControlledList, DataInput, License, OperatingSystem, ProgrammingLanguage,
    FileFormat, RepoStatus, CpuArchitecture,
)

from typing import Type, Any

URL_REPOSTATUS = "https://www.repostatus.org/badges/latest/ontology.jsonld"
URL_HSSIBASE = "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/"
URL_CPUARCHITECTURES = URL_HSSIBASE + "CPUArchitectures.json"
URL_DATAINPUTS = URL_HSSIBASE + "DataSources.json"
URL_LICENSES = URL_HSSIBASE + "Licenses.json"
URL_OPERATINGSYSTEMS = URL_HSSIBASE + "OperatingSystems.json"
URL_SUPPORTEDFILEFORMATS = URL_HSSIBASE + "OutputFileFormats.json"
URL_PROGRAMMINGLANGUAGES = URL_HSSIBASE + "ProgrammingLanguages.json"

MODEL_URL_MAP={
    DataInput.__name__: URL_DATAINPUTS,
    License.__name__: URL_LICENSES,
    OperatingSystem.__name__: URL_OPERATINGSYSTEMS,
    CpuArchitecture.__name__: URL_CPUARCHITECTURES,
    ProgrammingLanguage.__name__: URL_PROGRAMMINGLANGUAGES,
    FileFormat.__name__: URL_SUPPORTEDFILEFORMATS,
    RepoStatus.__name__: URL_REPOSTATUS,
}

def get_data(url: str) -> dict | list:
    req = requests.get(url)
    try:
        return req.json()
    except Exception:
        print("json data is dirty, cleaning...")
        str_data: str = req.text
        str_data = str_data.replace('“', '"').replace('”', '"')
    return json.loads(str_data)

def get_concepts(data: dict | list[dict]) -> list[dict]:
    if isinstance(data, dict):
        if '@graph' in data:
            return get_concepts(data['@graph'])
    else:
        vals = []
        for concept in data:
            if not '@type' in concept: continue
            if concept['@type'] == 'Concept':
                vals.append(concept)
        return vals

def parse_jsonld(target_type: Type[ControlledList], data: dict):
    obj = target_type()
    obj.name = ""
    obj.save()

class JsonldConcept:
    pref_label: str = ""
    definition: str = ""

    def __init__(self):
        self.pref_label = ""
        self.definition = ""

    def to_model(self, model: Type[ControlledList]):
        obj = model()
        obj.name = self.pref_label
        obj.definition = self.definition
        obj.save()
        print(f"saved object {obj.name} to {model}")
    
    @classmethod
    def from_concept_json(cls, concepts: list[dict[str, Any]]) -> list['JsonldConcept']:
        vals = []
        for concept in concepts:
            label = concept.get('prefLabel')
            definition = concept.get('definition')
            conc = JsonldConcept()

            did_write = False
            if label is not None:
                did_write = True
                conc.pref_label = label
            if definition is not None:
                did_write = True
                conc.definition = definition
            
            if did_write:
                vals.append(conc)
        return vals