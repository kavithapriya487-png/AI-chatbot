import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="public", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 384 * 1024

MAX_MESSAGES = 20
MAX_USER_MESSAGE_LENGTH = 8_000
MAX_ASSISTANT_MESSAGE_LENGTH = 16_000


class ChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


class AssistantConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_graph():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise AssistantConfigurationError("GROQ_API_KEY is not configured.")

    tools = [
        WikipediaQueryRun(
            api_wrapper=WikipediaAPIWrapper(
                top_k_results=1, doc_content_chars_max=500
            )
        ),
        ArxivQueryRun(
            api_wrapper=ArxivAPIWrapper(
                top_k_results=2, doc_content_chars_max=500
            ),
            description="Search academic papers on arXiv.",
        ),
    ]

    if os.getenv("TAVILY_API_KEY"):
        tools.append(TavilySearchResults())
    else:
        logger.warning("TAVILY_API_KEY is not configured; web search is disabled.")

    llm_with_tools = ChatGroq(
        model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
        api_key=api_key,
    ).bind_tools(tools)

    def call_assistant(state: ChatState) -> dict[str, list[AIMessage]]:
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    builder = StateGraph(ChatState)
    builder.add_node("assistant", call_assistant)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "assistant")
    builder.add_conditional_edges("assistant", tools_condition)
    builder.add_edge("tools", "assistant")
    return builder.compile()


def parse_messages(payload: object) -> list[AnyMessage]:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("Add a message before sending.")
    if len(messages) > MAX_MESSAGES:
        raise ValueError(f"Keep the conversation to {MAX_MESSAGES} messages or fewer.")

    parsed: list[AnyMessage] = []
    for message in messages:
        if not isinstance(message, dict):
            raise ValueError("Each message must include a role and content.")
        role = message.get("role")
        content = message.get("content")
        if (
            not isinstance(role, str)
            or role not in {"user", "assistant"}
            or not isinstance(content, str)
        ):
            raise ValueError("Messages must have a user or assistant role and text content.")
        max_length = (
            MAX_USER_MESSAGE_LENGTH
            if role == "user"
            else MAX_ASSISTANT_MESSAGE_LENGTH
        )
        if not content.strip() or len(content) > max_length:
            raise ValueError(f"Messages must contain 1 to {max_length} characters.")
        parsed.append(
            HumanMessage(content=content)
            if role == "user"
            else AIMessage(content=content)
        )

    if not isinstance(parsed[-1], HumanMessage):
        raise ValueError("The latest message must be from you.")
    return parsed


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    try:
        messages = parse_messages(request.get_json(silent=True))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    try:
        result = get_graph().invoke(
            {"messages": messages},
            config={"recursion_limit": 20},
        )
        answer = result["messages"][-1].content
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("The assistant returned an empty response.")
        return jsonify({"reply": answer})
    except AssistantConfigurationError as error:
        logger.error("Chat is not configured: %s", error)
        return jsonify(
            {"error": "The assistant is not configured yet. Please try again later."}
        ), 503
    except Exception:
        logger.exception("The assistant could not complete a chat request.")
        return jsonify({"error": "I couldn't complete that request. Please try again."}), 502


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify(
        {"error": "That request is too large. Please shorten your message."}
    ), 413
