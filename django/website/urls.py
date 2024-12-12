from django.urls import path
from django.shortcuts import redirect

from . import submissions, subscriptions, views


app_name = 'website' # Defines app url namespace
urlpatterns = [
    path('', views.published_resources, name="published_resources"),
    path('cidseed', views.cid_seed, name="CID_Seed"),
    path('Contact_all/', views.contact_all, name='Contact_all'),
    path('ASCL_scraper/', views.ascl_scraper, name='ASCL_scraper'),
    path('analytics/', views.run_analytics, name="analytics"),
    path('io_diagram/', views.run_io_diagram, name="io_diagram"),
    path('FAQ/', views.FAQ, name="FAQ"),
    path('news/', views.NewsView.as_view(), name='news'),
    path('news/rss/', views.NewsFeed()),
    path('news/<int:pk>/', views.NewsItemView.as_view(), name='news_item'),
    path('submissions/', submissions.submit, name="new_submission"),
    path('submissions/success/', submissions.success, name='submitted'),
    path('submissions/<id>/', submissions.edit, name="edit_submission"),
    path('subscriptions/', subscriptions.submit, name="new_subscription"),
    path('subscriptions/success/', subscriptions.success, name='subscribed'),
    path('subscriptions/<id>/', subscriptions.edit, name="edit_subscription"),
    path('notify_subscribers/<str:frequency>/', subscriptions.notify_subscribers, name="notify_subscribers"),
    path('team/', views.team, name="team"),
    path('export/', views.export_search_results, name='export_seach_results'),
    path('scan_links/', views.scan_links, name='scan_links'),
    path('seminars/', views.seminars, name='seminars'),
    path('workshop/', lambda request: redirect('/seminars/#workshop', permanent=True)),
    path('developers/', views.developers, name='developers'),
    path('api/resource-links', views.ADS_endpoint, name='ADS_endpoint'),
    path('curators/', views.curator_login, name='curator_login'),
    path('curate/', views.curate, name='curate'),
    path('curate/success/', views.curate_success, name='curate_success'),
    path('github_release_edit/<id>/', submissions.resource_update_alert, name="edit_github_release"),
    path('git_updates/<id>/', views.version_update, name="send_update_alert"),
    path('fetch_git_versions/', views.git_fetch_version, name='fetch_git_versions')
]
