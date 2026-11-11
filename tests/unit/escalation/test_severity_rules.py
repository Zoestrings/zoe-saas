import pytest
from zoe.escalation.handler import determine_severity


@pytest.mark.automated
def test_severity_rules_critical_vs_normal() -> None:
    # Critical: compromised wallet, stolen funds
    critical_text = "My wallet was compromised and all my funds were stolen!"
    assert determine_severity(critical_text) == "critical"

    hack_text = "Someone hacked the smart contract and exploited liquidity."
    assert determine_severity(hack_text) == "critical"

    # High: scam, phishing, impersonation
    high_text = "Watch out, there is a scam admin impersonator sending DMs."
    assert determine_severity(high_text) == "high"

    # Normal: general complaint, feedback, support request
    normal_text = "General complaint about the UI delay in the transaction dashboard."
    assert determine_severity(normal_text) == "normal"

    admin_inquiry = "Can an admin please help me find the link to the grant program?"
    assert determine_severity(admin_inquiry) == "normal"

