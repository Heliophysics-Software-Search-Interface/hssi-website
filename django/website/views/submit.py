import json, uuid, datetime
from uuid import UUID

from django.shortcuts import render, redirect, HttpResponse
from django.http import (
	HttpRequest, HttpResponseBadRequest, 
	JsonResponse, HttpResponseRedirect, HttpResponseServerError,
)

from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3
)
from ..models import *
from ..forms.names import *
from ..util import *

def view_form(request: HttpRequest) -> HttpResponse:
	return render(
		request, 
		"pages/submit.html", 
		{ 
			"structure_names": [
				SUBMISSION_FORM_FIELDS_1.type_name,
				SUBMISSION_FORM_FIELDS_2.type_name,
				SUBMISSION_FORM_FIELDS_3.type_name
			],
		}
	)

def view_confirmation(request: HttpRequest) -> HttpResponse:
	if request.method != "GET":
		return HttpResponseBadRequest("GET expected")
	
	return render(
		request,
		"pages/submit_confirmation.html",
		{ "recieved_data": request.body }
	)

def submit_data(request: HttpRequest) -> HttpResponse:
	if request.method != "POST":
		return HttpResponseBadRequest("POST expected")
	
	# parse request body to json
	encoding = request.encoding or "utf-8"
	data = request.body.decode(encoding)
	json_data = json.loads(data)

	# try handle json_data and save to database
	print("recieved form data", json_data)
	submisison_id = handle_submission_data(json_data)

	return redirect(f"/submit/submitted?id={str(submisison_id)}")

def handle_submission_data(data: dict) -> uuid.UUID:
	software = Software()

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

	dev_status_str = data.get(FIELD_DEVELOPMENTSTATUS)
	try:
		uid = UUID(dev_status_str)
		software.developmentStatus = RepoStatus.objects.get(id=uid)
	except Exception:
		repostatus = RepoStatus.objects.filter(name=dev_status_str).first()
		if repostatus: software.developmentStatus = repostatus
	
	## LOGO

	logo_url = data.get(FIELD_LOGO)
	if logo_url:
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

	submitter_found: Submitter = Submitter.objects.filter(email=submitter_email)
	if submitter_found:
		sub_person_found = Person.objects.filter(
			firstName=submitter_found.person.firstName, 
			lastName=submitter_found.person.lastName
		)
		success = False
		for person in sub_person_found:
			if person.pk == sub_person_found.pk:
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
		license_name = license_data.get(FIELD_LICENSE)
		try:
			uid = UUID(license_name)
			license = License.objects.get(pk=uid)
			software.license = license
		except Exception:
			license = License.objects.filter(name=license_name).first()
			if not license:
				license_url = license_data.get(FIELD_LICENSEURI)
				license = License.objects.filter(url=license_url).first()
			if license: software.license = license
			else:
				license = License()
				license.name = license_name
				license.url = license_data.get(FIELD_LICENSEURI)
				license.save()
				software.license = license

	## DEV STATUS

	devstatus = data.get(FIELD_DEVELOPMENTSTATUS)
	try:
		uid = UUID(devstatus)
		devstatus = RepoStatus.objects.get(pk=uid)
		software.developmentStatus = devstatus
	except Exception:
		devstatus = RepoStatus.objects.filter(name=devstatus).first()
		software.developmentStatus = devstatus
	
	## PUBLISHER

	publisher_data: dict = data.get(FIELD_PUBLISHER)
	if publisher_data:
		publisher = Organization()
		publisher.name = publisher_data.get(FIELD_PUBLISHER)
		try:
			uid = UUID(publisher.name)
			dbpub = Organization.objects.get(pk=uid)
			software.publisher = dbpub
		except Exception:
			publisher.identifier = publisher_data.get(FIELD_PUBLISHERIDENTIFIER)
			pub_match = None
			if publisher.name.lower() == "zenodo":
				pub_match = Organization.objects.filter(name="Zenodo").first()
			elif publisher.identifier: 
				pub_match = Organization.objects.filter(identifier=publisher.identifier).first()
			if pub_match: publisher = pub_match
			else: publisher.save()
			software.publisher = publisher

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
	for author_data in author_datas:
		author = Person()
		author.identifier = author_data.get(FIELD_AUTHORIDENTIFIER)
		author_match = None
		if author.identifier: 
			author_match = Person.objects.filter(identifier=author.identifier).first()

		# TODO some way to change author name after submission
		if author_match: author = author_match
		else:
			author_name: str = author_data.get(FIELD_AUTHORS)
			author_spl: str = author_name.split(',')
			author_lastname = ""
			author_firstname = ""
			if len(author_spl) > 1:
				author_firstname = author_spl[-1]
				author_lastname = author_spl[0]
			else:
				author_lastname = author_name.split()[-1]
				author_firstname = author_name.replace(author_lastname, '').strip()
			author.lastName = author_lastname
			author.firstName = author_firstname
			author.save()

		affiliation_datas: dict = author_data.get(FIELD_AUTHORAFFILIATION)
		if affiliation_datas:
			for affiliation_data in affiliation_datas:
				affiliation_name = affiliation_data.get(FIELD_AUTHORAFFILIATION)
				affiliation_id = affiliation_data.get(FIELD_AUTHORAFFILIATIONIDENTIFIER)

				affiliation = Organization()
				affiliation.name = affiliation_name
				affiliation.identifier = affiliation_id
				affil_match = None
				if affiliation_id: 
					affil_match = Organization.objects.filter(identifier=affiliation.identifier).first()
				if affil_match: affiliation = affil_match
				else: affiliation.save()
				author.affiliation.add(affiliation)

		author.save()
		software.authors.add(author)

	pub_date = data.get(FIELD_PUBLICATIONDATE)
	if pub_date: 
		pub_date = datetime.datetime.strptime(pub_date, '%Y-%m-%d').date()
		software.publicationDate = pub_date

	## PROGRAMMING LANGUAGES

	proglangs = data.get(FIELD_PROGRAMMINGLANGUAGE)
	for lang in proglangs:
		try:
			uid = UUID(lang)
			software.programmingLanguage.add(ProgrammingLanguage.objects.get(pk=uid))
		except Exception:
			lang_ref = ProgrammingLanguage.objects.filter(name=lang).first()
			if lang_ref: software.programmingLanguage.add(lang_ref)
	
	## KEYWORDS

	keywords: list[str] = data.get(FIELD_KEYWORDS)
	for kw in keywords:
		try:
			uid = UUID(kw)
			dbkw = Keyword.objects.get(pk=uid)
			software.keywords.add(dbkw)
		except Exception as e:
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
	for functionality in functionalities:
		try:
			uid = UUID(functionality)
			software.softwareFunctionality.add(FunctionCategory.objects.get(pk=uid))
		except Exception:
			print(f"ERROR - software functionality '{functionality}' does not exist")
	
	## DATA SOURCES
	
	data_sources = data.get(FIELD_DATASOURCES)
	for datasrc in data_sources:
		try:
			uid = UUID(datasrc)
			software.dataSources.add(DataInput.objects.get(pk=uid))
		except Exception:
			src_ref = DataInput.objects.filter(name=datasrc).first()
			if src_ref: software.dataSources.add(src_ref)
			else:
				src = DataInput()
				src.name = datasrc
				src.save()
				software.dataSources.add(src)

	## FILE FORMATS

	inputs = data.get(FIELD_INPUTFORMATS)
	for input in inputs:
		try:
			uid = UUID(input)
			software.inputFormats.add(FileFormat.objects.get(pk=uid))
		except Exception:
			input_ref = FileFormat.objects.filter(name=input).first()
			if input_ref: software.inputFormats.add(input_ref)
			else:
				inpt = FileFormat()
				inpt.name = input
				inpt.save()
				software.inputFormats.add(inpt)
	
	outputs = data.get(FIELD_OUTPUTFORMATS)
	for output in outputs:
		try:
			uid = UUID(output)
			software.outputFormats.add(FileFormat.objects.get(pk=uid))
		except Exception:
			outref = FileFormat.objects.filter(name=output).first()
			if outref: software.outputFormats.add(outref)
			else:
				out = FileFormat()
				out.name = output
				out.save()
				software.outputFormats.add(out)
	
	## CPU ARCHITECTURE

	architectures = data.get(FIELD_CPUARCHITECTURE)
	for architecture in architectures:
		try:
			uid = UUID(architecture)
			software.cpuArchitecture.add(CpuArchitecture.objects.get(pk=uid))
		except:
			arcref = CpuArchitecture.objects.filter(name=architecture).first()
			if arcref: software.cpuArchitecture.add(arcref)
			else:
				arc = CpuArchitecture()
				arc.name = architecture
				arc.save()
				software.cpuArchitecture.add(arc)

	## OPERATING SYSTEM

	opsystems = data.get(FIELD_OPERATINGSYSTEM)
	for opsys in opsystems:
		try:
			uid = UUID(opsys)
			software.operatingSystem.add(OperatingSystem.objects.get(pk=uid))
		except: print(f"invalid os entry '{opsys}'")
		

	## RELATED REGION

	regions = data.get(FIELD_RELATEDREGION)
	for region in regions:
		try:
			uid = UUID(region)
			software.relatedRegion.add(Region.objects.get(pk=uid))
		except Exception:
			regref = Region.objects.filter(name=region)
			if regref: software.relatedRegion.add(regref)
			else:
				regn = Region()
				regn.name = region
				regn.save()
				software.relatedRegion.add(regn)

	## RELATED PHENOMENA

	phenoms = data.get(FIELD_RELATEDPHENOMENA)
	for phenom in phenoms:
		try:
			uid = UUID(phenom)
			software.relatedPhenomena.add(Phenomena.objects.get(pk=uid))
		except:
			phenomref = Phenomena.objects.filter(name=phenom).first()
			if phenomref: software.relatedPhenomena.add(phenomref)
			else:
				phen = Phenomena()
				phen.name = phenom
				phen.save()
				software.relatedPhenomena.add(phen)

	## AWARDS
	
	award_datas: list[dict] = data.get(FIELD_AWARDTITLE)
	for award_data in award_datas:
		award_name = award_data.get(FIELD_AWARDTITLE)
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
	for funder_data in funder_datas:
		funder_name = funder_data.get(FIELD_FUNDER)
		print(f"adding funder '{funder_name}'")
		try:
			uid = UUID(funder_name)
			fnref = Organization.objects.get(pk=uid)
			software.funder.add(Organization.objects.get(pk=uid))
		except Exception:
			funder_ident = funder_data.get(FIELD_FUNDERIDENTIFIER)
			funder_ref: Organization = None
			if funder_ident: 
				funder_ref = Organization.objects.filter(identifier=funder_ident).first()
			if funder_ref: software.funder.add(funder_ref)
			else:
				funder = Organization()
				funder.name = funder_name
				if funder_ident: funder.identifier = funder_ident
				funder.save()
				software.funder.add(funder)

	## RELATED OBJECTS
	
	relpubs: list[str] = data.get(FIELD_RELATEDPUBLICATIONS)
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
	for intersoft in intersofts:
		try:
			uid = UUID(intersoft)
			software.interoperableSoftware.add(RelatedItem.objects.get(pk=uid))
		except Exception:
			intersoft_ref = RelatedItem.objects.filter(
				identifier=intersoft, 
				type=RelatedItemType.SOFTWARE.value
			).first()
			if intersoft_ref: software.relatedSoftware.add(intersoft_ref)
			else:
				intersoftware = RelatedItem()
				intersoftware.name = "UNKNOWN"
				intersoftware.identifier = intersoft
				intersoftware.type = RelatedItemType.SOFTWARE.value
				intersoftware.save()
				software.interoperableSoftware.add(intersoftware)

	## RELATED INSTRUMENTS AND OBSERVATORIES

	relinstr_datas: list[dict] = data.get(FIELD_RELATEDINSTRUMENTS)
	for relinstr_data in relinstr_datas:
		instr_name = relinstr_data.get(FIELD_RELATEDINSTRUMENTS)
		try:
			uid = UUID(instr_name)
			software.relatedInstruments.add(InstrumentObservatory.objects.get(pk=uid))
		except Exception:
			instr_ident = relinstr_data.get(FIELD_RELATEDINSTRUMENTIDENTIFIER)
			instr_ref = None
			if instr_ident: instr_ref = InstrumentObservatory.objects.filter(identifier=instr_ident)
			if instr_ref: software.relatedInstruments.add(instr_ref)
			else:
				instr = InstrumentObservatory()
				instr.name = instr_name or "UNKNOWN"
				instr.identifier = instr_ident
				instr.type = InstrObsType.INSTRUMENT.value
				instr.save()
				software.relatedInstruments.add(instr)

	relobs_datas: list[dict] = data.get(FIELD_RELATEDOBSERVATORIES)
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
			if isinstance(relobs_data, dict): relobs_data.get(FIELD_RELATEDINSTRUMENTIDENTIFIER)
			obs_ref = None
			if obs_ident: obs_ref = InstrumentObservatory.objects.filter(identifier=obs_ident)
			if obs_ref: software.relatedInstruments.add(obs_ref)
			else:
				obs = InstrumentObservatory()
				obs.name = obs_name or "UNKNOWN"
				obs.identifier = obs_ident
				obs.type = InstrObsType.OBSERVATORY.value
				obs.save()
				software.relatedObservatories.add(obs)

	software.save()
	return submission.id
