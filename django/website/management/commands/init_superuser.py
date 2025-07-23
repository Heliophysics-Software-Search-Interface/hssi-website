from django.core.management.base import BaseCommand

from django.contrib.auth.models import User

# from hssi.secret_settings import ADMIN_EMAIL, SUPERUSER_PWD, SUPERUSER_NAME
# should really import these from a secret_settings file
from hssi.settings import ADMIN_EMAIL, SUPERUSER_PWD, SUPERUSER_NAME


class Command(BaseCommand):

	help = "Initializes the Superuser"

	def handle(self, *args, **options):

		print("Checking for Superuser...")
		if User.objects.filter(username=SUPERUSER_NAME).count()==0:
			User.objects.create_superuser(SUPERUSER_NAME, ADMIN_EMAIL, SUPERUSER_PWD)
			print("Superuser created")
		else:
			print("Superuser already exists")
