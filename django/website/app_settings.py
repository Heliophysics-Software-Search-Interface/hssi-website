from django.conf import settings

settings.INSTALLED_APPS.extend([
	'colorful',
	'crispy_forms',
	'crispy_bootstrap4',
	'import_export',
	'ipware',
	'mathfilters',
	'website.apps.WebsiteConfig',
])

settings.DB_IMPORT_IN_PROGRESS = False
