from typing import Optional, Type, TypeVar, Any, List
import os
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)

class GeminiService:
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
        self._llm = None
        self._client = None
        self._embeddings = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def get_llm(self, model_name: Optional[str] = None) -> ChatGoogleGenerativeAI:
        if not self.is_configured:
            raise ValueError("GOOGLE_API_KEY is not configured in backend environment")
        model = model_name or settings.GEMINI_TEXT_MODEL
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=self.api_key,
            temperature=0.3,
            max_retries=3,
            timeout=60
        )

    def get_embeddings(self) -> GoogleGenerativeAIEmbeddings:
        if not self.is_configured:
            raise ValueError("GOOGLE_API_KEY is not configured in backend environment")
        return GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=self.api_key
        )

    def invoke_structured(
        self,
        schema: Type[T],
        system_prompt: str,
        user_prompt: str,
        model_name: Optional[str] = None
    ) -> T:
        """Invoke Gemini with structured output validation using Pydantic schema."""
        llm = self.get_llm(model_name)
        structured_llm = llm.with_structured_output(schema)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        result = structured_llm.invoke(messages)
        return result

    def invoke_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model_name: Optional[str] = None
    ) -> str:
        """Invoke Gemini for text generation."""
        llm = self.get_llm(model_name)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        response = llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)

    def generate_image_bytes(self, prompt: str) -> bytes:
        """Generate image bytes using Google GenAI SDK."""
        if not self.is_configured:
            raise ValueError("GOOGLE_API_KEY is not configured for image generation")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            model_name = settings.GEMINI_IMAGE_MODEL

            # Try generating image
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_ONLY_HIGH"
                        )
                    ]
                )
            )

            parts = getattr(response, "parts", None)
            if not parts and getattr(response, "candidates", None):
                try:
                    parts = response.candidates[0].content.parts
                except Exception:
                    parts = None

            if not parts:
                raise RuntimeError(f"No image content returned by model {model_name}")

            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline and getattr(inline, "data", None):
                    return inline.data

            raise RuntimeError("No inline image bytes found in response")
        except Exception as e:
            logger.error(f"Image generation failed with model {settings.GEMINI_IMAGE_MODEL}: {e}")
            raise

gemini_service = GeminiService()
