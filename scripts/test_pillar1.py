import sys
sys.path.insert(0, "src")

from zoe.tools.news import fetch_crypto_news
from zoe.tools.web_search import search_web
from zoe.conversation.router import route_intent
from zoe.conversation.prompt_builder import DEFAULT_ZOE_IDENTITY_PROMPT

print("Router tests:")
print("Latest news on XRP ->", route_intent("What is the latest news on XRP?"))
print("Search web for ETH ->", route_intent("Search the web for the new Ethereum upgrade"))
print("DeFi today ->", route_intent("What is happening in DeFi today?"))
print("Prompt contains brand persona ->", "elite intelligence terminal" in DEFAULT_ZOE_IDENTITY_PROMPT)
