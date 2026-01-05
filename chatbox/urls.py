from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  

urlpatterns = [
    
    path("chatbot/", include("apps.newchat.urls")),
    path("",include("apps.author.urls")),
    path("",include("apps.history.urls")),
    path("", include("apps.profiles.urls")),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

