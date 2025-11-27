from django.contrib import admin
from django.urls import path
from chatbox import views
from django.conf import settings
from django.conf.urls.static import static  

urlpatterns = [
    path('index/', views.index,name="index"),
    path('login/', views.login_view,name="login"),
    path('', views.signup,name="signup"),
    path('admin/', admin.site.urls),
    path("logout/", views.logout, name="logout"),
    path("profile/", views.profile, name="profile"),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
