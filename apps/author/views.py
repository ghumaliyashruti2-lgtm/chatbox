from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from apps.author.forms import SignupForm, LoginForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import ForgotPasswordForm

def signup(request):
    if request.user.is_authenticated:
        return redirect("chatbot")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login") 
    else:
        form = SignupForm()

    return render(request, "base/signup.html", {"form": form})


def login(request):
    if request.user.is_authenticated:
        return redirect("chatbot")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            auth_login(request, form.cleaned_data["user"])
            return redirect("chatbot")
    else:
        form = LoginForm()

    return render(request, "base/login.html", {"form": form})

def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            new_password = form.cleaned_data["new_password"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Email not found")
                return redirect("forgot_password")

            user.set_password(new_password)  # ✅ hash password
            user.save()

            messages.success(request, "Password updated successfully! Please login.")
            return redirect("login")

    else:
        form = ForgotPasswordForm()

    return render(request, "base/forgot-password.html", {"form": form})


@login_required
def logout(request):
    auth_logout(request)
    return redirect("home")


def home(request):
    return render(request, "base/home.html")
