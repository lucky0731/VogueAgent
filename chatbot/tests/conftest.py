"""
Test setup for the shopping assistant. Everything runs offline:

- MongoDB is an in-memory mongomock database seeded with a small catalogue
- the shopping agent runs on a scripted model (``script_agent``) instead of an LLM
- Groq/Portkey calls (guardrails, Whisper, vision) are replaced by ``fake_llm``

so the suite needs no API keys, no network and no database.
"""
import base64
import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

# Must be set before the app is imported: these win over any real chatbot/.env.
os.environ.update({
    "MONGO_URI": "mongodb://localhost:27017/test",
    "GROQ_API_KEY": "gsk_test_key_for_offline_tests",
    "PORTKEY_API_KEY": "",
    "LOGFIRE_TOKEN": "",
    "STORE_URL": "http://localhost:8000",
})

import mongomock  # noqa: E402
import pymongo  # noqa: E402

pymongo.MongoClient = mongomock.MongoClient
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart  # noqa: E402
from pydantic_ai.models.function import FunctionModel  # noqa: E402

from app.api import app  # noqa: E402
from app.chatbot import agent as agent_module  # noqa: E402
from app.chatbot import guardrails, visual_search, voice  # noqa: E402
from app.database import products_collection  # noqa: E402


def jpeg(rgb: tuple[int, int, int], size=(120, 160)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, rgb).save(buf, "JPEG")
    return buf.getvalue()


CATALOGUE = [
    # name, category, colour, rgb, price
    ("Classic Black Tee", "men", "Black", (15, 15, 15), 499),
    ("Striped Polo Shirt", "men", "Navy", (25, 35, 95), 699),
    ("Sky Blue Linen Shirt", "men", "Blue", (120, 170, 230), 1299),
    ("Navy Oxford Shirt", "men", "Navy", (20, 30, 90), 2499),
    ("Blue Denim Jacket", "men", "Blue", (60, 90, 150), 3499),
    ("Red Floral Dress", "women", "Red", (200, 30, 40), 1799),
    ("Pink Cotton Kurti", "women", "Pink", (235, 150, 180), 899),
    ("Kids Dino Pyjamas", "kids", "Green", (40, 150, 70), 599),
]


@pytest.fixture(autouse=True)
def catalogue():
    """A fresh catalogue for every test, with real (tiny) product photos."""
    products_collection.delete_many({})
    products_collection.insert_many([
        {"name": n, "category": c, "color": [col], "size": ["S", "M", "L"], "price": float(p),
         "image_data": base64.b64encode(jpeg(rgb)).decode(), "image_content_type": "image/jpeg"}
        for n, c, col, rgb, p in CATALOGUE
    ])
    visual_search._catalog.clear()  # drop the photo-search cache
    yield


def completion(content: str):
    """Shape of an OpenAI/Groq chat completion, as far as the app reads it."""
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class FakeLLM:
    """Stands in for every Groq/Portkey call. Tests adjust the canned answers."""

    def __init__(self):
        self.injection_score = "0.01"
        self.input_verdict = {"violation": 0}
        self.output_verdict = {"violation": 0}
        self.vision_tags = {"is_clothing": True, "garment_type": "shirt", "category": "men",
                            "colors": ["blue"], "pattern": "solid", "style_keywords": ["linen"],
                            "description": "a light blue linen shirt"}
        self.transcript = "show me men's shirts under 2000"
        self.fail = set()          # model names that should raise
        self.calls = []            # (model, kwargs) for assertions

    async def chat_completion(self, model, **kwargs):
        self.calls.append((model, kwargs))
        if model in self.fail:
            raise RuntimeError(f"{model} unavailable")
        if model == guardrails.PROMPT_GUARD_MODEL_NAME:
            return completion(self.injection_score)
        if model == guardrails.GUARD_MODEL_NAME:
            is_input = kwargs["messages"][0]["content"] == guardrails.INPUT_POLICY
            return completion(json.dumps(self.input_verdict if is_input else self.output_verdict))
        if model == visual_search.settings.vision_model_name:
            return completion(json.dumps(self.vision_tags))
        raise AssertionError(f"unexpected model {model}")

    async def transcription(self, model, file, **kwargs):
        self.calls.append((model, {"file": file, **kwargs}))
        if model in self.fail:
            raise RuntimeError(f"{model} unavailable")
        return SimpleNamespace(text=self.transcript)


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    fake = FakeLLM()
    monkeypatch.setattr(guardrails, "chat_completion", fake.chat_completion)
    monkeypatch.setattr(visual_search, "chat_completion", fake.chat_completion)
    monkeypatch.setattr(voice, "transcription", fake.transcription)
    return fake


@pytest.fixture
def script_agent(monkeypatch):
    """
    Run the real agent (and its real search_products tool) on a scripted model:
    ``script_agent(tool_args, reply)`` makes the "LLM" call search_products with
    ``tool_args`` (or no tool if None), then answer ``reply``.
    """
    def use(tool_args: dict | None, reply: str = "Here you go!"):
        def model(messages, info):
            last = messages[-1].parts
            if tool_args is not None and not any(isinstance(p, ToolReturnPart) for p in last):
                return ModelResponse(parts=[ToolCallPart("search_products", tool_args)])
            tool_result = next((p.content for p in last if isinstance(p, ToolReturnPart)), None)
            return ModelResponse(parts=[TextPart(reply.format(tool=tool_result))])

        monkeypatch.setattr(agent_module.agent, "model", FunctionModel(model))

    return use


@pytest.fixture
def client():
    # Not used as a context manager, so the startup checks (real MongoDB/Groq) don't run.
    return TestClient(app)
