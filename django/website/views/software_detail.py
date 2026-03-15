"""Views for Software detail pages."""

from typing import Any, Optional

from django.db.models import QuerySet
from django.views import generic

from ..models import Software, VerifiedSoftware, SoftwareVersion


class SoftwareDetailView(generic.DetailView):
    """
    View for displaying a single software's landing page with all metadata.
    Uses the software's UUID as the primary key in the URL.
    """
    model = Software
    template_name = 'website/software_detail.html'
    context_object_name = 'software'

    def get_queryset(self) -> QuerySet[Software]:
        """Return only visible (published) software records."""
        visible_ids = VerifiedSoftware.objects.values_list('id', flat=True)
        return Software.objects.filter(pk__in=visible_ids)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the latest SoftwareVersion to the template context."""
        context = super().get_context_data(**kwargs)
        software: Optional[Software] = context.get('software')
        latest_version: Optional[SoftwareVersion] = None
        if software is not None:
            latest_version = (
                software.version.all()
                .order_by('-release_date', '-number')
                .first()
            )
        context['latest_version'] = latest_version
        return context
