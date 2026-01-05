from django import forms
from apps.history.models import History


class ChatbotMessageForm(forms.Form):
    message = forms.CharField(required=False)

    def __init__(self, user, chat_id, conversation, *args, **kwargs):
        self.user = user
        self.chat_id = chat_id
        self.conversation = conversation
        super().__init__(*args, **kwargs)

    def save(self, bot_engine, uploaded_file=None, image_base64=None):

        user_message = self.cleaned_data.get("message", "")

        # =====================
        # AI RESPONSE
        # =====================
        ai_message = bot_engine.get_response(
            user_input=user_message,
            conversation_history=self.conversation,
            image_base64=image_base64
        )

        # =====================
        # SAVE TO DB (WITH FILE)
        # =====================
        History.objects.create(
            user=self.user,
            chat_id=self.chat_id,
            user_message=user_message,
            ai_message=ai_message,
            uploaded_file=uploaded_file   # ✅ THIS IS THE KEY LINE
        )

        return ai_message
