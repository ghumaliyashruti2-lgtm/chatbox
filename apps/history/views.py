from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.history.models import History
import json
from django.http import JsonResponse
from apps.profiles.models import Profile
from collections import defaultdict
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import CleanHistoryForm, DeleteHistoryForm
from django.http import JsonResponse

@login_required(login_url='login')
def view_history(request):

    profile, _ = Profile.objects.get_or_create(user=request.user)

    sort_option = request.GET.get("sort", "newest")

    # Always fetch messages in chronological order
    messages = History.objects.filter(
        user=request.user,
        is_archived=False
    ).order_by("created_at")

    # ==========================
    # GROUP BY CHAT ID
    # ==========================
    chat_groups = defaultdict(list)

    for msg in messages:
        chat_groups[msg.chat_id].append(msg)

    history_groups = []

    # ==========================
    # ONE ENTRY PER CHAT (FIXED)
    # ==========================
    history_groups = []

    for chat_id, msgs in chat_groups.items():
        first_msg = msgs[0]

        is_image = (
            first_msg.uploaded_file and
            first_msg.uploaded_file.name.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        )

        history_groups.append({
            "chat_id": chat_id,
            "start_time": first_msg.created_at,
            "preview": first_msg.user_message[:60] if first_msg.user_message else "📷 Image",
            "image_url": first_msg.uploaded_file.url if is_image else None,
            "count": len(msgs),
            "from_time": first_msg.created_at.isoformat(),
        })


    # ==========================
    # SORT GROUPS
    # ==========================
    history_groups.sort(
        key=lambda x: x["start_time"],
        reverse=(sort_option == "newest")
    )

    return render(request, "root/history.html", {
        "history_groups": history_groups,
        "profile": profile,
        "sort_option": sort_option,
    })


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


@login_required(login_url='login')
def delete_history(request, chat_id):
    if request.method == "POST":
        form = DeleteHistoryForm(request.user, {"chat_id": chat_id})
        if form.is_valid():
            form.delete_history()
            return JsonResponse({"ok": True})
        return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url="login")
def archive_chat(request, chat_id):
    if request.method == "POST":

        History.objects.filter(
            user=request.user,
            chat_id=chat_id
        ).update(is_archived=True)

        return JsonResponse({"status": "archived"})

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required(login_url="login")
def unarchive_chat(request, chat_id):
    if request.method == "POST":

        History.objects.filter(
            user=request.user,
            chat_id=chat_id
        ).update(is_archived=False)

        return JsonResponse({"status": "unarchived"})

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required(login_url="login")
def archived_history(request):

    profile, _ = Profile.objects.get_or_create(user=request.user)

    messages = History.objects.filter(
        user=request.user,
        is_archived=True
    ).order_by("created_at")

    chat_groups = defaultdict(list)

    for msg in messages:
        chat_groups[msg.chat_id].append(msg)

    history_groups = []

    for chat_id, msgs in chat_groups.items():
        first_msg = msgs[0]

        history_groups.append({
            "chat_id": chat_id,
            "start_time": first_msg.created_at,
            "preview": first_msg.user_message[:60],
            "from_time": first_msg.created_at.isoformat(),
        })

    return render(request,"root/archive.html",{
        "history_groups":history_groups,
        "profile":profile
    })

@login_required(login_url="login")
def unarchive_chat(request, chat_id):

    if request.method == "POST":

        History.objects.filter(
            chat_id=chat_id,
            user=request.user
        ).update(is_archived=False)

        return JsonResponse({"status": "unarchived"})

    return JsonResponse({"error": "Invalid request"}, status=400)
