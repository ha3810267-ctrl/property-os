import os
from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze_maintenance_request(description):
    response = client.responses.create(
        model="gpt-5.6-luna",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a property maintenance AI assistant. "
                    "Analyze a tenant maintenance request and return "
                    "a concise structured assessment."
                )
            },
            {
                "role": "user",
                "content": description
            }
        ]
    )

    return response.output_text