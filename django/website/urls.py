from django.urls import path

from . import submissions, views


app_name = 'website' # Defines app url namespace
urlpatterns = [
    path('', views.published_resources, name="published_resources"),
    path('api', views.api_view, name="rest_api"),
    path('Contact_all/', views.contact_all, name='Contact_all'),
    path('FAQ/', views.FAQ, name="FAQ"),
    path('news/', views.NewsView.as_view(), name='news'),
    path('news/rss/', views.NewsFeed()),
    path('news/<int:pk>/', views.NewsItemView.as_view(), name='news_item'),
    path('submit/', views.submit.submit_resource),
    path('model_structure/', views.exposed_models.get_model_structure),
    #path('submit/success/', submissions.success, name='submitted'),
    #path('submit/<id>/', submissions.edit, name="edit_submission"),
    path('team/', views.team, name="team"),
    path('export/', views.export_search_results, name='export_seach_results')
]
