import secrets

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasUpdateToken(BasePermission):
	"""Bearer-token permission for HSSI update endpoints.

	Denies the request when ``settings.HSSI_UPDATE_TOKEN`` is unset, when the
	Authorization header is missing or malformed, or when the provided token
	does not match. Uses ``secrets.compare_digest`` for constant-time
	comparison so timing does not leak token bytes.
	"""

	message = "Missing or invalid update token."

	def has_permission(self, request, view):
		expected = getattr(settings, "HSSI_UPDATE_TOKEN", None)
		if not expected:
			return False
		auth_header = request.META.get("HTTP_AUTHORIZATION", "")
		prefix = "Bearer "
		if not auth_header.startswith(prefix):
			return False
		provided = auth_header[len(prefix):]
		return secrets.compare_digest(provided, expected)
