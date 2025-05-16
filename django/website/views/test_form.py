from django.shortcuts import render
from ..forms import TestForm

def form_test(request):
    form = TestForm(request.POST or None)
    if form.is_valid():
        print(form.cleaned_data)  # just log it for now
    return render(request, "forms/test_form.html", {"form": form})
