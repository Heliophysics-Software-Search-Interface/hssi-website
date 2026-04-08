"""
Functionality for retrieving json-ld data from our 
maintained HSSI vocabulary repository at 
https://github.com/Heliophysics-Software-Search-Interface/HSSI-vocab/
"""

from __future__ import annotations

import requests
import json

from ..models import (
	ControlledList, ControlledGraphList, DataInput, License, 
	OperatingSystem, ProgrammingLanguage, FileFormat, RepoStatus, 
	CpuArchitecture, Region
)

from typing import Type, Any

URL_REPOSTATUS = "https://www.repostatus.org/badges/latest/ontology.jsonld"
URL_HSSIBASE = "https://raw.githubusercontent.com/Heliophysics-Software-Search-Interface/HSSI-vocab/main/"
URL_JSONBASE = URL_HSSIBASE + "jsonld/"
URL_TTLBASE = URL_HSSIBASE + "ttl/"
URL_CPUARCHITECTURES = URL_JSONBASE + "CPUArchitectures.json"
URL_DATAINPUTS = URL_JSONBASE + "DataSources.json"
URL_LICENSES = URL_JSONBASE + "Licenses.json"
URL_OPERATINGSYSTEMS = URL_JSONBASE + "OperatingSystems.json"
URL_SUPPORTEDFILEFORMATS = URL_JSONBASE + "OutputFileFormats.json"
URL_PROGRAMMINGLANGUAGES = URL_JSONBASE + "ProgrammingLanguages.json"
URL_FUNCTIONCATEGORIES = URL_TTLBASE + "softwareFunctionality-v0.3.ttl"

URL_HELIOPHYSICS_API = "https://api.heliophysics.net/api/"
URL_REGIONS_JSON = URL_HELIOPHYSICS_API + "regions/"

URL_HELIOKNOWBASE = "https://raw.githubusercontent.com/rmcgranaghan/Helio-KNOW/refs/heads/main/data-models/"
URL_REGIONS_TTL = URL_HELIOKNOWBASE + "hk_region.ttl"
URL_PHENOMENA = URL_HELIOKNOWBASE + "hk_phenomenon.ttl"

MODEL_URL_MAP={
	DataInput.__name__: URL_DATAINPUTS,
	License.__name__: URL_LICENSES,
	OperatingSystem.__name__: URL_OPERATINGSYSTEMS,
	CpuArchitecture.__name__: URL_CPUARCHITECTURES,
	ProgrammingLanguage.__name__: URL_PROGRAMMINGLANGUAGES,
	FileFormat.__name__: URL_SUPPORTEDFILEFORMATS,
	RepoStatus.__name__: URL_REPOSTATUS,
	Region.__name__: URL_REGIONS_JSON,
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

def ttl_spl_str(data_str: str) -> str:
	"""
	ttls json exports misslabel keys with full urls, and we only want the 
	key part, not the full url
	"""
	splitstr = data_str.split('#')
	if len(splitstr) > 1:
		return splitstr[-1]
	return data_str

def get_concepts_generalized(
	data: list[dict[str, Any]],
	key_preflabel: str = "prefLabel", 
	key_ident: str = "@id", 
	key_definition: str = "definition"
) -> list[DataListConcept]:
	concepts: list[DataListConcept] = []
	for item in data:
		preflabel = item.get(key_preflabel)
		ident = item.get(key_ident)
		definition = item.get(key_definition)
		if preflabel or ident or definition:
			concept = DataListConcept()
			if preflabel: concept.pref_label = preflabel
			if ident: concept.identifier = ident
			if definition: concept.definition = definition
			concepts.append(concept)
	return concepts

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

class DataListConcept:
	pref_label: str = ""
	definition: str = ""
	identifier: str = ""

	def __init__(self):
		self.pref_label = ""
		self.definition = ""

	def to_model_entry(self, model: Type[ControlledList]) -> ControlledList:
		obj = model()
		setattr(obj, model.get_top_field().name, self.pref_label)
		if isinstance(obj, ControlledList):
			obj.definition = self.definition
			obj.identifier = self.identifier
		elif isinstance(obj, License):
			obj.url = self.definition
		obj.save()
		print(f"saved object {obj.name} to {model}")
		return obj
	
	@classmethod
	def from_concept_serialized(cls, concepts: list[dict[str, Any]]) -> list['DataListConcept']:
		vals = []
		for concept in concepts:
			label = concept.get('prefLabel')
			definition = concept.get('definition')
			if not definition: definition = concept.get('licenseUrl')
			identifier = concept.get('@id')
			conc = DataListConcept()

			did_write = False
			if label:
				did_write = True
				conc.pref_label = label
			if definition:
				did_write = True
				conc.definition = definition
			if identifier:
				did_write = True
				conc.identifier = identifier
			
			if did_write: vals.append(conc)
		return vals

def link_concept_children(
	model: type[ControlledGraphList], 
	concept_data: list[dict[str, Any]], 
	parent_field_name: str = "broader"
):
	print(f"Linking {model.__name__} children with '{parent_field_name}' field")
	objs = model.objects.all()
	for obj in objs:
		concept = next((
			c for c in concept_data if c['@id'] == obj.identifier
		), None)
		print("CONCEPT", concept)
		if concept is None: continue
		parents = concept.get(parent_field_name, [])
		for parent in parents:
			parent_id = parent.get('@id')
			if parent_id is None: continue
			parent_obj = model.objects.filter(identifier=parent_id).first()
			if parent_obj is None: continue
			parent_obj.children.add(obj)
			print(f"Linked '{parent_obj.name}' with child '{obj.name}'")
	for obj in objs: obj.save()
