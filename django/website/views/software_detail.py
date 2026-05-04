"""Views for Software detail pages."""

import json
from typing import Any, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet
from django.utils.safestring import mark_safe
from django.views import generic
from django.http import Http404

from ..models import Software, VerifiedSoftware, SoftwareVersion
from ..models.serializers.software import SoftwareSerializer
from ..models.serializers.util import SerialView


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

    def get_object(self, queryset = None):
        if not queryset:
            queryset = self.get_queryset()
        if 'pk' in self.kwargs:
            return super().get_object(queryset)
        
        slug = self.kwargs.get('slug')
        software = VerifiedSoftware.objects.filter(slug=slug).first()
        if not software:
            raise Http404
        
        self.kwargs['pk'] = software.pk
        return super().get_object(queryset)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add display data to the software detail template context."""
        context = super().get_context_data(**kwargs)
        software: Optional[Software] = context.get('software')
        latest_version: Optional[SoftwareVersion] = None
        functionality_tags = []
        if software is not None:
            latest_version = (
                software.version.all()
                .order_by('-release_date', '-number')
                .first()
            )
            functionality_tags = software.get_ordered_software_functionality()
            serializer = SoftwareSerializer(
                software,
                context={"request": self.request},
            )
            serializer._view = SerialView.JSONLD
            jsonld = json.dumps(serializer.data, cls=DjangoJSONEncoder).translate({
                ord("<"): "\\u003C",
                ord(">"): "\\u003E",
                ord("&"): "\\u0026",
            })
            context['software_jsonld'] = mark_safe(jsonld)
        context['latest_version'] = latest_version
        context['functionality_tags'] = functionality_tags
        return context
