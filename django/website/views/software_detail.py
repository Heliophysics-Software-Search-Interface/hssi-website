from django.views import generic

from ..models import Software, VisibleSoftware


class SoftwareDetailView(generic.DetailView):
    """
    View for displaying a single software's landing page with all metadata.
    Uses the software's UUID as the primary key in the URL.
    """
    model = Software
    template_name = 'website/software_detail.html'
    context_object_name = 'software'

    def get_queryset(self):
        # Only show visible (published) software
        visible_ids = VisibleSoftware.objects.values_list('id', flat=True)
        return Software.objects.filter(pk__in=visible_ids)
