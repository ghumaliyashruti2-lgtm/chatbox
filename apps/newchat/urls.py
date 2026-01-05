
from django.conf import settings
from django.conf.urls.static import static  
from django.urls import path
from . import views

urlpatterns = [
    path("", views.new_chatbot, name="chatbot"),
    path("stream/", views.stream_chatbot, name="stream_chatbot"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

