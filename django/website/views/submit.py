from django.shortcuts import render, HttpResponse

def submit_resource(request):
    return render(
        request, 
        "pages/model_form.html", 
        { "structure_name": "SubmissionForm" }
    )
