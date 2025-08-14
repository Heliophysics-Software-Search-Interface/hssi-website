"""
This module contains functionality for retrieving json-ld data from our 
maintained HSSI vocabulary repository at 
https://github.com/Heliophysics-Software-Search-Interface/HSSI-vocab/
"""

import requests
import json

from ..models import (
	HssiModel, ControlledList, ControlledGraphList, DataInput, License, 
	OperatingSystem, ProgrammingLanguage, FileFormat, RepoStatus, 
	CpuArchitecture, FunctionCategory
)

from django.db.models import Model
import rdflib

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
	if url.endswith('.ttl'): return get_data_turtle(url)
	req = requests.get(url)
	try:
		return req.json()
	except Exception:
		print("json data is dirty, cleaning...")
		str_data: str = req.text
		str_data = str_data.replace('“', '"').replace('”', '"')
	return json.loads(str_data)

def get_data_turtle(url: str) -> dict | list:
	req = requests.get(url)
	graph = rdflib.Graph()
	try:
		graph.parse(data=req.text, format='turtle')
	except Exception as e:
		print(f"Error parsing turtle data from {url}: {e}")
	json_data = parse_ttl_jsonld(json.loads(graph.serialize(format='json-ld')))
	return json_data

def parse_ttl_jsonld(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
	"""
	Parse the turtle file data (which should be exported as a json-ld) into a 
	proper json data format.
	"""
	parsed = []

	# TODO we should probably remove this entire intermediary step of 
	# converting the ttl to a json then parsing the json, and instead 
	# just parse the ttl directly with rdflib

	# get the names of the classes that inherit from Concept
	class_names = ["Class", "Concept"]
	cnfound = True
	while cnfound:
		cnfound = False
		for entry in data:
			val = entry.get('@type', None)
			id = entry.get('@id', None)
			if id and val:
				while isinstance(val, list): val = val[0]
				val = ttl_spl_str(val)
				if val == "Class":
					sckey = "subClassOf"
					for key in entry.keys():
						nkey = ttl_spl_str(key)
						if nkey == "subClassOf":
							sckey = key
							break
					nval = entry.get(sckey, None)
					if nval:
						while isinstance(nval, list): nval = nval[0]
						if isinstance(nval, dict): 
							nval = nval.get('@id') or nval.get('@value')
						nval = ttl_spl_str(nval)
						if nval in class_names:
							id = ttl_spl_str(id)
							if id not in class_names:
								cnfound = True
								class_names.append(id)

	for entry in data:
		new = {}
		etype = entry.get('@type', None)
		if etype:
			while isinstance(etype, list): etype = etype[0]
			etype = ttl_spl_str(etype)
			if etype in class_names: etype = "Concept"
			new['@type'] = etype
		for entry_key, entry_value in entry.items():
			if entry_key == '@type': continue
			newkey = ttl_spl_str(entry_key)
			newval = entry_value
			split_val = not newkey.startswith('@')
			delistify = newkey not in ["broader"]
			if delistify: 
				while isinstance(newval, list): newval = newval[0]
			if isinstance(newval, dict):
				if '@id' in newval: split_val = False
				newval = newval.get('@value') or newval.get('@id') or newval
				if isinstance(newval, dict):
					if len(newval) > 0: newval = newval.values()[0]
			if delistify:
				while isinstance(newval, list): newval = newval[0]
			if split_val and delistify: newval = ttl_spl_str(newval)
			new[newkey] = newval
		parsed.append(new)
	return parsed

def ttl_spl_str(data_str: str) -> str:
	"""
	ttls json exports misslabel keys with full urls, and we only want the 
	key part, not the full url
	"""
	splitstr = data_str.split('#')
	if len(splitstr) > 1:
		return splitstr[-1]
	return data_str

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
			