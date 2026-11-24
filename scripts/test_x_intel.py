import sys
sys.path.insert(0, "src")

from zoe.conversation.router import route_intent, extract_x_intel_target
from zoe.tools.x_intel import analyze_x_sentiment_sync

print("Testing X intelligence router:")
r1 = route_intent("What is CT saying about Solana?")
r2 = route_intent("What is the sentiment on X for $BTC?")
r3 = route_intent("What is trending on Crypto Twitter right now?")
r4 = route_intent("What are people on X saying about $ONELOVE?")

print("CT saying Solana ->", r1)
print("Sentiment on X for $BTC ->", r2)
print("Trending on Crypto Twitter ->", r3)
print("People on X saying ONELOVE ->", r4)

assert r1 == "x_intelligence", f"Expected x_intelligence, got {r1}"
assert r2 == "x_intelligence", f"Expected x_intelligence, got {r2}"
assert r3 == "x_intelligence", f"Expected x_intelligence, got {r3}"
assert r4 == "x_intelligence", f"Expected x_intelligence, got {r4}"

target = extract_x_intel_target("What is CT saying about Solana?")
print("Extracted target ->", target)
assert target == "SOLANA", f"Expected SOLANA, got {target}"

# Test fallback behavior when empty query or fewer than 3 tweets
empty_res = analyze_x_sentiment_sync("NonExistentToken99999XYZRandomNeverHeardOf")
print("Fallback result sentiment ->", empty_res.get("sentiment"))
print("Fallback result summary ->", empty_res.get("summary"))
assert empty_res.get("sentiment") == "Unknown"
assert "Not enough recent public data" in empty_res.get("summary")

print("\nALL X INTELLIGENCE TESTS PASSED SUCCESSFULLY!")
