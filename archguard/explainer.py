import os
from typing import Any

import anthropic


def explain_violation(violation_type: str, details: Any, code_snippet: str = "") -> str:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY", "dummy_key")
    )

    prompt = f"""
You are ArchGuard, an expert software architect AI.
A developer has introduced an architecture violation into the codebase.
Explain the violation clearly in plain English and recommend how to fix it.

Violation Type: {violation_type}
Details: {details}
Code Snippet:
```python
{code_snippet}
```

Keep your explanation concise, friendly, and actionable. Do not use markdown headers.
"""

    if os.environ.get("ANTHROPIC_API_KEY") is None or os.environ.get("ANTHROPIC_API_KEY") == "dummy_key":
         # Return a mocked explanation if no API key is provided
         return f"Mocked Explanation for {violation_type}: The code introduces a {violation_type}. Please refactor to decouple the services."

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error connecting to Anthropic API: {str(e)}"
