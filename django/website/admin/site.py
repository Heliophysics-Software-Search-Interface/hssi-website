from django.urls import path
from django.contrib import admin

from .actions import (
	view_export_db_new, 
	view_import_db_new, 
	view_get_metadata, 
	fetch_vocab
)

class HssiAdminSite(admin.AdminSite):
	"""
	Admin site for administration and interaction with HSSI website and
	database. Inherited from django.admin.AdminSite and implements custom
	metadata for HSSI and adds some custom actions through url views and 
	controls defined in custom index html template file.
	"""

	site_title = 'HSSI admin'
	site_header = 'HSSI administration'
	index_title = 'HSSI administration'
	index_template = 'admin/index.html'

	# override get_urls to add custom views
	def get_urls(self: 'HssiAdminSite'):

		# here we need to insert our custom urls after all of the default 
		# patterns EXCEPT FOR the last one. Which is the catch-all pattern 
		# that is used for debugging, this one we do not want to catch every 
		# web page before our custom patterns are compared against. 
		# NOTE this pattern is only included in debug builds but swapping the 
		# final pattern in release builds shouldn't cause any issues.. hopefully
		urls_base = super().get_urls()
		urls = urls_base[:-1] + [
			path('export_db_new/', view_export_db_new, name='export_db_new'),
			path('import_db_new/', view_import_db_new, name='import_db_new'),
			path('get_metadata/', view_get_metadata, name='get_metadata'),
			path('fetch_vocab/', fetch_vocab, name="fetch_vocab")
		] + urls_base[-1:]
		return urls

admin_site = HssiAdminSite()