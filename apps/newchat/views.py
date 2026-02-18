
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import uuid, base64, traceback
from threading import Thread

from apps.newchat.forms import ChatbotMessageForm
from apps.history.models import History
from apps.profiles.models import Profile
from chatbox.openrouter_api import OpenRouterChatbot
from .guardrails import check_guardrails



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

    profile, _ = Profile.objects.get_or_create(user=request.user)

    # =====================
    # FETCH CHAT HISTORY
    # =====================
    conversation = []

    if not is_new_chat:
        db_history = History.objects.filter(
            user=request.user,
            chat_id=chat_id
        ).only("user_message", "ai_message", "uploaded_file", "created_at") \
        .order_by("-created_at")[:20]

        db_history = reversed(db_history)

        for item in db_history:
            if item.user_message or item.uploaded_file:
                conversation.append({
                    "role": "user",
                    "content": item.user_message,
                    "image": item.uploaded_file.url if item.uploaded_file else None
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
    # AJAX MESSAGE SEND (NON-STREAM)
    # =====================
    if request.method == "POST" and request.headers.get("X-Requested-With"):

        if limit_reached:
            return JsonResponse({
                "limit_reached": True,
                "remaining_seconds": remaining_seconds
            })

        try:
            # ✅ ALWAYS DEFINE FIRST
            message = request.POST.get("message", "").strip()
            # 🚫 Guardrails check
            if message and len(message) > 3 and not check_guardrails(message):
                return JsonResponse({"blocked": True}, status=403)


            uploaded_file = request.FILES.get("file")
            
            MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB

            if uploaded_file and uploaded_file.size > MAX_IMAGE_SIZE:
                return JsonResponse({"error": "Image too large"}, status=400)

            image_base64 = request.POST.get("image_base64")

            model = request.POST.get("model", "openai/gpt-4o-mini")
            chatbot_engine = OpenRouterChatbot(model=model)

            ai_message = message or "Describe this image"
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
                return JsonResponse({"error": form.errors}, status=400)

            reply = form.save(
                bot_engine=chatbot_engine,
                uploaded_file=uploaded_file,
                image_base64=image_base64
            )

            return JsonResponse({
                "reply": reply or "",
                "limit_reached": False
            })

        except Exception as e:
            traceback.print_exc()
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


# =====================
# STREAMING VIEW
# =====================
@csrf_exempt
@login_required(login_url="login")
def stream_chatbot(request):
    
    """
    Streaming chatbot response (Server-Sent like plain text stream)
    """

    if request.method != "POST":
        return StreamingHttpResponse("Invalid request", status=405)

    try:
        # =====================
        # SAFE INPUT HANDLING
        # =====================
        message = request.POST.get("message", "").strip()
        # 🚫 Guardrails check
        if message and len(message) > 3 and not check_guardrails(message):
            return StreamingHttpResponse(
                '{"blocked": true}',
                status=403,
                content_type="application/json"
            )


        chat_id = request.POST.get("chat_id")
        image_base64 = request.POST.get("image_base64")
        uploaded_file = request.FILES.get("file")

        # Model from frontend
        model = request.POST.get("model", "openai/gpt-4o-mini")

        if not chat_id:
            return StreamingHttpResponse("Missing chat_id", status=400)

        # =====================
        # LOAD CHAT HISTORY
        # =====================
        db_history = History.objects.filter(
            user=request.user,
            chat_id=chat_id
        ).only("user_message", "ai_message", "uploaded_file", "created_at") \
        .order_by("-created_at")[:20]

        db_history = reversed(db_history)


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

        # =====================
        # FILE / IMAGE HANDLING
        # =====================
        final_prompt = message or "[Image]"
        
        if uploaded_file:
            if uploaded_file.content_type.startswith("image"):
                image_base64 = base64.b64encode(
                    uploaded_file.read()
                ).decode("utf-8")
                uploaded_file.seek(0)

            elif uploaded_file.content_type.startswith("text"):
                text = uploaded_file.read().decode(errors="ignore")[:1000]
                uploaded_file.seek(0)
                final_prompt += f"\n\n[Text File]\n{text}"

            else:
                final_prompt += f"\n\n[File]\n{uploaded_file.name}"

        # =====================
        # INIT CHATBOT
        # =====================
        chatbot_engine = OpenRouterChatbot(model=model)

        # =====================
        # STREAM GENERATOR
        # =====================
        def event_stream():
            full_reply = ""

            try:
                for token in chatbot_engine.stream_response(
                    user_input=final_prompt,
                    conversation_history=conversation,
                    image_base64=image_base64,
                    model=model
                ):
                    full_reply += token
                    yield token

            except Exception as e:
                yield f"\n\n[Error: {str(e)}]"

            finally:
                # =====================
                # SAVE CHAT HISTORY
                # =====================
                def save_history():
                    History.objects.create(
                        user=request.user,
                        chat_id=chat_id,
                        user_message=message,
                        ai_message=full_reply,
                        uploaded_file=uploaded_file
                    )

                Thread(target=save_history).start()


        return StreamingHttpResponse(
            event_stream(),
            content_type="text/plain"
        )

    except Exception as e:
        traceback.print_exc()
        return StreamingHttpResponse(
            f"Server error: {str(e)}",
            status=500
        ) 