from django import template

from website.models import Submission

register = template.Library()

@register.filter    
def is_under_development(resource):
    return resource.is_under_development()

@register.filter    
def submission_name(id):
    submission = Submission.objects.get(id=id)
    return submission.name

@register.filter    
def id_values_list(queryset):
    return list(queryset.values_list('id', flat=True))

@register.filter    
def intersection(list1, list2):
    return set(list1) & set(list2)
