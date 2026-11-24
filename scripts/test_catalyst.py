import sys
sys.path.insert(0, "src")

from zoe.conversation.router import route_intent, extract_catalyst_target
from zoe.tools.catalyst import get_upcoming_events_sync

print("Testing Catalyst Calendar router:")
r1 = route_intent("What is the next Ethereum upgrade?")
r2 = route_intent("Are there any upcoming events for Solana?")
r3 = route_intent("When is the next token unlock for Arbitrum?")
r4 = route_intent("When is the next event for Bitcoin?")

print("Next ETH upgrade ->", r1)
print("Upcoming events Solana ->", r2)
print("Next token unlock Arbitrum ->", r3)
print("Next event Bitcoin ->", r4)

assert r1 == "catalyst_calendar", f"Expected catalyst_calendar, got {r1}"
assert r2 == "catalyst_calendar", f"Expected catalyst_calendar, got {r2}"
assert r3 == "catalyst_calendar", f"Expected catalyst_calendar, got {r3}"
assert r4 == "catalyst_calendar", f"Expected catalyst_calendar, got {r4}"

t1 = extract_catalyst_target("What is the next Ethereum upgrade?")
t2 = extract_catalyst_target("When is the next token unlock for Arbitrum?")
print("Extracted target 1 ->", t1)
print("Extracted target 2 ->", t2)
assert t1 == "ETHEREUM", f"Expected ETHEREUM, got {t1}"
assert t2 == "ARBITRUM", f"Expected ARBITRUM, got {t2}"

# Test fallback behavior when empty query
empty_events = get_upcoming_events_sync("")
print("Empty query events ->", empty_events)
assert empty_events == []

print("\nALL CATALYST CALENDAR TESTS PASSED SUCCESSFULLY!")
