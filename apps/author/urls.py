from django.contrib import admin
from django.urls import path, include
from apps.author import views
from django.conf import settings
from django.conf.urls.static import static  

urlpatterns = [
    
    path("home/",views.home,name="home"),
    path("login/", views.login,name="login"),
    path("", views.signup,name="signup"),
    path("logout/", views.logout, name="logout"),
    path("admin/", admin.site.urls),
    path("forgot-password/", views.forgot_password, name="forgot_password"),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

