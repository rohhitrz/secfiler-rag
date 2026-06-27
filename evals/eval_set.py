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
    {
        "query": "research and development",
        "expected_substring": "research and development",
        "company": "msft",
    },

    # Tesla
    {
        "query": "Megapack",
        "expected_substring": "Megapack",
        "company": "tsla",
    },
]

TIER_2 = [
    {
        "query": "what was Apple's total revenue this year?",
        "expected_substring": "net sales",
        "company": "aapl",
    },
     # Microsoft
    {
        "query": "What are Microsoft's main business segments?",
        "expected_substring": "Productivity and Business Processes",
        "company": "msft",
    },

    # Tesla
    {
        "query": "What products make up Tesla's energy business?",
        "expected_substring": "Powerwall",
        "company": "tsla",
    },
]


EVAL_SET = TIER_1 + TIER_2