import pytest
from zoe.conversation.classifier import classify_message


@pytest.mark.automated
def test_classifier_direct_question_vs_casual() -> None:
    # Casual examples
    casual_inputs = [
        "gm",
        "gm everyone!",
        "hello",
        "hey there",
        "good morning folks",
        "lol",
        "nice!",
        "thx",
    ]
    for text in casual_inputs:
        res = classify_message(text)
        assert res.category == "casual", f"Expected 'casual' for '{text}', got '{res.category}'"

    # Direct question examples
    question_inputs = [
        "What is the minimum bonding period for staking?",
        "How do I run a validator node on mainnet?",
        "Can anyone help with the RPC endpoint setup?",
        "Where can I find the official documentation?",
        "When is the next governance vote taking place?",
    ]
    for text in question_inputs:
        res = classify_message(text)
        assert res.category == "direct_question", f"Expected 'direct_question' for '{text}', got '{res.category}'"


@pytest.mark.automated
def test_classifier_escalation_and_spam() -> None:
    # Escalation
    esc = classify_message("Admin please help, my wallet was hacked and funds stolen!")
    assert esc.category == "escalation_trigger"
    assert esc.escalation_keyword in {"admin", "hacked", "stolen"}

    # Spam
    spam = classify_message("Claim free airdrop tokens here: https://scam-airdrop.xyz")
    assert spam.category == "spam"

