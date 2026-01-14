from django.views import generic
from django.http import Http404

from ..models import Software, VisibleSoftware


class SoftwareDetailView(generic.DetailView):
    """
    View for displaying a single software's landing page with all metadata.
    """
    model = Software
    template_name = 'website/software_detail.html'
    context_object_name = 'software'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    # Reserved slugs that should not be matched as software
    RESERVED_SLUGS = {
        'api', 'faq', 'news', 'submit', 'team', 'export',
        'curate', 'sapi', 'request_edit', 'admin', 'static'
    }

    def get_queryset(self):
        # Only show visible (published) software
        visible_ids = VisibleSoftware.objects.values_list('id', flat=True)
        return Software.objects.filter(pk__in=visible_ids)

    def get_object(self, queryset=None):
        slug = self.kwargs.get(self.slug_url_kwarg)

        # Protect against reserved slugs
        if slug and slug.lower() in self.RESERVED_SLUGS:
            raise Http404("Software not found")

        return super().get_object(queryset)
