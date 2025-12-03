from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout  as auth_logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from profiles.models import Profile
from django.conf import settings 
import os


# Simple view to render your index.html
@login_required(login_url='login')
def index(request):
    return render(request, "index.html")

# signup page
def signup(request):

    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        name = request.POST.get("signup_name")
        email = request.POST.get("signup_email")
        password = request.POST.get("signup_password")
        confirm_password = request.POST.get("signup_confirm_password")
        

        if not name or not email or not password or not confirm_password:
            return render(request, "signup.html", {'error': True})

        if password != confirm_password:
            return render(request, "signup.html", {'password_not_match_error': True})

        if User.objects.filter(username=name).exists():
            return render(request, "signup.html", {"user_exits_error": "Username already exists!"})

        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"email_exits_error": "Email already exists!"})

        # Create staff user
        user = User.objects.create_user(
            username=name,
            email=email,
            password=password
        )
        user.is_staff = True  # <-- Make this user a staff user
        user.save()

        login(request, user)
        return redirect("login")

    return render(request, "signup.html")

# login page 

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("login_email")
        password = request.POST.get("login_password")

        if not email or not password:
            return render(request, "login.html", {"empty_error": True})

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "login.html", {"email_invalid": True})

        # Authenticate using username + password
        user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            return render(request, "login.html", {"password_invalid": True})

        # Check if user is staff
        if not user.is_staff:
            return render(request, "login.html", {"not_staff_error": "You are not a staff user!"})

        login(request, user)
        return redirect("index")

    return render(request, "login.html")


#logout page 
@login_required(login_url='login')
def logout(request):
    auth_logout(request)
    return redirect("login")



#profile page 
@staff_member_required(login_url='login')
def profile(request):
    profile = Profile.objects.get(user=request.user)
    context = {
        "name": request.user.username,
        "email": request.user.email,
        "profile": profile
    }
    return render(request, "profile.html", context)

# my-profile page 
@staff_member_required(login_url='login')
def myprofile(request):
    profile = Profile.objects.get(user=request.user)  # load profile first

    if request.method == "POST":
        gender = request.POST.get("gender")
        mobile = request.POST.get("mobile")

        profile.gender = gender
        profile.mobile = mobile
        profile.save()

        return redirect("profile")  

    return render(request, "my-profile.html", {"profile": profile})


# save profile image 
def editprofile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.FILES.get("profile_picture"):
        profile.profile_picture = request.FILES["profile_picture"]
        profile.save()
        return redirect("my-profile")
    return render(request, "edit-profile.html", {"profile": profile})


# delete image from my-profile and edit-profile

#def deleteprofile(request):
#    return render(request, "delete-profile.html")



def deleteprofile(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == "POST":

        # delete file only if not default image
        if profile.profile_picture.name != "default/user_img.png":
            try:
                os.remove(os.path.join(settings.MEDIA_ROOT, profile.profile_picture.name))
            except:
                pass

        # set profile image to default
        profile.profile_picture = "default/user_img.png"
        profile.save()

        return redirect("my-profile")   # after delete, go to my-profile

    return render(request, "delete-profile.html", {"profile": profile})

