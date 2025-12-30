from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, logout as auth_logout
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from chat_history.models import ChatHistory
from chatbox.openrouter_api import OpenRouterChatbot
from django.http import JsonResponse
import json
from profiles.models import Profile
# Create your views here.

# ----------------------------
# AUTH
# ----------------------------

chatbot = OpenRouterChatbot()
@login_required(login_url='login')
def index(request):

    profile = Profile.objects.get(user=request.user)
    # Load chat history from DB
    db_history = ChatHistory.objects.filter(user=request.user).order_by("created_at")

    conversation_history = []
    for item in db_history:
        conversation_history.append({"role": "user", "content": item.user_message})
        conversation_history.append({"role": "assistant", "content": item.ai_message})

    # Handle AJAX chat request
    if request.method == "POST" and request.headers.get("Content-Type") == "application/json":
        try:
            data = json.loads(request.body)
            user_input = data.get("message", "")
        except:
            user_input = ""

        bot_reply = chatbot.get_response(user_input, conversation_history)

        # Save in DB
        ChatHistory.objects.create(
            user=request.user,
            user_message=user_input,
            ai_message=bot_reply
        )

        return JsonResponse({
            "reply": bot_reply,
            "show_courses": False,
            "success": True
        })

    # Initial page render
    return render(request, "index.html", {
        "conversation": conversation_history,
        "profile": profile,
    })


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

        user = User.objects.create_user(
            username=name,
            email=email,
            password=password
        )
        user.is_staff = True
        user.save()

        login(request, user)
        return redirect("login")

    return render(request, "signup.html")


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

        user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            return render(request, "login.html", {"password_invalid": True})

        if not user.is_staff:
            return render(request, "login.html", {"not_staff_error": "You are not a staff user!"})

        login(request, user)
        return redirect("index")

    return render(request, "login.html")


@login_required
def logout(request):
    auth_logout(request)
    return redirect("home")


def home(request):
    return render(request, "home.html")


