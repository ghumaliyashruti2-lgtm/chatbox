from django.contrib import admin
from django.urls import path
from profiles import views
from django.conf import settings
from django.conf.urls.static import static  

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("my-profile/",views.myprofile,name="my-profile"),
    path("edit-profile/",views.editprofile,name="edit-profile"),
    path("delete-profile/",views.deleteprofile,name="delete-profile"),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
