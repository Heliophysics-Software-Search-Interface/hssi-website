import threading

from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Resource, TeamMember
from .subscriptions import resource_added_categories

original_category_ids_by_resource_id = {}

@receiver(m2m_changed, sender=Resource.categories.through)
def categories_changed(instance, action, *args, **kwargs):
    global original_category_ids_by_resource_id

    if action == 'pre_add':
        if instance.id not in original_category_ids_by_resource_id:
            original_category_ids_by_resource_id[instance.id] = set(instance.categories.values_list("id", flat=True))
        else:
            original_category_ids_by_resource_id[instance.id] = original_category_ids_by_resource_id[instance.id] | set(instance.categories.values_list("id", flat=True))
    elif action == 'post_add':
        changed_category_ids = set(instance.categories.values_list("id", flat=True))
        added_category_ids = changed_category_ids.difference(original_category_ids_by_resource_id[instance.id])
        if len(added_category_ids) > 0:
            threading.Thread(target=resource_added_categories, args=(instance, added_category_ids))
            original_category_ids_by_resource_id[instance.id] = {}


# the CSV export for Team Members is triggered before the M2M fields (Collections and Categories) are fully saved,
# so we need to re-trigger a save to re-trigger the CSV export once the M2M field is fully set

@receiver(m2m_changed, sender=TeamMember.categories.through)
def curator_categories_changed(instance, action, *args, **kwargs):
    if not settings.DB_IMPORT_IN_PROGRESS:
        if action.startswith('post_'):
            instance.save()
    

@receiver(m2m_changed, sender=TeamMember.collections.through)
def curator_collections_changed(instance, action, *args, **kwargs):
    if not settings.DB_IMPORT_IN_PROGRESS:
        if action.startswith('post_'):
            instance.save()