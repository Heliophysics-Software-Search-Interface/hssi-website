import os, traceback

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from import_export import resources
from tablib import Dataset

import website.admin

from website.admin import export_database_changes
from website.models import Category, Collection, Feedback, NewsItem, PendingSubscriptionNotification, Resource, Submission, Subscription, TeamMember,ToolType, InLitResource
from website.signals import categories_changed

class Command(BaseCommand):

    help = "Imports the EMAC website database from the exported config files"

    def import_db_file(self, file_path, Model):

        print(f"Importing {file_path} ...")
        if os.path.isfile(file_path):
            model_resource = resources.modelresource_factory(model=Model)()

            try:
                dataset = Dataset().load(open(file_path).read(), format='csv')
                result = model_resource.import_data(dataset)

                if result.has_errors() or result.has_validation_errors():
                    print("Import failed: ")
                    print("Has errors: " + str(result.has_errors()) + " Has validation errors: " + str(result.has_validation_errors()))
            except:
                traceback.print_exc()
        else:
            print(file_path + " does not exist, skipping")

    def add_arguments(self, parser):

        parser.add_argument('-p', '--path', type=str, help="Path to the EMAC website databse config files", )

    def handle(self, *args, **kwargs):

        DB_CONFIG_PATH = website.admin.DEFAULT_DB_CONFIG_PATH if kwargs['path'] is None else kwargs['path'] 

        CATEGORIES_FILE_PATH = DB_CONFIG_PATH + 'categories.csv'
        COLLECTIONS_FILE_PATH = DB_CONFIG_PATH + 'collections.csv'
        FEEDBACK_FILE_PATH = DB_CONFIG_PATH + 'feedback.csv'
        NEWS_FILE_PATH = DB_CONFIG_PATH + 'news.csv'
        PENDING_SUBSCRIPTION_NOTIFICATIONS_FILE_PATH = DB_CONFIG_PATH + 'pending_subscription_notifications.csv'
        RESOURCES_FILE_PATH = DB_CONFIG_PATH + 'resources.csv'
        INLITRESOURCES_FILE_PATH = DB_CONFIG_PATH + website.admin.IN_LIT_RESOURCES_FILE_NAME
        # the above should be done for all of these. No reason to write the same filename in two places.
        # What if one of them changes?
        SUBMISSIONS_FILE_PATH = DB_CONFIG_PATH + 'submissions.csv'
        SUBSCRIPTIONS_FILE_PATH = DB_CONFIG_PATH + 'subscriptions.csv'
        TEAM_FILE_PATH = DB_CONFIG_PATH + 'team.csv'
        TOOL_TYPES_FILE_PATH = DB_CONFIG_PATH + 'tool_types.csv'

        print("Disabling auto-export of EMAC website database changes ...")
        post_save.disconnect(export_database_changes)
        post_save.disconnect(categories_changed)

        settings.DB_IMPORT_IN_PROGRESS = True

        # Import order matters!!
        self.import_db_file(CATEGORIES_FILE_PATH, Category)
        self.import_db_file(COLLECTIONS_FILE_PATH, Collection)
        self.import_db_file(TOOL_TYPES_FILE_PATH, ToolType)
        self.import_db_file(SUBMISSIONS_FILE_PATH, Submission)
        self.import_db_file(RESOURCES_FILE_PATH, Resource)
        self.import_db_file(INLITRESOURCES_FILE_PATH, InLitResource)
        self.import_db_file(SUBSCRIPTIONS_FILE_PATH, Subscription)
        self.import_db_file(PENDING_SUBSCRIPTION_NOTIFICATIONS_FILE_PATH, PendingSubscriptionNotification)
        self.import_db_file(FEEDBACK_FILE_PATH, Feedback)
        self.import_db_file(NEWS_FILE_PATH, NewsItem)
        self.import_db_file(TEAM_FILE_PATH, TeamMember)
    
        settings.DB_IMPORT_IN_PROGRESS = False

        print("Enabling auto-export of EMAC website database changes ...")
        post_save.connect(export_database_changes)
        post_save.connect(categories_changed)
