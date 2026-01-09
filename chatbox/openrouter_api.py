from django.conf import settings
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class OpenRouterChatbot:
    
    # TURN OFF STREAMING DATA FUNCTION 
    def get_response(self, user_input, conversation_history=None, image_base64=None):
        """
        NON-STREAM RESPONSE (used when streaming OFF)
        """

        full_reply = ""

        for token in self.stream_response(
            user_input=user_input,
            conversation_history=conversation_history,
            image_base64=image_base64,
            model=self.model
        ):
            full_reply += token

        return full_reply
    
    
    def __init__(self, model=None):
        self.api_key = settings.OPENROUTER_API_KEY

        # ✅ Default model fallback
        self.model = model or "openai/gpt-4o-mini"

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def stream_response(
    self,
    user_input,
    conversation_history,
    image_base64=None,
    model=None
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

            model = model or self.model

            stream = self.client.chat.completions.create(
                model=model,
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
                    yield delta.content

        except Exception as e:
            logger.exception("Streaming AI error")
            yield f"\n[Error]: {str(e)}"


