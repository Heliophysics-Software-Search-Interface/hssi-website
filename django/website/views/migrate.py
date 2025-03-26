from django.http import HttpResponse, HttpResponseForbidden, HttpRequest
from django.forms.models import model_to_dict

from ..models import *

def migrate_db_old_to_new(request: HttpRequest) -> HttpResponse:

    # ensure user is a superuser
    if not request.user.is_superuser:
        return HttpResponseForbidden("You must be super user")
    
    print("Beginning migration from old to new database")
    resources = Resource.objects.all()

    for resource in resources:
        print(f"migrating {resource.name} to new DB")

        # create/assign author
        res_auth_split = resource.author.split(' ') if resource.author is not None else "anonymous"
        author: Person
        if len(res_auth_split) >= 2:
            author, _ = Person.objects.get_or_create(
                name=' '.join(res_auth_split[:-1]), 
                lastName=res_auth_split[-1]
            )
        else:
            author, _ = Person.objects.get_or_create(name=res_auth_split[0])

        # create the submission info
        res_submission: Submission = resource.submission
        submission_info = SubmissionInfo.objects.create()
        submission_info.submitter = author
        if res_submission is not None:
            submission_info.submitterEmail = res_submission.submitter_contact
            submission_info.submissionDate = res_submission.creation_date
            submission_info.lastContactDate = res_submission.date_contacted
            submission_info.internalStatusNote = res_submission.status_notes
            submission_info.internalStatusCode = res_submission.status.to_new_code().value
        submission_info.save()

        # create the software from the specified submission info
        software = Software.objects.create(submissionInfo=submission_info)
        software.softwareName = resource.name
        software.codeRepositoryUrl = resource.repo_url
        software.publicationDate = resource.creation_date
        software.versionNumber = resource.version
        software.versionDate = resource.update_date
        software.description = resource.description
        software.conciseDescription = resource.description[:200]
        software.documentation = resource.docs_url
        software.authors.add(author)

        # create/assign programming language
        if len(resource.code_language.strip()) > 0:
            lang, _ = ProgrammingLanguage.objects.get_or_create(name=resource.code_language.strip())
            lang.save()
            software.programmingLanguage = lang
        
        # create/assign keywords
        res_keyw_split = map(lambda x: x.strip(), resource.search_keywords.split(','))
        for res_keyword in res_keyw_split:
            if len(res_keyword) <= 0: continue
            # we need to query with case-insensitivity, hence the __iexact, but 
            # if not found, it needs to set the 'name' field, hence the 
            # 'defaults' parameter
            keyword, _ = Keyword.objects.get_or_create(
                name__iexact=res_keyword, 
                defaults={'name': res_keyword}
            )
            software.keywords.add(keyword)

        # create/assign image logo
        res_logo = resource.logo_url
        if res_logo is not None and len(res_logo) > 0:
            image, _ = Image.objects.get_or_create(url=res_logo)
            software.logo = image

        # TODO
        #software.supportedFileFormats =
        #software.dataInputs =
        #software.softwareFunctionality =
        # end TODO

        # apply changes and add the software to the database
        software.save()

        # add to visible software if published
        if resource.is_published:
            VisibleSoftware.objects.create(id=software)

    return HttpResponse("Success")