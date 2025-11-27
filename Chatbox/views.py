from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login , logout  as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

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
            return render(request, "signup.html", {'Password_not_match_error': True})

        if User.objects.filter(username=name).exists():
            return render(request, "signup.html", {"user_exits_error": "Username already exists!"})

        if User.objects.filter(email=email).exists():
            return render(request, "signup.html", {"email_exits_error": "Email already exists!"})

        user = User.objects.create_user(
            username=name,
            email=email,
            password=password
        )

      
        login(request, user)

        return redirect("index")

    return render(request, "signup.html")


# login page 
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("login_email")
        password = request.POST.get("login_password")

        if not email or not password:
            return render(request, "login.html", {"empty_error": True})

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return render(request, "login.html", {"user_not_found": True})

        user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            return render(request, "login.html", {"password_error": True})

        login(request, user)   # Django login works now
        return redirect("index")

    return render(request, "login.html")


#logout page 
def logout(request):
    auth_logout(request)
    return redirect("login")


#profile page 
@login_required
def profile(request):

    context = {
        "name": request.user.username,
        "email": request.user.email
    }

    return render(request, "profile.html", context)

 