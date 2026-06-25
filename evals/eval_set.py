TIER_1 = [
    {
        "query": "derivative instruments",
        "expected_substring": "uses derivative instruments",
        "company": "aapl",
    },
    {
        "query": "global minimum tax standards",
        "expected_substring": "global minimum tax standards",
        "company": "aapl",
    },
    {
        "query": "net sales",
        "expected_substring": "net sales",
        "company": "aapl",
    },
]

TIER_2 = [
    {
        "query": "what was Apple's total revenue this year?",
        "expected_substring": "net sales",
        "company": "aapl",
    },
]

EVAL_SET = TIER_1 + TIER_2