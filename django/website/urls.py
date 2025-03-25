from django.urls import path

from . import submissions, views


app_name = 'website' # Defines app url namespace
urlpatterns = [
    path('', views.published_resources, name="published_resources"),
    path('api', views.apiView, name="rest_api"),
    path('Contact_all/', views.contact_all, name='Contact_all'),
    path('FAQ/', views.FAQ, name="FAQ"),
    path('news/', views.NewsView.as_view(), name='news'),
    path('news/rss/', views.NewsFeed()),
    path('news/<int:pk>/', views.NewsItemView.as_view(), name='news_item'),
    path('submissions/', submissions.submit, name="new_submission"),
    path('submissions/success/', submissions.success, name='submitted'),
    path('submissions/<id>/', submissions.edit, name="edit_submission"),
    path('team/', views.team, name="team"),
    path('export/', views.export_search_results, name='export_seach_results')
]
