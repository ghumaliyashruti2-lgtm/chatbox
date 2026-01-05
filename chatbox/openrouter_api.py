from django.conf import settings
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class OpenRouterChatbot:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = "openai/gpt-4o-mini"

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def stream_response(
        self,
        user_input,
        conversation_history,
        image_base64=None
    ):
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are ElixirTechne HelpDesk chatbot. "
                        "Analyze images if provided and reply clearly."
                    )
                }
            ]

            # ✅ Previous messages
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # ✅ User message
            if image_base64:
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_input or "Describe this image"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                })
            else:
                messages.append({
                    "role": "user",
                    "content": user_input
                })

            # 🔥 STREAMING CALL
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=600,
                stream=True
            )

            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content  # ⬅ token by token

        except Exception as e:
            logger.exception("Streaming AI error")
            yield f"\n[Error]: {str(e)}"
