import uuid
from django import template

register = template.Library()

@register.simple_tag
def unique_id(prefix="id"):
    return f"{prefix}-{uuid.uuid4().hex}"
