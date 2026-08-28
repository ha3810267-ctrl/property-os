import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
You are the maintenance intelligence system for a property management platform.

Analyse a tenant's maintenance message and return ONLY valid JSON.

The JSON must contain exactly these fields:

{
    "summary": "short description of the issue",
    "category": "issue category",
    "priority": "low | normal | high | urgent",
    "issue": "specific problem identified",
    "recommended_action": "short recommended next action",
    "required_trades": [
        {
            "trade": "specific trade or speciality required",
            "reason": "short reason this trade is required"
        }
    ]
}

Rules:

- Do not invent facts.
- Use only information contained in the tenant's message.
- Choose the priority based on urgency and potential property damage or safety risk.
- Keep the summary and recommended action concise.
- required_trades must contain at least one trade when the maintenance issue clearly requires a trade.
- Include multiple trades when the tenant's message clearly describes multiple distinct problems that reasonably require different specialities.
- Do not add multiple trades simply because they might possibly be useful.
- If one trade can reasonably handle the entire issue, return only one trade.
- Keep trade names simple and suitable for matching against worker specialities.
- Examples of trade names include plumber, electrician, heating engineer, roofer, locksmith, carpenter, painter, appliance repair technician.
"""


def analyse_maintenance_request(description):

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Maintenance description is required")

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": description.strip()
            }
        ]
    )

    result = response.choices[0].message.content

    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        raise ValueError("AI returned invalid JSON")

    required_fields = {
        "summary",
        "category",
        "priority",
        "issue",
        "recommended_action",
        "required_trades"
    }

    if set(data.keys()) != required_fields:
        raise ValueError("AI returned an invalid maintenance structure")

    if data["priority"] not in {
        "low",
        "normal",
        "high",
        "urgent"
    }:
        raise ValueError("AI returned an invalid priority")

    if not isinstance(data["required_trades"], list):
        raise ValueError("AI returned an invalid required_trades structure")

    if not data["required_trades"]:
        raise ValueError("AI returned no required trades")

    for trade in data["required_trades"]:
        if not isinstance(trade, dict):
            raise ValueError("AI returned an invalid trade")

        if set(trade.keys()) != {"trade", "reason"}:
            raise ValueError("AI returned an invalid trade structure")

        if not isinstance(trade["trade"], str) or not trade["trade"].strip():
            raise ValueError("AI returned an invalid trade name")

        if not isinstance(trade["reason"], str) or not trade["reason"].strip():
            raise ValueError("AI returned an invalid trade reason")

    return data