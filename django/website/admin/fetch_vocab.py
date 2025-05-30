"""
This module contains functionality for retrieving json-ld data from our 
maintained HSSI vocabulary repository at 
https://github.com/Heliophysics-Software-Search-Interface/HSSI-vocab/
"""

import requests
import json

from ..models import (
    ControlledList, DataInput, License, OperatingSystem, ProgrammingLanguage,
    FileFormat, RepoStatus
)

from typing import Type, Any

URL_BASE = "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/"
URL_DATAINPUTS = "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/DataInputs.json"
URL_LICENSE = URL_BASE + "DataInputs.json"
URL_OPERATINGSYSTEM = URL_BASE + "DataInputs.json"
URL_SUPPORTEDFILEFORMATS = URL_BASE + "DataInputs.json"

MODEL_URL_MAP={
    DataInput.__name__: "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/DataInputs.json",
    License.__name__: "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/License.json",
    OperatingSystem.__name__: "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/OperatingSystem.json",
    ProgrammingLanguage.__name__: "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/ProgrammingLanguages.json",
    FileFormat.__name__: "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/jsonld/SupportedFileFormats.json",
    RepoStatus.__name__: "https://www.repostatus.org/badges/latest/ontology.jsonld",
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