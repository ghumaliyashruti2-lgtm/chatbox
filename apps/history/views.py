from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.history.models import History
from apps.profiles.models import Profile
from .forms import CleanHistoryForm, DeleteHistoryForm
import json


# ================================
# HISTORY PAGE
# ================================
@login_required(login_url='login')
def view_history(request):

    profile, _ = Profile.objects.get_or_create(user=request.user)
    sort_option = request.GET.get("sort", "newest")

    # Order directly from DB (IMPORTANT FIX)
    ordering = "-created_at" if sort_option == "newest" else "created_at"

    messages = History.objects.filter(
        user=request.user,
        is_archived=False
    ).order_by(ordering)

    chat_seen = set()
    history_groups = []

    # One entry per chat (stable order)
    for msg in messages:
        if msg.chat_id not in chat_seen:

            is_image = (
                msg.uploaded_file and
                msg.uploaded_file.name.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
            )

            history_groups.append({
                "chat_id": msg.chat_id,
                "start_time": msg.created_at,
                "preview": msg.user_message[:60] if msg.user_message else "📷 Image",
                "image_url": msg.uploaded_file.url if is_image else None,
                "count": messages.filter(chat_id=msg.chat_id).count(),
                "from_time": msg.created_at.isoformat(),
            })

            chat_seen.add(msg.chat_id)

    return render(request, "root/history.html", {
        "history_groups": history_groups,
        "profile": profile,
        "sort_option": sort_option,
    })


# ================================
# ARCHIVE CHAT
# ================================
@login_required(login_url="login")
def archive_chat(request, chat_id):
    if request.method == "POST":
        History.objects.filter(
            user=request.user,
            chat_id=chat_id
        ).update(is_archived=True)

        return JsonResponse({"status": "archived"})

    return JsonResponse({"error": "Invalid request"}, status=400)


# ================================
# UNARCHIVE CHAT (ONLY ONE!)
# ================================
@login_required(login_url="login")
def unarchive_chat(request, chat_id):
    if request.method == "POST":
        History.objects.filter(
            user=request.user,
            chat_id=chat_id
        ).update(is_archived=False)

        return JsonResponse({"status": "unarchived"})

    return JsonResponse({"error": "Invalid request"}, status=400)


# ================================
# ARCHIVED PAGE
# ================================
@login_required(login_url="login")
@login_required(login_url="login")
def archived_history(request):

    profile, _ = Profile.objects.get_or_create(user=request.user)

    # ✅ Get sort from URL
    sort_option = request.GET.get("sort", "newest")

    # ✅ Apply ordering
    ordering = "-created_at" if sort_option == "newest" else "created_at"

    messages = History.objects.filter(
        user=request.user,
        is_archived=True
    ).order_by(ordering)

    chat_seen = set()
    history_groups = []

    for msg in messages:
        if msg.chat_id not in chat_seen:
            history_groups.append({
                "chat_id": msg.chat_id,
                "start_time": msg.created_at,
                "preview": msg.user_message[:60] if msg.user_message else "No message",
                "from_time": msg.created_at.isoformat(),
            })
            chat_seen.add(msg.chat_id)

    return render(request, "root/archive.html", {
        "history_groups": history_groups,
        "profile": profile,
        "sort_option": sort_option,   # ✅ VERY IMPORTANT
    })



# ================================
# CLEAN HISTORY
# ================================
@login_required(login_url="login")
def clean_history(request):
    if request.method == "POST":
        data = json.loads(request.body)
        form = CleanHistoryForm(request.user, data=data)
        if form.is_valid():
            form.clean_history()
            return JsonResponse({"status": "success"})
        return JsonResponse({"error": form.errors}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)


# ================================
# DELETE CHAT
# ================================
@login_required(login_url='login')
def delete_history(request, chat_id):
    if request.method == "POST":
        form = DeleteHistoryForm(request.user, {"chat_id": chat_id})
        if form.is_valid():
            form.delete_history()
            return JsonResponse({"ok": True})
        return JsonResponse({"error": form.errors}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)
