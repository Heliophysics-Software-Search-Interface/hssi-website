from django.shortcuts import render
from ..forms import SubmissionForm

def submit_resource(request):
    form = SubmissionForm(request.POST or None)
    return render(request, "pages/submit.html", {"form": form})
