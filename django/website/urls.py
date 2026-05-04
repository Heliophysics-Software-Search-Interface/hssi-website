from django.urls import path

from . import views

app_name = 'website' # Defines app url namespace
urlpatterns = [
	path('', views.published_resources, name="published_resources"),
	path('api', views.api_view, name="rest_api"),
	path('api/submit', views.api_submit),
	path('FAQ/', views.FAQ, name="FAQ"),
	#path('news/', views.NewsView.as_view(), name='news'),
	#path('news/rss/', views.NewsFeed()),
	#path('news/<int:pk>/', views.NewsItemView.as_view(), name='news_item'),
	path('submit/', views.submit.view_form),
	path('submit/submit_data/', views.submit.submit_data),
	path('submit/submitted/', views.submit.view_confirmation),
    path('request_edit/<str:uid>/', views.request_edit_link),
    path('curate/edit_submission/', views.edit_submission),
    path('curate/edit_submission/submit_data/<str:uid>/', views.submit_edits),
    path('sapi/software_edit_data/<str:uid>/', views.get_submission_data),
	path('api/models/structures/', views.exposed_models.get_model_structure),
	path('api/models/<str:model_name>/choices/', views.exposed_models.get_model_choices),
	path('api/models/<str:model_name>/form/', views.exposed_models.model_form),
	path('api/models/<str:model_name>/rows/all/', views.model_rows.get_model_rows_all),
	path('api/models/<str:model_name>/rows/<str:uid>/', views.model_rows.get_model_row),
	path('api/describe', views.somef.describe_view),
	path('api/describe_form', views.somef.form_fill_view),
	path('api/citation/', views.get_citation, name='get_citation'),
	path('api/search/', views.search_visible_software, name='search_visible_software'),

	# DRF api views
	path('api/submission/', views.api.SubmissionAPI.as_view()),
	path('api/update', views.api.SoftwareUpdateAPI.as_view()),
	path('api/update/lookup', views.api.SoftwareUpdateLookupAPI.as_view()),
	path('api/list/software/', views.api.SoftwareListAPI.as_view()),
	path('api/view/software/<uuid:uid>/', views.api.SoftwareViewAPI.as_view()),
	path('api/data/software/<uuid:uid>/', views.api.SoftwareDetailAPI.as_view()),

	# Software landing page - uses UUID primary key
	path('software/<uuid:pk>/', views.SoftwareDetailView.as_view(), name='software_detail'),

	path('team/', views.team, name="team"),
]
