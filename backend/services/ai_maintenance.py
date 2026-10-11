import json
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
You are Matchly's general-purpose service intelligence system.

Matchly helps people find suitable service providers for tasks,
problems, projects and other needs.

Analyse the customer's description and return ONLY valid JSON.

The JSON must contain exactly these fields:

{
    "summary": "short description of what the customer needs",
    "category": "short, dynamically generated description of the service",
    "priority": "low | normal | high | urgent",
    "issue": "specific need, task or problem identified",
    "recommended_action": "short recommended next action",
    "required_trades": [
        {
            "trade": "specific service provider type or speciality required",
            "reason": "short reason this provider is suitable"
        }
    ]
}

GENERAL RULES:

- This is NOT a property-maintenance-only system.
- The customer may request ANY legitimate service.
- Do not choose from a predefined category or service list.
- Infer the appropriate service directly from the customer's description.
- Generate natural, specific category and provider descriptions.
- Do not force requests into property maintenance categories.
- Do not assume the customer is a tenant or property manager.
- Do not assume the task concerns a property.
- Do not invent facts that the customer has not provided.
- Keep the summary, issue and recommended action concise.
- Use the customer's actual requirements to determine suitable providers.

PROVIDER REQUIREMENTS:

- required_trades is retained as a field name for compatibility.
  Its entries represent ANY suitable provider type, not just tradespeople.
- Examples include tutors, photographers, cleaners, gardeners,
  removal companies, web developers, designers, mechanics,
  caterers, translators, plumbers and electricians.
- These are examples only, not an exhaustive or predefined list.
- Generate any provider description that fits the actual request.
- Use multiple provider types when the request genuinely requires
  different specialities.
- Do not add extra provider types merely because they might help.
- If one provider can reasonably fulfil the request, return one.
- Each provider type must be specific enough to guide a real-world
  search while remaining flexible about how businesses describe
  their services.
- Explain briefly why each provider type is suitable.
- If the request is unclear, identify the missing information
  through the summary and recommended action rather than inventing
  requirements.

PRIORITY:

- low: non-urgent request with little immediate impact.
- normal: ordinary request with no clear immediate urgency.
- high: time-sensitive request or significant potential impact.
- urgent: immediate danger or a serious time-critical situation.
- Judge priority in context. Do not automatically treat every
  request as a property emergency.

Return valid JSON with exactly the specified fields.
"""


def analyse_maintenance_request(description):

    if not isinstance(description, str) or not description.strip():
        raise ValueError("A service description is required")

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
    except (json.JSONDecodeError, TypeError):
        raise ValueError("AI returned invalid JSON")

    required_fields = {
        "summary",
        "category",
        "priority",
        "issue",
        "recommended_action",
        "required_trades"
    }

    if not isinstance(data, dict) or set(data.keys()) != required_fields:
        raise ValueError("AI returned an invalid service analysis structure")

    for field in (
        "summary",
        "category",
        "issue",
        "recommended_action"
    ):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(f"AI returned an invalid {field}")

    if data["priority"] not in {
        "low",
        "normal",
        "high",
        "urgent"
    }:
        raise ValueError("AI returned an invalid priority")

    if not isinstance(data["required_trades"], list):
        raise ValueError("AI returned an invalid provider requirements structure")

    if not data["required_trades"]:
        raise ValueError("AI returned no suitable provider requirements")

    for provider in data["required_trades"]:

        if not isinstance(provider, dict):
            raise ValueError("AI returned an invalid provider requirement")

        if set(provider.keys()) != {"trade", "reason"}:
            raise ValueError("AI returned an invalid provider requirement structure")

        if (
            not isinstance(provider["trade"], str)
            or not provider["trade"].strip()
        ):
            raise ValueError("AI returned an invalid provider type")

        if (
            not isinstance(provider["reason"], str)
            or not provider["reason"].strip()
        ):
            raise ValueError("AI returned an invalid provider reason")

    return data