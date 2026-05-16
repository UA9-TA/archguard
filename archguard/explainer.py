import os

from anthropic import Anthropic


def explain_violation(violation_type: str, details: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "ANTHROPIC_API_KEY not set. Cannot explain violation."

    client = Anthropic(api_key=api_key)

    prompt = f"""
    You are an expert software architect. Explain the following microservice architecture violation in plain English and recommend a fix.

    Violation Type: {violation_type}
    Details:
    {details}
    """

    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error explaining violation: {e}"
