
import json

from .models import Category, Collection

def organized_categories_json():

    categories = Category.objects.filter(parents__isnull=True).order_by('index')
    category_hierarchy = {}
    category_names_by_id = {}

    for category in categories:
        category_names_by_id[str(category.id)] = category.name
        category_hierarchy[str(category.id)] = []

        for subcategory in category.children.all():
            category_names_by_id[str(subcategory.id)] = subcategory.name
            category_hierarchy[str(category.id)].append(str(subcategory.id))

    return json.dumps(category_hierarchy), json.dumps(category_names_by_id)

def organized_collections_json():

    collections = Collection.objects.filter(parents__isnull=True).order_by('name')
    collection_hierarchy = {}
    collection_names_by_id = {}
    for collection in collections:
        collection_names_by_id[str(collection.id)] = collection.name
        collection_hierarchy[str(collection.id)] = []

        for subcollection in collection.children.all():
            collection_names_by_id[str(subcollection.id)] = subcollection.name
            collection_hierarchy[str(collection.id)].append(str(subcollection.id))

    return json.dumps(collection_hierarchy), json.dumps(collection_names_by_id)