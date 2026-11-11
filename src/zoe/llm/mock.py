"""Mock LLM client for testing and summarization."""

import re
from typing import Any, Dict, List, Optional


class MockLLMClient:
    """Mock LLM client that generates attributed summaries and tracks prompts."""

    name: str = "mock"

    def __init__(self, canned_response: Optional[str] = None):
        self.canned_response = canned_response
        self.calls: List[Dict[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        self.calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        })
        if self.canned_response is not None:
            return self.canned_response

        lower_prompt = user_prompt.lower()
        if "[cross-chat awareness directive]" in lower_prompt:
            if "[official knowledge — authoritative source]" in lower_prompt and "no official knowledge documents retrieved" not in lower_prompt:
                official_section = lower_prompt.split("[official knowledge — authoritative source]")[1].split("[")[0].strip()
                if official_section:
                    first_chunk = official_section.split("\n")[0].lstrip("- ")
                    return f"My apologies. I see the question in the group was about that. According to official project records, {first_chunk}"
            return "My apologies. I checked the community logs and see the question asked in the group. Here is the verified information from official records."

        if "[proactive radar intervention]" in lower_prompt:
            if any(k in lower_prompt for k in ["rug", "liquidity", "locked", "panic", "scam"]):
                return "I hear the concern, but I've analyzed the official data: liquidity is $93k and locked. We're good."
            return "I am detecting some concern in the chat regarding liquidity and project stability. Based on official project records, liquidity remains healthy and all contracts are verified."

        incoming_msg = (
            lower_prompt.split("[user incoming message]")[-1]
            if "[user incoming message]" in lower_prompt
            else lower_prompt
        )

        # Serious technical / vulnerability troubleshooting (strictly professional, no slang)
        if "vulnerability" in incoming_msg or "how do i fix" in incoming_msg:
            return (
                "To fix a smart contract vulnerability, first identify the specific vector such as "
                "reentrancy, access control flaws, or arithmetic issues. Apply established patterns like "
                "OpenZeppelin ReentrancyGuard, follow the checks-effects-interactions order, and verify the "
                "fix through automated testing and an external audit."
            )

        # Bullish / hype community milestone (matches energy with contextual slang)
        if any(h in incoming_msg for h in ["10x'd the liquidity", "10x", "10000 members", "10,000 members", "ath"]):
            return "Let's go! WAGMI fam, LFG!"
        if any(h in incoming_msg for h in ["why didn't you reply", "why didn't you answer", "why did you not reply", "why did you not answer", "why you didn't reply"]):
            return "I missed that message, my apologies! Let me answer it now."

        # Web3 casual greetings
        if "user: gm" in incoming_msg or incoming_msg.strip() == "gm":
            return "GM! What's the play today?"

        # Standard casual greetings
        if any(g in incoming_msg for g in ["user: hey", "user: hi", "user: hello", "user: sup"]) or incoming_msg.strip() in ("hey", "hi", "hello", "sup"):
            return "Hey! How is it going? Need an update on Hummingbird, or just checking in?"

        # Follow-up confirmations
        if re.search(r"\b(?:really|for\s+real|are\s+you\s+sure|fr|wait\s+really)\b", incoming_msg):
            if re.search(r"\bfr\b", incoming_msg):
                return "Yeah fr, just pulled that straight from DexScreener."
            if "price" in lower_prompt or "$0." in lower_prompt or "fly" in lower_prompt or "dexscreener" in lower_prompt:
                return "Yes, really! That is the live price from DexScreener right now."
            return "Yes, really! That is verified directly from official records."

        if "wen price update" in incoming_msg:
            return "Just checked DexScreener, $FLY is at $0.0024 right now."

        # Staking questions
        if "how do i stake" in incoming_msg or "how to stake" in incoming_msg:
            return "You can stake your tokens through the official Hummingbird staking portal. The unbonding period is 14 days. Do you want me to share the staking contract address?"

        # General knowledge / coding queries
        if "python" in incoming_msg and ("script" in incoming_msg or "loop" in incoming_msg or "code" in incoming_msg or "hello" in incoming_msg):
            return "Here is a Python script to say hello:\nprint('Hello, world!')"

        if "explain smart contract" in incoming_msg or "what is a smart contract" in incoming_msg:
            return "A smart contract is a self-executing digital agreement stored on a blockchain that executes automatically when predetermined conditions are met."

        if "blockchain" in incoming_msg:
            return "A blockchain is a decentralized distributed ledger that securely records transactions across a network of computers."

        # Conversational price inquiry with engagement follow-up question
        if "what is the price" in incoming_msg or "how much is" in incoming_msg or "price of fly" in incoming_msg:
            return "The current price of $FLY is $0.0024 USD with $93,712 in liquidity. Do you want me to check the 24h volume for you?"

        if "\n[live market data]\n" in lower_prompt:
            return "Just checked DexScreener, $FLY is at $0.0024 right now."

        if "[official knowledge — authoritative source]" in lower_prompt and "no official knowledge documents retrieved" not in lower_prompt:
            official_section = lower_prompt.split("[official knowledge — authoritative source]")[1].split("[")[0].strip()
            if official_section:
                for line in official_section.split("\n"):
                    line_clean = line.strip().lstrip("- ")
                    if "founder" in incoming_msg or "creator" in incoming_msg or "captain" in incoming_msg:
                        if "captain robbie olson" in line_clean or "captain robert olson" in line_clean or "creator" in line_clean:
                            return f"According to official project records, the founder and creator of $ONELOVE is Captain Robbie Olson (Captain Robert Olson)."
                first_chunk = official_section.split("\n")[0].lstrip("- ")
                return f"According to official project records, {first_chunk}"

        topics = []
        if "partnership" in lower_prompt:
            topics.append("a potential partnership")
        if "listing" in lower_prompt:
            topics.append("possible exchange listings")
        if "airdrop" in lower_prompt:
            topics.append("an unverified airdrop rumor")
        if "hack" in lower_prompt or "exploit" in lower_prompt:
            topics.append("security concerns and claims")
        if "delay" in lower_prompt:
            topics.append("speculation about project delays")

        if topics:
            return f"Several members discussed {', '.join(sorted(set(topics)))}. Community members also discussed general project topics."
        else:
            return "Community members discussed general questions regarding node operations, governance proposals, and ecosystem updates."

    def classify(self, text: str, categories: List[str], **kwargs: Any) -> str:
        """Simple mock category classifier."""
        return categories[0] if categories else "casual"

