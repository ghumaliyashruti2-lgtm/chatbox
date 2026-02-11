from django.contrib import admin
from django.urls import path
from apps.history import views
from django.conf import settings
from django.conf.urls.static import static  

app_name = "history"

urlpatterns = [
    
    path("history/",views.view_history,name="history"),
    path("clean-history/", views.clean_history, name="clean-history"),
    path("delete-history/<uuid:chat_id>/", views.delete_history, name="delete_single_history"),
    path("archive/<uuid:chat_id>/", views.archive_chat, name="archive_chat"),
    path("unarchive/<uuid:chat_id>/", views.unarchive_chat, name="unarchive_chat"),
    path("archived/", views.archived_history, name="archived_history"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
