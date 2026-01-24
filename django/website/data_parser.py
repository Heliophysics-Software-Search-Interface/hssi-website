import uuid, datetime, json
from uuid import UUID

from .forms.names import *

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
		email = submitter_entry.get("email")
		if not email:
			raise ValueError("Each submitter must include 'email'.")
		submitter_emails.append(email)

	form[FIELD_SUBMITTERNAME] = {
		FIELD_SUBMITTERNAME: full_name(submitter_person),
		FIELD_SUBMITTEREMAIL: json.dumps(submitter_emails),
	}

	form[FIELD_SOFTWARENAME] = require("softwareName")
	code_repo = item.get("codeRepositoryUrl")
	if not code_repo:
		code_repo = item.get("codeRepositoryURL")
	if not code_repo:
		raise ValueError("Missing required field 'codeRepositoryUrl'.")
	form[FIELD_CODEREPOSITORYURL] = code_repo
	form[FIELD_DESCRIPTION] = require("description")

	# authors
	authors = require("authors")
	if not isinstance(authors, list) or len(authors) < 1:
		raise ValueError("Field 'authors' must be a non-empty array.")
	form_authors: list[dict] = []
	for author in authors:
		if not isinstance(author, dict):
			raise ValueError("Author entries must be objects.")
		author_entry = {
			FIELD_AUTHORS: full_name(author),
		}
		author_identifier = author.get("identifier")
		if author_identifier:
			author_entry[FIELD_AUTHORIDENTIFIER] = author_identifier
		affiliations = author.get("affiliation", [])
		if affiliations is None:
			affiliations = []
		if not isinstance(affiliations, list):
			raise ValueError("Author 'affiliation' must be an array when provided.")
		if affiliations:
			affil_entries: list[dict] = []
			for affil in affiliations:
				if not isinstance(affil, dict):
					raise ValueError("Affiliation entries must be objects.")
				affil_name = affil.get("name")
				if not affil_name:
					raise ValueError("Affiliation must include 'name'.")
				affil_entry = {FIELD_AUTHORAFFILIATION: affil_name}
				affil_ident = affil.get("identifier")
				if affil_ident:
					affil_entry[FIELD_AUTHORAFFILIATIONIDENTIFIER] = affil_ident
				affil_entries.append(affil_entry)
			author_entry[FIELD_AUTHORAFFILIATION] = affil_entries
		form_authors.append(author_entry)
	form[FIELD_AUTHORS] = form_authors

	# recommended/optional fields
	form[FIELD_CONCISEDESCRIPTION] = item.get("conciseDescription")
	form[FIELD_DOCUMENTATION] = item.get("documentation")
	form[FIELD_PERSISTENTIDENTIFIER] = item.get("persistentIdentifier")
	form[FIELD_PUBLICATIONDATE] = item.get("publicationDate")
	form[FIELD_REFERENCEPUBLICATION] = item.get("referencePublication")
	form[FIELD_LICENSEFILEURL] = item.get("licenseFileUrl")
	form[FIELD_LOGO] = item.get("logo")

	publisher = item.get("publisher") or {}
	if isinstance(publisher, dict) and publisher:
		form[FIELD_PUBLISHER] = {
			FIELD_PUBLISHER: publisher.get("name") or "",
			FIELD_PUBLISHERIDENTIFIER: publisher.get("identifier"),
		}
	else:
		form[FIELD_PUBLISHER] = {FIELD_PUBLISHER: ""}

	license_field = item.get("license")
	if isinstance(license_field, str):
		form[FIELD_LICENSE] = {FIELD_LICENSE: license_field}
	elif isinstance(license_field, dict) and license_field:
		form[FIELD_LICENSE] = {
			FIELD_LICENSE: license_field.get("name"),
			FIELD_LICENSEURI: license_field.get("url"),
		}
	else:
		form[FIELD_LICENSE] = {}

	version = item.get("version")
	if isinstance(version, dict) and version:
		form[FIELD_VERSIONNUMBER] = {
			FIELD_VERSIONNUMBER: version.get("number"),
			FIELD_VERSIONDATE: version.get("release_date"),
			FIELD_VERSIONDESCRIPTION: version.get("description"),
			FIELD_VERSIONPID: version.get("version_pid"),
		}

	def list_or_empty(key: str) -> list:
		val = item.get(key, [])
		return val if isinstance(val, list) else []

	form[FIELD_PROGRAMMINGLANGUAGE] = list_or_empty("programmingLanguage")
	form[FIELD_SOFTWAREFUNCTIONALITY] = list_or_empty("softwareFunctionality")
	form[FIELD_DATASOURCES] = list_or_empty("dataSources")
	form[FIELD_INPUTFORMATS] = list_or_empty("inputFormats")
	form[FIELD_OUTPUTFORMATS] = list_or_empty("outputFormats")
	form[FIELD_CPUARCHITECTURE] = list_or_empty("cpuArchitecture")
	form[FIELD_OPERATINGSYSTEM] = list_or_empty("operatingSystem")
	form[FIELD_RELATEDREGION] = list_or_empty("relatedRegion")
	form[FIELD_RELATEDPHENOMENA] = list_or_empty("relatedPhenomena")
	form[FIELD_KEYWORDS] = list_or_empty("keywords")
	form[FIELD_RELATEDPUBLICATIONS] = list_or_empty("relatedPublications")
	form[FIELD_RELATEDDATASETS] = list_or_empty("relatedDatasets")
	form[FIELD_RELATEDSOFTWARE] = list_or_empty("relatedSoftware")
	form[FIELD_INTEROPERABLESOFTWARE] = list_or_empty("interoperableSoftware")

	relinstruments = list_or_empty("relatedInstruments")
	form_relinstruments: list[dict] = []
	for instr in relinstruments:
		if not isinstance(instr, dict):
			raise ValueError("Related instrument entries must be objects.")
		form_relinstruments.append({
			FIELD_RELATEDINSTRUMENTS: instr.get("name"),
			FIELD_RELATEDINSTRUMENTIDENTIFIER: instr.get("identifier"),
		})
	form[FIELD_RELATEDINSTRUMENTS] = form_relinstruments

	relobservatories = list_or_empty("relatedObservatories")
	form_relobservatories: list[dict] = []
	for obs in relobservatories:
		if not isinstance(obs, dict):
			raise ValueError("Related observatory entries must be objects.")
		form_relobservatories.append({
			FIELD_RELATEDOBSERVATORIES: obs.get("name"),
			FIELD_RELATEDINSTRUMENTIDENTIFIER: obs.get("identifier"),
		})
	form[FIELD_RELATEDOBSERVATORIES] = form_relobservatories

	funders = list_or_empty("funder")
	form_funders: list[dict] = []
	for funder in funders:
		if not isinstance(funder, dict):
			raise ValueError("Funder entries must be objects.")
		form_funders.append({
			FIELD_FUNDER: funder.get("name"),
			FIELD_FUNDERIDENTIFIER: funder.get("identifier"),
		})
	form[FIELD_FUNDER] = form_funders

	awards = list_or_empty("award")
	form_awards: list[dict] = []
	for award in awards:
		if not isinstance(award, dict):
			raise ValueError("Award entries must be objects.")
		form_awards.append({
			FIELD_AWARDTITLE: award.get("name"),
			FIELD_AWARDNUMBER: award.get("identifier"),
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
	organization_name = data.get(name_field)
	if not organization_name: return None

	# first test to see if organization top field is uuid and return the object
	# it references if so
	try:
		uid = UUID(organization_name)
		org_ref = Organization.objects.get(pk=uid)
		return org_ref
	
	except:
		org_ident = data.get(ident_field)
		org_ref: Organization = None

		# look for an return an organization with matching identifier if exists
		if org_ident: org_ref = Organization.objects.filter(identifier=org_ident).first()
		if org_ref: return org_ref

		# build new org object from data
		elif allow_creation:
			organization = Organization()
			organization.name = organization_name
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
		data: dict, 
		name_field: str = None, 
		ident_field: str = None,
		definition_field: str = None,
		allow_creation: bool = True,
	) -> ControlledList:

	name = data.get(name_field)
	definition = data.get(definition_field)

	# see if the name field is acting as a uuid reference, and return referenced object if so
	try:
		uuid = UUID(name)
		reference_object = target_model.objects.get(pk=uuid)
		return reference_object
	
	except:
		ident = data.get(ident_field)
		reference_object: ControlledList = None

		# look for object with matching identifier and return it if found
		if ident: reference_object = target_model.objects.filter(identifier=ident).first()
		if reference_object: return reference_object

		# create new object if no object with matching identifier exists
		elif allow_creation:
			obj = target_model()
			if name: obj.name = name
			if ident: obj.identifier = ident
			if definition: obj.definition = definition
			obj.save()
			return obj
	
	# if no references were found and creation of new object is not allowed
	return None

def parse_controlled_list_reference(
		target_model: type[ControlledList],
		uid: str, 
	) -> ControlledList:

	if uid is None: return None

	# see if the uuid reference exists, and return referenced object if so
	try:
		uuid = UUID(uid)
		reference_object = target_model.objects.get(pk=uuid)
		return reference_object
	
	except:
		found_ref = target_model.objects.filter(name=uid).first()
		if found_ref: return found_ref
	
	return None

def handle_submission_data(data: dict, software_target: Software = None) -> uuid.UUID:
	""" store submission data in the specified software target """
	software = software_target
	if not software: software = Software()

	software.persistentIdentifier = data.get(FIELD_PERSISTENTIDENTIFIER)
	software.codeRepositoryUrl = data.get(FIELD_CODEREPOSITORYURL)
	software.softwareName = data.get(FIELD_SOFTWARENAME)
	software.description = data.get(FIELD_DESCRIPTION)
	software.conciseDescription = data.get(FIELD_CONCISEDESCRIPTION)
	software.documentation = data.get(FIELD_DOCUMENTATION)

	## REFERENCE PUBLICATION

	refpub = data.get(FIELD_REFERENCEPUBLICATION)
	if refpub:
		refpub_ref = RelatedItem.objects.filter(identifier=refpub).first()
		if refpub_ref: software.referencePublication = refpub_ref
		else:
			refpublication = RelatedItem()
			refpublication.name = "UNKNOWN"
			refpublication.identifier = refpub
			refpublication.type = RelatedItemType.PUBLICATION
			refpublication.save()
			software.referencePublication = refpublication

	## DEVELOPMENT STATUS

	software.developmentStatus = parse_controlled_list_reference(
		RepoStatus, 
		data.get(FIELD_DEVELOPMENTSTATUS)
	)
	
	## LOGO

	logo_url = data.get(FIELD_LOGO)
	if logo_url:
		img: Image = None
		img = Image.objects.filter(url=logo_url).first()
		if not img: 
			img = Image()
			img.description = f"logo for {software.softwareName}"
			img.url = logo_url
			img.save()
		software.logo = img

	## SUBMISSION
	
	submission = SubmissionInfo()

	submitter_data: dict = data.get(FIELD_SUBMITTERNAME)
	submitter_name: str = submitter_data.get(FIELD_SUBMITTERNAME)
	submitter_lastname = submitter_name.split()[-1]
	submitter_firstname = submitter_name.replace(submitter_lastname, '').strip()
	submitter_email = submitter_data.get(FIELD_SUBMITTEREMAIL)

	submitter_found: Submitter = Submitter.objects.filter(email=submitter_email).first()
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
		if not success: submitter_found = None
	
	submitter: Submitter = None
	if not submitter_found:
		submitter_person = Person()
		submitter_person.lastName = submitter_lastname
		submitter_person.firstName = submitter_firstname
		submitter_person.save()

		submitter = Submitter()
		submitter.person = submitter_person
		submitter.email = submitter_email
		submitter.save()
	else: submitter = submitter_found
	
	submission.submitter = submitter
	submission.dateModified = date.today()
	submission.modificationDescription = "Initial submission"
	submission.metadataVersionNumber = "0.1.0"
	submission.submissionDate = date.today()
	submission.internalStatusNote = "Not assigned or reviewed"

	submission.save()
	software.submissionInfo = submission

	## LICENSE

	license_data: dict = data.get(FIELD_LICENSE)
	if license_data:
		license_name: str = license_data.get(FIELD_LICENSE)
		try:
			uid = UUID(license_name)
			license = License.objects.get(pk=uid)
			software.license = license
		except Exception:
			license = None
			if license_name and license_name.upper() != "OTHER":
				license = License.objects.filter(name=license_name).first()
			if not license:
				license_url = license_data.get(FIELD_LICENSEURI)
				license = License.objects.filter(url=license_url).first()
			if license: software.license = license
			else:
				license_url = license_data.get(FIELD_LICENSEURI)
				if license_url:
					license = License()
					license.name = "Other"
					license.url = license_data.get(FIELD_LICENSEURI)
					license.save()
					software.license = license
					print(f"LICENSE SAVED: {software.license.id}")
				else: software.license = License.get_other_licence()

	## PUBLISHER

	publisher_data: dict = data.get(FIELD_PUBLISHER)
	if publisher_data:
		publisher_name: str = publisher_data.get(FIELD_PUBLISHER)
		if publisher_name.lower() == "zenodo":
			software.publisher = Organization.objects.filter(name="Zenodo").first()
		else: software.publisher = parse_organization(
			publisher_data, 
			FIELD_PUBLISHER, 
			FIELD_PUBLISHERIDENTIFIER
		)

	## VERSION

	version_data: dict = data.get(FIELD_VERSIONNUMBER)
	if version_data:
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

	# software needs to be inside database table before any values are added to
	# any of its M2M fields or other fields with foreign keys that need to 
	# reference it
	software.save()

	## AUTHORS

	author_datas: list[dict] = data.get(FIELD_AUTHORS)
	if author_datas: software.authors.clear()
	for author_data in author_datas:
		author = parse_person(
			author_data, 
			FIELD_AUTHORS, FIELD_AUTHORIDENTIFIER, 
			FIELD_AUTHORAFFILIATION, FIELD_AUTHORAFFILIATIONIDENTIFIER
		)
		software.authors.add(author)

	pub_date = data.get(FIELD_PUBLICATIONDATE)
	if pub_date: 
		pub_date = datetime.datetime.strptime(pub_date, '%Y-%m-%d').date()
		software.publicationDate = pub_date

	## PROGRAMMING LANGUAGES

	proglangs = data.get(FIELD_PROGRAMMINGLANGUAGE)
	if proglangs:
		software.programmingLanguage.clear()
		for lang in proglangs:
			obj = parse_controlled_list_reference(ProgrammingLanguage, lang)
			if obj: software.programmingLanguage.add(obj)
	
	## KEYWORDS

	keywords: list[str] = data.get(FIELD_KEYWORDS)
	if keywords:
		software.keywords.clear()
		for kw in keywords:
			kw_obj = parse_controlled_list_reference(Keyword, kw)
			if kw_obj: software.keywords.add(kw_obj)
			else:
				kw_fmtd = SPACE_REPLACE.sub(' ', kw).lower()
				kw_ref = Keyword.objects.filter(name=kw_fmtd).first()
				if kw_ref: software.keywords.add(kw_ref)
				else:
					keyword = Keyword()
					keyword.name = kw_fmtd
					keyword.save()
					software.keywords.add(keyword)

	## FUNCTIONALITY

	functionalities = data.get(FIELD_SOFTWAREFUNCTIONALITY)
	if functionalities:
		software.softwareFunctionality.clear()
		for functionality in functionalities:
			obj = parse_controlled_list_reference(FunctionCategory, functionality)
			if obj: software.softwareFunctionality.add(obj)
	
	## DATA SOURCES
	
	data_sources = data.get(FIELD_DATASOURCES)
	if data_sources:
		software.dataSources.clear()
		for datasrc in data_sources:
			obj = parse_controlled_list_reference(DataInput, datasrc)
			if obj: software.dataSources.add(obj)

	## FILE FORMATS

	inputs = data.get(FIELD_INPUTFORMATS)
	if inputs:
		software.inputFormats.clear()
		for input in inputs:
			obj = parse_controlled_list_reference(FileFormat, input)
			if obj: software.inputFormats.add(obj)
	
	outputs = data.get(FIELD_OUTPUTFORMATS)
	if outputs:
		software.outputFormats.clear()
		for output in outputs:
			obj = parse_controlled_list_reference(FileFormat, output)
			if obj: software.outputFormats.add(obj)
	
	## CPU ARCHITECTURE

	architectures = data.get(FIELD_CPUARCHITECTURE)
	if architectures:
		software.cpuArchitecture.clear()
		for architecture in architectures:
			obj = parse_controlled_list_reference(CpuArchitecture, architecture)
			if obj: software.cpuArchitecture.add(obj)

	## OPERATING SYSTEM

	opsystems = data.get(FIELD_OPERATINGSYSTEM)
	if opsystems:
		software.operatingSystem.clear()
		for opsys in opsystems:
			obj = parse_controlled_list_reference(OperatingSystem, opsys)
			if obj: software.operatingSystem.add(obj)
		

	## RELATED REGION

	regions = data.get(FIELD_RELATEDREGION)
	if regions:
		software.relatedRegion.clear()
		for region in regions:
			obj = parse_controlled_list_reference(Region, region)
			if obj: software.relatedRegion.add(obj)

	## RELATED PHENOMENA

	phenoms = data.get(FIELD_RELATEDPHENOMENA)
	if phenoms:
		software.relatedPhenomena.clear()
		for phenom in phenoms:
			obj = parse_controlled_list_reference(Phenomena, phenom)
			if obj: software.relatedPhenomena.add(obj)

	## AWARDS
	
	award_datas: list[dict] = data.get(FIELD_AWARDTITLE)
	if award_datas:
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
				if award_ref: software.award.add(award_ref)
				else:
					award = Award()
					award.name = award_name
					award.identifier = award_num
					award.save()
					software.award.add(award)

	## FUNDER

	funder_datas: list[dict] = data.get(FIELD_FUNDER)
	if funder_datas:
		software.funder.clear()
		for funder_data in funder_datas:
			funder = parse_organization(funder_data, FIELD_FUNDER, FIELD_FUNDERIDENTIFIER)
			if funder: software.funder.add(funder)

	## RELATED OBJECTS
	
	relpubs: list[str] = data.get(FIELD_RELATEDPUBLICATIONS)
	if relpubs:
		software.relatedPublications.clear()
		for relpub in relpubs:
			try:
				uid = UUID(relpub)
				software.relatedPublications.add(RelatedItem.objects.get(pk=uid))
			except:
				relpub_ref = RelatedItem.objects.filter(identifier=relpub).first()
				if relpub_ref: software.relatedPublications.add(relpub_ref)
				else:
					relatedpub = RelatedItem()
					relatedpub.name = "UNKNOWN"
					relatedpub.identifier = relpub
					relatedpub.type = RelatedItemType.PUBLICATION
					relatedpub.save()
					software.relatedPublications.add(relatedpub)
	
	reldatas: list[str] = data.get(FIELD_RELATEDDATASETS)
	if reldatas:
		software.relatedDatasets.clear()
		for reldat in reldatas:
			try:
				uid = UUID(reldat)
				software.relatedDatasets.add(RelatedItem.objects.get(pk=uid))
			except Exception:
				reldat_ref = RelatedItem.objects.filter(
					identifier=reldat, 
					type=RelatedItemType.DATASET.value
				).first()
				if reldat_ref: software.relatedDatasets.add(reldat_ref)
				else:
					reldataset = RelatedItem()
					reldataset.name = "UNKNOWN"
					reldataset.identifier = reldat
					reldataset.type = RelatedItemType.DATASET.value
					reldataset.save()
					software.relatedDatasets.add(reldataset)
	
	relsofts: list[str] = data.get(FIELD_RELATEDSOFTWARE)
	if relsofts:
		software.relatedSoftware.clear()
		for relsoft in relsofts:
			try:
				uid = UUID(relsoft)
				software.relatedSoftware.add(RelatedItem.objects.get(pk=uid))
			except Exception:
				relsoft_ref = RelatedItem.objects.filter(
					identifier=relsoft, 
					type=RelatedItemType.SOFTWARE.value
				).first()
				if relsoft_ref: software.relatedSoftware.add(relsoft_ref)
				else:
					relsoftware = RelatedItem()
					relsoftware.name = "UNKNOWN"
					relsoftware.identifier = relsoft
					relsoftware.type = RelatedItemType.SOFTWARE.value
					relsoftware.save()
					software.relatedSoftware.add(relsoftware)
	
	intersofts: list[str] = data.get(FIELD_INTEROPERABLESOFTWARE)
	if intersofts:
		software.interoperableSoftware.clear()
		for intersoft in intersofts:
			try:
				uid = UUID(intersoft)
				software.interoperableSoftware.add(RelatedItem.objects.get(pk=uid))
			except Exception:
				intersoft_ref = RelatedItem.objects.filter(
					identifier=intersoft, 
					type=RelatedItemType.SOFTWARE.value
				).first()
				if intersoft_ref: software.interoperableSoftware.add(intersoft_ref)
				else:
					intersoftware = RelatedItem()
					intersoftware.name = "UNKNOWN"
					intersoftware.identifier = intersoft
					intersoftware.type = RelatedItemType.SOFTWARE.value
					intersoftware.save()
					software.interoperableSoftware.add(intersoftware)

	## RELATED INSTRUMENTS AND OBSERVATORIES

	relinstr_datas: list[dict] = data.get(FIELD_RELATEDINSTRUMENTS)
	if relinstr_datas:
		software.relatedInstruments.clear()
		for relinstr_data in relinstr_datas:
			instr_name = relinstr_data.get(FIELD_RELATEDINSTRUMENTS)
			try:
				uid = UUID(instr_name)
				software.relatedInstruments.add(InstrumentObservatory.objects.get(pk=uid))
			except Exception:
				instr_ident = relinstr_data.get(FIELD_RELATEDINSTRUMENTIDENTIFIER)
				instr_ref = None
				if instr_ident: instr_ref = InstrumentObservatory.objects.filter(identifier=instr_ident).first()
				if instr_ref: software.relatedInstruments.add(instr_ref)
				else:
					instr = InstrumentObservatory()
					instr.name = instr_name or "UNKNOWN"
					instr.identifier = instr_ident
					instr.type = InstrObsType.INSTRUMENT.value
					instr.save()
					software.relatedInstruments.add(instr)

	relobs_datas: list[dict] = data.get(FIELD_RELATEDOBSERVATORIES)
	if relobs_datas:
		software.relatedObservatories.clear()
		for relobs_data in relobs_datas:
			obs_name: str = ""
			if isinstance(relobs_data, dict): obs_name = relobs_data.get(FIELD_RELATEDOBSERVATORIES)
			else: obs_name = relobs_data
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
				if obs_ref: software.relatedObservatories.add(obs_ref)
				else:
					obs = InstrumentObservatory()
					obs.name = obs_name or "UNKNOWN"
					obs.identifier = obs_ident
					obs.type = InstrObsType.OBSERVATORY.value
					obs.save()
					software.relatedObservatories.add(obs)

	software.save()
	return submission.id
