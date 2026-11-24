from zoe.worker.pipeline import CREDIT_COSTS, check_and_deduct_credit

print("CREDIT_COSTS:", CREDIT_COSTS)
assert CREDIT_COSTS["basic_chat"] == 1
assert CREDIT_COSTS["web_search"] == 5
assert CREDIT_COSTS["x_sentiment"] == 10
assert CREDIT_COSTS["token_scan"] == 15
assert CREDIT_COSTS["contract_audit"] == 50
assert CREDIT_COSTS["contract_generate"] == 30

# Test anonymous / community group check
allowed, msg, balance = check_and_deduct_credit(None, "contract_audit")
print("Anonymous allowed:", allowed, balance)
assert allowed is True

# Test offline / fallback check
allowed, msg, balance = check_and_deduct_credit("test_user_123", "basic_chat")
print("User check:", allowed, msg, balance)
assert allowed is True

print("Pipeline credit tests passed successfully!")
