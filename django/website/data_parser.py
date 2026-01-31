import uuid, datetime, json
from uuid import UUID

from .forms.names import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from django.db.models.manager import ManyToManyRelatedManager

def api_submission_to_formdict(item: dict) -> dict:
	"""
	Convert the REST API submission schema into the form-compatible dict
	expected by handle_submission_data.
	"""
	if not isinstance(item, dict):
		raise ValueError("Each submission must be a JSON object.")

	def require(key: str, label: str | None = None):
		val = item.get(key)
		if val is None or (isinstance(val, str) and not val.strip()):
			raise ValueError(f"Missing required field '{label or key}'.")
		return val

	def full_name(person: dict) -> str:
		first = person.get("firstName")
		last = person.get("lastName")
		if not first or not last:
			raise ValueError("Submitter/author person must include 'firstName' and 'lastName'.")
		return f"{first} {last}".strip()

	form: dict = {}

	# required fields
	submitter_list = require("submitter")
	if not isinstance(submitter_list, list) or len(submitter_list) < 1:
		raise ValueError("Field 'submitter' must be a non-empty array.")
	submitter = submitter_list[0]
	if not isinstance(submitter, dict):
		raise ValueError("Submitter entries must be objects.")
	submitter_person = submitter.get("person")
	if not isinstance(submitter_person, dict):
		raise ValueError("Submitter must include a 'person' object.")
	submitter_emails: list[str] = []
	for submitter_entry in submitter_list:
		if not isinstance(submitter_entry, dict):
			raise ValueError("Submitter entries must be objects.")
		email = submitter_entry.get(ROW_SUBMITTER_EMAIL)
		if not email:
			raise ValueError("Each submitter must include 'email'.")
		submitter_emails.append(email)

	form[FIELD_SUBMITTERNAME] = {
		FIELD_SUBMITTERNAME: full_name(submitter_person),
		FIELD_SUBMITTEREMAIL: json.dumps(submitter_emails),
	}

	form[FIELD_SOFTWARENAME] = require(FIELD_SOFTWARENAME)
	code_repo = item.get(ROW_SOFTWARE_CODEREPOSITORYURL)
	if not code_repo:
		raise ValueError("Missing required field 'codeRepositoryUrl'.")
	form[FIELD_CODEREPOSITORYURL] = code_repo
	form[FIELD_DESCRIPTION] = require(FIELD_DESCRIPTION)

	# authors
	authors = require(FIELD_AUTHORS)
	if not isinstance(authors, list) or len(authors) < 1:
		raise ValueError("Field 'authors' must be a non-empty array.")
	form_authors: list[dict] = []
	for author in authors:
		if not isinstance(author, dict):
			raise ValueError("Author entries must be objects.")
		author_entry = {
			FIELD_AUTHORS: full_name(author),
		}
		author_identifier = author.get(ROW_PERSON_IDENTIFIER)
		if author_identifier:
			author_entry[FIELD_AUTHORIDENTIFIER] = author_identifier
		affiliations = author.get(ROW_PERSON_AFFILIATION, [])
		if not isinstance(affiliations, list):
			raise ValueError(f"Author '{ROW_PERSON_AFFILIATION}' must be an array when provided.")
		if affiliations:
			affil_entries: list[dict] = []
			for affil in affiliations:
				if not isinstance(affil, dict):
					raise ValueError("Affiliation entries must be objects.")
				affil_name = affil.get(ROW_ORGANIZATION_NAME)
				if not affil_name:
					raise ValueError("Affiliation must include 'name'.")
				affil_entry = {FIELD_AUTHORAFFILIATION: affil_name}
				affil_ident = affil.get(ROW_ORGANIZATION_IDENTIFIER)
				if affil_ident:
					affil_entry[FIELD_AUTHORAFFILIATIONIDENTIFIER] = affil_ident
				affil_entries.append(affil_entry)
			author_entry[FIELD_AUTHORAFFILIATION] = affil_entries
		form_authors.append(author_entry)
	form[FIELD_AUTHORS] = form_authors

	# recommended/optional fields
	form[FIELD_CONCISEDESCRIPTION] = item.get(FIELD_CONCISEDESCRIPTION)
	form[FIELD_DOCUMENTATION] = item.get(FIELD_DOCUMENTATION)
	form[FIELD_PERSISTENTIDENTIFIER] = item.get(FIELD_PERSISTENTIDENTIFIER)
	form[FIELD_PUBLICATIONDATE] = item.get(FIELD_PUBLICATIONDATE)
	form[FIELD_REFERENCEPUBLICATION] = item.get(FIELD_REFERENCEPUBLICATION)
	form[FIELD_LICENSEFILEURL] = item.get(FIELD_LICENSEFILEURL)
	form[FIELD_LOGO] = item.get(FIELD_LOGO)

	publisher = item.get(FIELD_PUBLISHER) or {}
	if isinstance(publisher, dict) and publisher:
		form[FIELD_PUBLISHER] = {
			FIELD_PUBLISHER: publisher.get(ROW_ORGANIZATION_NAME) or "",
			FIELD_PUBLISHERIDENTIFIER: publisher.get(FIELD_PUBLISHERIDENTIFIER),
		}
	else:
		form[FIELD_PUBLISHER] = {FIELD_PUBLISHER: ""}

	license_field = item.get(FIELD_LICENSE)
	if isinstance(license_field, str):
		form[FIELD_LICENSE] = {FIELD_LICENSE: license_field}
	elif isinstance(license_field, dict) and license_field:
		form[FIELD_LICENSE] = {
			FIELD_LICENSE: license_field.get(ROW_LICENSE_NAME),
			FIELD_LICENSEURI: license_field.get(ROW_LICENSE_URL),
		}
	else:
		form[FIELD_LICENSE] = {}

	version = item.get(ROW_SOFTWARE_VERSION)
	if isinstance(version, dict) and version:
		form[FIELD_VERSIONNUMBER] = {
			FIELD_VERSIONNUMBER: version.get(ROW_VERSION_NUMBER),
			FIELD_VERSIONDATE: version.get(ROW_VERSION_DATE),
			FIELD_VERSIONDESCRIPTION: version.get(ROW_VERSION_DESCRIPTION),
			FIELD_VERSIONPID: version.get(ROW_VERSION_PID),
		}

	def list_or_empty(key: str) -> list:
		val = item.get(key, [])
		return val if isinstance(val, list) else []

	form[FIELD_PROGRAMMINGLANGUAGE] = list_or_empty(FIELD_PROGRAMMINGLANGUAGE)
	form[FIELD_SOFTWAREFUNCTIONALITY] = list_or_empty(FIELD_SOFTWAREFUNCTIONALITY)
	form[FIELD_DATASOURCES] = list_or_empty(FIELD_DATASOURCES)
	form[FIELD_INPUTFORMATS] = list_or_empty(FIELD_INPUTFORMATS)
	form[FIELD_OUTPUTFORMATS] = list_or_empty(FIELD_OUTPUTFORMATS)
	form[FIELD_CPUARCHITECTURE] = list_or_empty(FIELD_CPUARCHITECTURE)
	form[FIELD_OPERATINGSYSTEM] = list_or_empty(FIELD_OPERATINGSYSTEM)
	form[FIELD_RELATEDREGION] = list_or_empty(FIELD_RELATEDREGION)
	form[FIELD_RELATEDPHENOMENA] = list_or_empty(FIELD_RELATEDPHENOMENA)
	form[FIELD_KEYWORDS] = list_or_empty(FIELD_KEYWORDS)
	form[FIELD_RELATEDPUBLICATIONS] = list_or_empty(FIELD_RELATEDPUBLICATIONS)
	form[FIELD_RELATEDDATASETS] = list_or_empty(FIELD_RELATEDDATASETS)
	form[FIELD_RELATEDSOFTWARE] = list_or_empty(FIELD_RELATEDSOFTWARE)
	form[FIELD_INTEROPERABLESOFTWARE] = list_or_empty(FIELD_INTEROPERABLESOFTWARE)

	relinstruments = list_or_empty(FIELD_RELATEDINSTRUMENTS)
	form_relinstruments: list[dict] = []
	for instr in relinstruments:
		if not isinstance(instr, dict):
			raise ValueError("Related instrument entries must be objects.")
		form_relinstruments.append({
			FIELD_RELATEDINSTRUMENTS: instr.get(ROW_CONTROLLEDLIST_NAME),
			FIELD_RELATEDINSTRUMENTIDENTIFIER: instr.get(ROW_CONTROLLEDLIST_IDENTIFIER),
		})
	form[FIELD_RELATEDINSTRUMENTS] = form_relinstruments

	relobservatories = list_or_empty(FIELD_RELATEDOBSERVATORIES)
	form_relobservatories: list[dict] = []
	for obs in relobservatories:
		if not isinstance(obs, dict):
			raise ValueError("Related observatory entries must be objects.")
		form_relobservatories.append({
			FIELD_RELATEDOBSERVATORIES: obs.get(ROW_CONTROLLEDLIST_NAME),
			FIELD_RELATEDINSTRUMENTIDENTIFIER: obs.get(ROW_CONTROLLEDLIST_IDENTIFIER),
		})
	form[FIELD_RELATEDOBSERVATORIES] = form_relobservatories

	funders = list_or_empty(FIELD_FUNDER)
	form_funders: list[dict] = []
	for funder in funders:
		if not isinstance(funder, dict):
			raise ValueError("Funder entries must be objects.")
		form_funders.append({
			FIELD_FUNDER: funder.get(ROW_ORGANIZATION_NAME),
			FIELD_FUNDERIDENTIFIER: funder.get(ROW_ORGANIZATION_IDENTIFIER),
		})
	form[FIELD_FUNDER] = form_funders

	awards = list_or_empty(FIELD_AWARDTITLE)
	form_awards: list[dict] = []
	for award in awards:
		if not isinstance(award, dict):
			raise ValueError("Award entries must be objects.")
		form_awards.append({
			FIELD_AWARDTITLE: award.get(ROW_CONTROLLEDLIST_NAME),
			FIELD_AWARDNUMBER: award.get(ROW_CONTROLLEDLIST_IDENTIFIER),
		})
	form[FIELD_AWARDTITLE] = form_awards

	return form

def parse_organization(
	data: dict, 
	name_field: str, 
	ident_field: str,
	allow_creation: bool = True
) -> Organization:
	"""
	parse a data dict representing an organization model object, given field 
	names for the organization name and the organization's identifier  
	Parameters:
		data: the key-value pairs representing the organization object
		name_field: the name of the key for the organization's name
		ident_field: the name of the key for the organization's identifier
	"""
	org_name: str = data.get(name_field)
	if not org_name: return None

	# first test to see if organization top field is uuid and return the object
	# it references if so
	try:
		uid = UUID(org_name)
		org_ref = Organization.objects.get(pk=uid)
		return org_ref
	
	except:
		org_ident = data.get(ident_field)
		org_ref: Organization = None

		# look for an return an organization with matching identifier if exists
		if org_ident: org_ref = Organization.objects.filter(identifier=org_ident).first()
		if not org_ref: org_ref = Organization.objects.filter(name=org_name).first()
		if org_ref: return org_ref

		# build new org object from data
		elif allow_creation:
			organization = Organization()
			org_abbrev_match = PARENTHESIS_MATCH.findall(org_name)
			org_name = PARENTHESIS_MATCH.sub(org_name, "")
			organization.name = org_name

			# infer abbreviation from parenthesis
			if org_abbrev_match:
				org_abbrev = ", ".join(org_abbrev_match)
				organization.abbreviation = org_abbrev

			if org_ident: organization.identifier = org_ident
			organization.save()
			return organization
	
	# returns none if no reference is found and creation of new orgs is disallowed
	return None

def parse_person(
	data: dict, 
	name_field: str, ident_field: str, 
	affil_field: str, affil_ident_field: str
) -> Person:
	
	person: Person = None
	person_match: Person = None
	person_identifier = data.get(ident_field)

	# first see if author field was passed as a uuid
	person_name: str = data.get(name_field)
	try:
		person_uid = UUID(person_name)
		person_match = Person.objects.get(pk=person_uid)
		return person_match
	except: person_match = None

	# if not, see if we can match an author with the same identifier
	if person_identifier: 
		person_match = Person.objects.filter(identifier=person_identifier).first()

	# if there's an author match, no need to create a new object
	if person_match: person = person_match

	# if no match, create new person object
	else:
		person = Person()
		person.identifier = person_identifier
		person_spl: str = person_name.split(',')
		lastname = ""
		firstname = ""
		if len(person_spl) > 1:
			firstname = person_spl[-1]
			lastname = person_spl[0]
		else:
			lastname = person_name.split()[-1]
			firstname = person_name.replace(lastname, '').strip()
		person.lastName = lastname
		person.firstName = firstname
		person.save()

	# add affiliation datas
	affiliation_datas: dict = data.get(affil_field)
	if affiliation_datas:
		for affiliation_data in affiliation_datas:
			affil = parse_organization(affiliation_data, affil_field, affil_ident_field)
			if affil: person.affiliation.add(affil)

	person.save()
	return person

def parse_controlled_list(
		target_model: type[ControlledList],
		name: str = None, 
		identifier: str = None,
		definition: str = None,
		allow_creation: bool = False,
		name_match_fallback: bool = True,
	) -> ControlledList:

	# see if the name field is acting as a uuid reference, and return referenced object if so
	try:
		uuid = UUID(name)
		reference_object = target_model.objects.get(pk=uuid)
		return reference_object
	
	except:
		
		reference_object: ControlledList = None

		# look for object with matching identifier and return it if found
		if identifier: reference_object = target_model.objects.filter(identifier=identifier).first()

		# fallback to looking up by name if allowed
		if not reference_object and (not identifier or name_match_fallback):
			reference_object = target_model.objects.filter(name=name).first()
		
		if reference_object: return reference_object

		# create new object if no object with matching identifier exists
		if allow_creation:
			obj = target_model()
			if name: obj.name = name
			if identifier: obj.identifier = identifier
			if definition: obj.definition = definition
			obj.save()
			return obj

		else:
			raise Exception(f"{target_model.__name__} does not contain '{name or identifier}'")
	
	# if no references were found and creation of new object is not allowed
	return None

def apply_software_core_fields(software: Software, data: dict) -> None:
	"""Populate core scalar Software fields directly from submission data."""
	software.persistentIdentifier = data.get(FIELD_PERSISTENTIDENTIFIER)
	software.codeRepositoryUrl = data.get(FIELD_CODEREPOSITORYURL)
	software.softwareName = data.get(FIELD_SOFTWARENAME)
	software.description = data.get(FIELD_DESCRIPTION)
	software.conciseDescription = data.get(FIELD_CONCISEDESCRIPTION)
	software.documentation = data.get(FIELD_DOCUMENTATION)

def apply_reference_publication(software: Software, data: dict) -> None:
	"""Resolve and assign the reference publication RelatedItem by identifier."""
	identifier = data.get(FIELD_REFERENCEPUBLICATION)
	if not identifier: return

	refpub: RelatedItem = parse_controlled_list(
		RelatedItem, 
		identifier=identifier, 
		allow_creation=True
	)

	if not refpub.name:
		refpub.name = "UNKNOWN"
		refpub.identifier = identifier
		refpub.type = RelatedItemType.PUBLICATION
		refpub.save()
	
	software.referencePublication = refpub

def apply_development_status(software: Software, data: dict) -> None:
	"""Resolve and assign Software.developmentStatus from RepoStatus."""
	devstatus: str = data.get(FIELD_DEVELOPMENTSTATUS)
	if devstatus:
		software.developmentStatus = parse_controlled_list(
			RepoStatus,
			devstatus,
			name_match_fallback=True
		)

def apply_logo(software: Software, data: dict) -> None:
	"""Resolve or create an Image from logo URL and assign Software.logo."""
	logo_url = data.get(FIELD_LOGO)
	if not logo_url: return

	img = Image.objects.filter(url=logo_url).first()
	if not img:
		img = Image()
		img.description = f"logo for {software.softwareName}"
		img.url = logo_url
		img.save()
	software.logo = img

def split_firstname_lastname(submitter_name: str) -> tuple[str, str]:
	"""Parse submitter full name into (first_name, last_name)."""
	submitter_lastname = submitter_name.split()[-1]
	submitter_firstname = submitter_name.replace(submitter_lastname, '').strip()
	return submitter_firstname, submitter_lastname

def resolve_submitter(data: dict) -> Submitter:
	"""Resolve a Submitter and associated Person from submitter data."""
	submitter_data: dict = data.get(FIELD_SUBMITTERNAME)
	submitter_name: str = submitter_data.get(FIELD_SUBMITTERNAME)
	submitter_firstname, submitter_lastname = split_firstname_lastname(submitter_name)
	submitter_email = submitter_data.get(FIELD_SUBMITTEREMAIL)

	# here we look for a submitter with the same email, then we verify it has 
	# the same name also, if both the email and the name match, the 
	# corresponding submitter object is returned, otherwise a new Submitter 
	# object is entered into the database
	submitter_found = Submitter.objects.filter(email=submitter_email).first()
	if submitter_found:
		sub_person_found = Person.objects.filter(
			firstName=submitter_found.person.firstName,
			lastName=submitter_found.person.lastName
		)
		success = False
		for person in sub_person_found:
			if person.pk == submitter_found.person.pk:
				success = True
				print(f"found existing submitter for {submitter_found.email}")
				break
		if not success:
			submitter_found = None

	if submitter_found:
		return submitter_found

	submitter_person = Person()
	submitter_person.lastName = submitter_lastname
	submitter_person.firstName = submitter_firstname
	submitter_person.save()

	submitter = Submitter()
	submitter.person = submitter_person
	submitter.email = submitter_email
	submitter.save()
	return submitter

def build_submission_info(data: dict) -> SubmissionInfo:
	"""Create and return a SubmissionInfo with resolved submitter."""
	submission = SubmissionInfo()
	submission.submitter = resolve_submitter(data)
	submission.dateModified = date.today()
	submission.modificationDescription = "Initial submission"
	submission.metadataVersionNumber = "0.1.0"
	submission.submissionDate = date.today()
	submission.internalStatusNote = "Not assigned or reviewed"
	submission.save()
	return submission

def apply_license(software: Software, data: dict) -> None:
	"""Resolve and assign Software.license from submission license data."""
	license_data: dict = data.get(FIELD_LICENSE)
	if not license_data: return

	license_name: str = license_data.get(FIELD_LICENSE)
	try:
		uid = UUID(license_name)
		license = License.objects.get(pk=uid)
		software.license = license
		return
	except Exception:
		pass

	license = None
	if license_name and license_name.upper() != "OTHER":
		license = License.objects.filter(name=license_name).first()
	if not license:
		license_url = license_data.get(FIELD_LICENSEURI)
		license = License.objects.filter(url=license_url).first()
	if license:
		software.license = license
		return

	license_url = license_data.get(FIELD_LICENSEURI)
	if license_url:
		license = License()
		license.name = "Other"
		license.url = license_data.get(FIELD_LICENSEURI)
		license.save()
		software.license = license
		print(f"LICENSE SAVED: {software.license.id}")
	else:
		software.license = License.get_other_licence()

def apply_publisher(software: Software, data: dict) -> None:
	"""Resolve and assign Software.publisher from publisher data."""
	publisher_data: dict = data.get(FIELD_PUBLISHER)
	if not publisher_data: return

	publisher_name: str = publisher_data.get(FIELD_PUBLISHER)
	if publisher_name.lower() == "zenodo":
		software.publisher = Organization.objects.filter(name="Zenodo").first()
	else:
		software.publisher = parse_organization(
			publisher_data,
			FIELD_PUBLISHER,
			FIELD_PUBLISHERIDENTIFIER
		)

def apply_version(software: Software, data: dict) -> None:
	"""Create and assign SoftwareVersion from version data."""
	version_data: dict = data.get(FIELD_VERSIONNUMBER)
	if not version_data: return

	version = SoftwareVersion()
	version.number = version_data.get(FIELD_VERSIONNUMBER)

	version_date = version_data.get(FIELD_VERSIONDATE)
	if version_date:
		version_date = datetime.datetime.strptime(version_date, '%Y-%m-%d').date()
		version.release_date = version_date

	version.description = version_data.get(FIELD_VERSIONDESCRIPTION)
	version.version_pid = version_data.get(FIELD_VERSIONPID)
	version.save()
	software.version = version

def apply_authors(software: Software, data: dict) -> None:
	"""Replace Software.authors from submission author data."""
	author_datas: list[dict] = data.get(FIELD_AUTHORS)
	if not author_datas: return

	software.authors.clear()
	for author_data in author_datas:
		author = parse_person(
			author_data,
			FIELD_AUTHORS, FIELD_AUTHORIDENTIFIER,
			FIELD_AUTHORAFFILIATION, FIELD_AUTHORAFFILIATIONIDENTIFIER
		)
		software.authors.add(author)

def apply_publication_date(software: Software, data: dict) -> None:
	"""Parse and set Software.publicationDate from submission data."""
	pub_date = data.get(FIELD_PUBLICATIONDATE)
	if not pub_date: return

	pub_date = datetime.datetime.strptime(pub_date, '%Y-%m-%d').date()
	software.publicationDate = pub_date

def apply_controlled_m2m(
	software: Software,
	data: dict,
	field_key: str,
	target_model: type[ControlledList],
	m2m_attr: str,
	allow_creation: bool = False,
) -> None:
	"""Replace a Software M2M controlled-list field with resolved references."""
	values = data.get(field_key)
	if not values: return

	m2m_manager: ManyToManyRelatedManager = getattr(software, m2m_attr)
	m2m_manager.clear()
	for value in values:
		obj = parse_controlled_list(target_model, value, allow_creation=allow_creation)
		if obj: m2m_manager.add(obj)

def apply_function_category(software: Software, fullnames: list[str]):
	"""
	Adds each specified FunctionCategory to the software submission. The 
	fullnames should be in the format "Parent Name: Child Name", or just 
	"Child Name" if it has no parent. The list can also contain UUID stings 
	that correlate to a specific FunctionCategory item UUID
	
	:param software: The software submission entry to apply the function 
		categories to
	:type software: Software
	:param fullnames: list of full function names to apply the function 
		categories to, can also be UUIDs
	:type fullnames: list[str]
	"""

	categories: list[FunctionCategory] = []
	for fullname in fullnames:
		subnames = fullname.split(":")
		subnames.reverse()
		child_name = subnames[0].strip()
		child_matches = FunctionCategory.objects.filter(name=child_name)
		ref_category: FunctionCategory = None

		# top level category names should be unique
		if len(subnames) == 1:
			ref_category = child_matches.first()

		# if parent name is specified, narrow down to specific category with 
		# matching name and parent
		elif len(subnames) == 2:
			parent_name = subnames[1].strip()
			ref_category = FunctionCategory.objects.filter(
				name=parent_name, 
				children__in=child_matches
			).first()

		# append the found category if it exists
		if(ref_category): categories.append(ref_category)
		else: raise Exception(f"{FunctionCategory.__name__} '{fullname}' does not exist")

	# apply categories to entry
	software.softwareFunctionality.set(categories)

def apply_keywords(software: Software, data: dict) -> None:
	"""Replace Software.keywords with Keyword references, creating when needed."""
	keywords: list[str] = data.get(FIELD_KEYWORDS)
	if not keywords: return

	software.keywords.clear()
	for kw in keywords:
		kw_obj = parse_controlled_list(Keyword, kw, allow_creation=False)
		if kw_obj:
			software.keywords.add(kw_obj)
			continue

		kw_fmtd = SPACE_REPLACE.sub(' ', kw).lower()
		kw_obj = parse_controlled_list(Keyword, name=kw_fmtd, allow_creation=True)
		software.keywords.add(kw_obj)

def apply_awards(software: Software, data: dict) -> None:
	"""Replace Software.award with Award references, creating when needed."""
	award_datas: list[dict] = data.get(FIELD_AWARDTITLE)
	if not award_datas: return

	software.award.clear()
	for award_data in award_datas:
		award_name = award_data.get(FIELD_AWARDTITLE)
		if not award_name: continue
		try:
			uid = UUID(award_name)
			software.award.add(Award.objects.get(pk=uid))
		except Exception:
			award_num = award_data.get(FIELD_AWARDNUMBER)
			award_ref = Award.objects.filter(identifier=award_num).first()
			if award_ref:
				software.award.add(award_ref)
			else:
				award = Award()
				award.name = award_name
				award.identifier = award_num
				award.save()
				software.award.add(award)

def apply_funders(software: Software, data: dict) -> None:
	"""Replace Software.funder with Organization references."""
	funder_datas: list[dict] = data.get(FIELD_FUNDER)
	if not funder_datas: return

	software.funder.clear()
	for funder_data in funder_datas:
		funder = parse_organization(funder_data, FIELD_FUNDER, FIELD_FUNDERIDENTIFIER)
		if funder: software.funder.add(funder)

def apply_related_items(
	software: Software,
	items: list[str | dict],
	m2m_attr: str,
	item_type: RelatedItemType,
) -> None:
	"""Replace a RelatedItem M2M field with resolved references of a given type."""
	if not items: return

	m2m_manager: ManyToManyRelatedManager = getattr(software, m2m_attr)
	m2m_manager.clear()
	for item in items:

		identifier = item
		name = None
		if isinstance(item, dict):
			name = item.get(ROW_CONTROLLEDLIST_NAME)
			identifier = item.get(ROW_AWARD_IDENTIFIER)

		rel_item: RelatedItem = parse_controlled_list(
			RelatedItem, 
			name=name,
			identifier=identifier,
			allow_creation=True,
			name_match_fallback=True
		)
		if not rel_item.name:
			rel_item.type = item_type.value if hasattr(item_type, "value") else item_type
			rel_item.name= "UNKNOWN"
			rel_item.save()
		m2m_manager.add(rel_item)

def apply_related_instruments(software: Software, data: dict) -> None:
	"""Replace Software.relatedInstruments with resolved instrument records."""
	relinstr_datas: list[dict] = data.get(FIELD_RELATEDINSTRUMENTS)
	if not relinstr_datas: return

	software.relatedInstruments.clear()
	for relinstr_data in relinstr_datas:
		instr_name = relinstr_data.get(FIELD_RELATEDINSTRUMENTS)
		try:
			uid = UUID(instr_name)
			software.relatedInstruments.add(InstrumentObservatory.objects.get(pk=uid))
		except Exception:
			instr_ident = relinstr_data.get(FIELD_RELATEDINSTRUMENTIDENTIFIER)
			instr_ref = None
			if instr_ident:
				instr_ref = InstrumentObservatory.objects.filter(identifier=instr_ident).first()
			if instr_ref:
				software.relatedInstruments.add(instr_ref)
			else:
				instr = InstrumentObservatory()
				instr.name = instr_name or "UNKNOWN"
				instr.identifier = instr_ident
				instr.type = InstrObsType.INSTRUMENT.value
				instr.save()
				software.relatedInstruments.add(instr)

def apply_related_observatories(software: Software, data: dict) -> None:
	"""Replace Software.relatedObservatories with resolved observatory records."""
	relobs_datas: list[dict] = data.get(FIELD_RELATEDOBSERVATORIES)
	if not relobs_datas: return

	software.relatedObservatories.clear()
	for relobs_data in relobs_datas:
		if isinstance(relobs_data, dict):
			obs_name = relobs_data.get(FIELD_RELATEDOBSERVATORIES)
		else:
			obs_name = relobs_data
		try:
			uid = UUID(obs_name)
			software.relatedObservatories.add(InstrumentObservatory.objects.get(pk=uid))
		except Exception:
			# TODO FIELD_RELATEDOBSERVATORYIDENTIFIER
			obs_ident = None
			if isinstance(relobs_data, dict):
				obs_ident = relobs_data.get(FIELD_RELATEDINSTRUMENTIDENTIFIER)
			obs_ref = None
			if obs_ident:
				obs_ref = InstrumentObservatory.objects.filter(identifier=obs_ident).first()
			if obs_ref:
				software.relatedObservatories.add(obs_ref)
			else:
				obs = InstrumentObservatory()
				obs.name = obs_name or "UNKNOWN"
				obs.identifier = obs_ident
				obs.type = InstrObsType.OBSERVATORY.value
				obs.save()
				software.relatedObservatories.add(obs)

def handle_submission_data(data: dict, software_target: Software = None) -> uuid.UUID:
	"""Store submission data in the specified software target."""
	software = software_target
	if not software:
		software = Software()

	apply_software_core_fields(software, data)
	apply_reference_publication(software, data)
	apply_development_status(software, data)
	apply_logo(software, data)

	submission = build_submission_info(data)
	software.submissionInfo = submission

	apply_license(software, data)
	apply_publisher(software, data)
	apply_version(software, data)

	# ensure Software is saved before any M2M assignments
	software.save()

	apply_authors(software, data)
	apply_publication_date(software, data)
	apply_controlled_m2m(
		software, data,
		FIELD_PROGRAMMINGLANGUAGE, 
		ProgrammingLanguage,
		FIELD_PROGRAMMINGLANGUAGE,
	)
	apply_function_category(software, data[FIELD_SOFTWAREFUNCTIONALITY])
	apply_controlled_m2m(
		software, data,
		FIELD_DATASOURCES, DataInput,
		FIELD_DATASOURCES,
	)
	apply_controlled_m2m(
		software, data,
		FIELD_INPUTFORMATS, FileFormat,
		FIELD_INPUTFORMATS,
	)
	apply_controlled_m2m(
		software, data,
		FIELD_OUTPUTFORMATS, FileFormat,
		FIELD_OUTPUTFORMATS,
	)
	apply_controlled_m2m(
		software, data,
		FIELD_CPUARCHITECTURE, CpuArchitecture,
		FIELD_CPUARCHITECTURE,
	)
	apply_controlled_m2m(
		software, data,
		FIELD_OPERATINGSYSTEM, OperatingSystem,
		FIELD_OPERATINGSYSTEM,
	)
	apply_controlled_m2m(
		software, data,
		FIELD_RELATEDREGION, Region,
		FIELD_RELATEDREGION,
	)
	apply_controlled_m2m(
		software, data,
		FIELD_RELATEDPHENOMENA, Phenomena,
		FIELD_RELATEDPHENOMENA,
	)
	apply_keywords(software, data)
	apply_awards(software, data)
	apply_funders(software, data)
	apply_related_items(
		software, data.get(FIELD_RELATEDPUBLICATIONS),
		FIELD_RELATEDPUBLICATIONS,
		RelatedItemType.PUBLICATION,
	)
	apply_related_items(
		software, data.get(FIELD_RELATEDDATASETS),
		FIELD_RELATEDDATASETS,
		RelatedItemType.DATASET,
	)
	apply_related_items(
		software, data.get(FIELD_RELATEDSOFTWARE),
		FIELD_RELATEDSOFTWARE,
		RelatedItemType.SOFTWARE,
	)
	apply_related_items(
		software, data.get(FIELD_INTEROPERABLESOFTWARE),
		FIELD_INTEROPERABLESOFTWARE,
		RelatedItemType.SOFTWARE,
	)
	apply_related_instruments(software, data)
	apply_related_observatories(software, data)

	software.save()
	return submission.id
