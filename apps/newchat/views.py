from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import uuid, base64
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.newchat.forms import ChatbotMessageForm
from apps.history.models import History
from apps.profiles.models import Profile
from chatbox.openrouter_api import OpenRouterChatbot


# =====================
# CHAT LIMIT CONFIG
# =====================
MAX_MESSAGES = 10
CHAT_LIMIT_HOURS = 24


@login_required(login_url="login")
def new_chatbot(request):

    # =====================
    # CHAT ID HANDLING
    # =====================
    if request.GET.get("action") == "new":
        chat_id = str(uuid.uuid4())
        request.session["chat_id"] = chat_id
        is_new_chat = True
    else:
        chat_id = (
            request.GET.get("chat_id")
            or request.POST.get("chat_id")
            or request.session.get("chat_id")
            or str(uuid.uuid4())
        )
        request.session["chat_id"] = chat_id
        is_new_chat = False

    profile = Profile.objects.get(user=request.user)

    # =====================
    # FETCH CHAT HISTORY
    # =====================
    conversation = []

    if not is_new_chat:
        db_history = History.objects.filter(
            user=request.user,
            chat_id=chat_id
        ).order_by("created_at")

        for item in db_history:
            if item.user_message:
                conversation.append({
                    "role": "user",
                    "content": item.user_message,
                    "file": item.uploaded_file.url if item.uploaded_file else None,
                    "file_name": item.uploaded_file.name.split("/")[-1] if item.uploaded_file else None,
                    "is_image": (
                        item.uploaded_file.name.lower().endswith((".jpg", ".png", ".jpeg"))
                        if item.uploaded_file else False
                    )
                })

            if item.ai_message:
                conversation.append({
                    "role": "assistant",
                    "content": item.ai_message
                })

    # =====================
    # CHAT LIMIT
    # =====================
    now = timezone.now()
    window_start = now - timedelta(hours=CHAT_LIMIT_HOURS)

    recent_user_messages = History.objects.filter(
        user=request.user,
        chat_id=chat_id,
        created_at__gte=window_start
    ).exclude(user_message="").exclude(user_message__isnull=True)

    user_message_count = recent_user_messages.count()
    remaining_messages = max(0, MAX_MESSAGES - user_message_count)

    limit_reached = user_message_count >= MAX_MESSAGES
    remaining_seconds = 0

    if limit_reached:
        first_msg = recent_user_messages.first()
        expiry_time = first_msg.created_at + timedelta(hours=CHAT_LIMIT_HOURS)
        remaining_seconds = int((expiry_time - now).total_seconds())

    # =====================
    # AJAX MESSAGE SEND
    # =====================
    # =====================
    # AJAX MESSAGE SEND
    # =====================
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":

        if limit_reached:
            return JsonResponse({
                "limit_reached": True,
                "remaining_seconds": remaining_seconds
            })

        try:
            message = request.POST.get("message", "").strip()
            uploaded_file = request.FILES.get("file")

            # ✅ MODEL FROM DROPDOWN
            model = request.POST.get("model", "openai/gpt-4o-mini")

            chatbot_engine = OpenRouterChatbot(model=model)


            # ✅ DEFAULT PROMPT FOR IMAGE-ONLY MESSAGE
            ai_message = message or "Describe this image"
            image_base64 = None
            file_for_db = None

            if uploaded_file:
                file_for_db = uploaded_file

                if uploaded_file.content_type.startswith("image"):
                    image_base64 = base64.b64encode(
                        uploaded_file.read()
                    ).decode("utf-8")
                    uploaded_file.seek(0)

                elif uploaded_file.content_type.startswith("text"):
                    text = uploaded_file.read().decode(errors="ignore")[:1000]
                    uploaded_file.seek(0)
                    ai_message += f"\n\n[Text File]\n{text}"

                else:
                    ai_message += f"\n\n[File]\n{uploaded_file.name}"

            form = ChatbotMessageForm(
                user=request.user,
                chat_id=chat_id,
                conversation=conversation,
                data={"message": ai_message}
            )

            if not form.is_valid():
                return JsonResponse(
                    {"error": form.errors},
                    status=400
                )

            reply = form.save(
                bot_engine=chatbot_engine,
                uploaded_file=uploaded_file,
                image_base64=image_base64
            )

            # ✅ SAFE FILE URL (NO 500 ERROR)
            file_url = None
            if file_for_db and hasattr(file_for_db, "url"):
                file_url = file_for_db.url

            return JsonResponse({
                "reply": reply or "",
                "file_url": file_url,
                "file_name": (
                    file_for_db.name.split("/")[-1]
                    if file_for_db else None
                ),
                "limit_reached": False
            })

        except Exception as e:
            # 🔥 NEVER RETURN HTML ERROR TO JS
            print("CHATBOT ERROR:", str(e))
            return JsonResponse(
                {"error": "Server error", "detail": str(e)},
                status=500
            )

    # =====================
    # PAGE LOAD
    # =====================
    return render(request, "root/chatbot.html", {
        "conversation": conversation,
        "profile": profile,
        "chat_id": chat_id,
        "limit_reached": limit_reached,
        "remaining_seconds": remaining_seconds,
        "remaining_messages": remaining_messages,
    })

@csrf_exempt
@login_required(login_url="login")
@csrf_exempt
@login_required(login_url="login")
def stream_chatbot(request):

    message = request.POST.get("message", "").strip()
    chat_id = request.POST.get("chat_id")
    image_base64 = request.POST.get("image_base64")

    # ✅ MODEL FROM FRONTEND
    model = request.POST.get("model", "openai/gpt-4o-mini")

    if not chat_id:
        return StreamingHttpResponse("Missing chat_id", status=400)

    # Load history
    db_history = History.objects.filter(
        user=request.user,
        chat_id=chat_id
    ).order_by("created_at")

    conversation = []
    for item in db_history:
        if item.user_message:
            conversation.append({
                "role": "user",
                "content": item.user_message
            })
        if item.ai_message:
            conversation.append({
                "role": "assistant",
                "content": item.ai_message
            })

    # ✅ CREATE CHATBOT PER REQUEST
    chatbot_engine = OpenRouterChatbot(model=model)

    def event_stream():
        full_reply = ""

        for token in chatbot_engine.stream_response(
            user_input=message or "Describe this image",
            conversation_history=conversation,
            image_base64=image_base64,
            model=model
        ):

            full_reply += token
            yield token

        # ✅ SAVE HISTORY AFTER STREAM
        History.objects.create(
            user=request.user,
            chat_id=chat_id,
            user_message=message,
            ai_message=full_reply
        )

    return StreamingHttpResponse(
        event_stream(),
        content_type="text/plain"
    )
