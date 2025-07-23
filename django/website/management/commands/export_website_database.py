from django.core.management.base import BaseCommand

from website import admin

class Command(BaseCommand):

	help = "Exports the website database to config files"

	def add_arguments(self, parser):

		parser.add_argument('-p', '--path', type=str, help="Path to the website databse config files", )

	def handle(self, *args, **kwargs):

		admin.export_database(**kwargs)
