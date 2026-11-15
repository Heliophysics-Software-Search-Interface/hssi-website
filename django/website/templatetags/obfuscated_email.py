"""Template tag for email links that don't show the address in the raw HTML."""

import base64

from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def obfuscated_email(email: str, text: str = "") -> str:
	"""
	An email link holding `email` base64-encoded instead of as plain text, so
	scrapers reading the page source don't find the address. The frontend
	(`frontend/obfuscatedEmail.ts`) decodes it on page load and fills in the
	`mailto:` link. The link shows `text` if given, otherwise the address.

	Usage: `{% load obfuscated_email %}` then
	`{% obfuscated_email "team@example.com" %}` or
	`{% obfuscated_email "team@example.com" "email us" %}`.
	"""
	encoded = base64.b64encode(email.encode()).decode()
	if text:
		return format_html(
			'<a class="obfuscated-email" data-email="{}" data-keep-text>{}</a>',
			encoded, text,
		)
	return format_html(
		'<a class="obfuscated-email" data-email="{}">(enable JavaScript to see email)</a>',
		encoded,
	)
