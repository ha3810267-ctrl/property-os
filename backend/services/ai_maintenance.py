import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize client without passing the model
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
    "recommended_action": "short recommended next action"
}

Rules:
- Do not invent facts.
- Use only information contained in the tenant's message.
- Choose the priority based on urgency and potential property damage or safety risk.
- Keep the summary and recommended action concise.
"""


def analyse_maintenance_request(description):

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Maintenance description is required")

    # Use chat.completions.create and specify the model here
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
        "recommended_action"
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

    return data