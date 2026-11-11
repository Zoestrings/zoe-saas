import pytest
from zoe.safety.validator import validate_output


@pytest.mark.automated
def test_safety_validator_rejects_price_predictions() -> None:
    bad_outputs = [
        "This coin is going to the moon very soon!",
        "The token will hit $50 by end of month.",
        "Expect a 100x return from here.",
        "Guaranteed profit once the mainnet launches.",
    ]
    for text in bad_outputs:
        res = validate_output(text)
        assert not res.is_safe, f"Expected unsafe for: {text}"
        assert "prohibited_price_prediction" in res.violations


@pytest.mark.automated
def test_safety_validator_rejects_kyc_and_seed_phrases() -> None:
    kyc_bad = "We guarantee KYC approval within 5 minutes without ID."
    res = validate_output(kyc_bad)
    assert not res.is_safe
    assert "prohibited_kyc_promise" in res.violations

    seed_bad = "Please enter your 12 words seed phrase to verify ownership."
    res2 = validate_output(seed_bad)
    assert not res2.is_safe
    assert "prohibited_credential_request" in res2.violations


@pytest.mark.automated
def test_safety_validator_fail_closed_on_exception(monkeypatch) -> None:
    """Validator must fail-closed if an unexpected error occurs during validation."""
    def crash(*args, **kwargs):
        raise RuntimeError("Unexpected regex parsing failure")

    monkeypatch.setattr("re.findall", crash)
    res = validate_output("Normal response")
    assert not res.is_safe
    assert any("validation_exception" in v for v in res.violations)

