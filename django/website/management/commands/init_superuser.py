from django.core.management.base import BaseCommand

from django.contrib.auth.models import User, Group;
from emac.secret_settings import EMAC_ADMIN_EMAIL, EMAC_ADMIN_PASSWORD, EMAC_ADMIN_USERNAME 

class Command(BaseCommand):

    help = "Initializes the HSSI superuser and Curators group"

    def handle(self, *args, **options):

        print("Checking for HSSI superuser...")
        if User.objects.filter(username=EMAC_ADMIN_USERNAME).count()==0:
            User.objects.create_superuser(EMAC_ADMIN_USERNAME, EMAC_ADMIN_EMAIL, EMAC_ADMIN_PASSWORD)
            print("HSSI superuser created")
        else:
            print("HSSI superuser already exists")

        print("Checking for Curators group...")
        if Group.objects.filter(name='Curators').count()==0:
            curators = Group.objects.create(name='Curators')
            print("Curators group created")
        else:
            print("Curators group already exists")
