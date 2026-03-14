from django.views import generic

from ..models import Software, VerifiedSoftware


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
        visible_ids = VerifiedSoftware.objects.values_list('id', flat=True)
        return Software.objects.filter(pk__in=visible_ids)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        software = context.get('software')
        latest_version = None
        if software is not None:
            latest_version = (
                software.version.all()
                .order_by('-release_date', '-number')
                .first()
            )
        context['latest_version'] = latest_version
        return context
