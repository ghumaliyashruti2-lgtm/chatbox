from django.conf import settings
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class OpenRouterChatbot:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY

        # ✅ CONFIRMED VISION MODEL
        self.model = "openai/gpt-4o-mini"

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def get_response(
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

            # ✅ ADD OLD CHAT (TEXT ONLY)
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # 🔥 IMAGE + TEXT (CORRECT FORMAT)
            if image_base64:
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_input or "Describe this image"
                        },
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

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=600,
                temperature=0.2
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.exception("AI error")
            return f"Error communicating with AI: {str(e)}"
