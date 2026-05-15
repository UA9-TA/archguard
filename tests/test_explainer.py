import os

from archguard.explainer import explain_violation


def test_explain_violation_mock():
    # Ensure no API key is set for the test to use the mocked response
    if "ANTHROPIC_API_KEY" in os.environ:
        del os.environ["ANTHROPIC_API_KEY"]

    explanation = explain_violation(
        "Circular Dependency",
        "auth-service -> user-service -> auth-service"
    )
    assert "Mocked Explanation" in explanation
    assert "Circular Dependency" in explanation
