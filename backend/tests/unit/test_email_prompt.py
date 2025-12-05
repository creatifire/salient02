"""
Unit tests for email tool guidance in system prompt.
"""

import pytest
from pathlib import Path

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


def get_windriver_system_prompt():
    """Read Wind River system prompt file."""
    prompt_path = Path(__file__).parent.parent.parent / "config" / "agent_configs" / "windriver" / "windriver_info_chat1" / "system_prompt.md"
    
    if not prompt_path.exists():
        pytest.fail(f"System prompt not found at {prompt_path}")
    
    return prompt_path.read_text()


def test_system_prompt_includes_email_guidance():
    """Verify system prompt contains email summary guidance section."""
    prompt = get_windriver_system_prompt()
    
    # Check for section header
    assert "## Sending Conversation Summaries" in prompt, \
        "System prompt missing 'Sending Conversation Summaries' section"
    
    # Check for key guidance points
    assert "send_conversation_summary()" in prompt, \
        "System prompt doesn't mention send_conversation_summary() tool"
    
    assert "email address" in prompt.lower(), \
        "System prompt doesn't mention email address"
    
    # Check for "When to offer summaries" guidance
    assert "When to offer summaries" in prompt, \
        "System prompt missing 'When to offer summaries' guidance"
    
    # Check for example interactions
    assert "Example interactions" in prompt, \
        "System prompt missing example interactions"


@pytest.mark.skipif(not HAS_TIKTOKEN, reason="tiktoken not installed")
def test_system_prompt_token_count():
    """Verify system prompt doesn't exceed reasonable token limits."""
    prompt = get_windriver_system_prompt()
    
    # Use tiktoken to count tokens (accurate for OpenAI models)
    encoding = tiktoken.encoding_for_model("gpt-4")
    token_count = len(encoding.encode(prompt))
    
    # System prompt should be under 2000 tokens (reasonable limit)
    # OpenAI models typically have 8K-128K context windows
    # Leaving plenty of room for conversation history and responses
    assert token_count < 2000, \
        f"System prompt too long: {token_count} tokens (should be < 2000)"
    
    # Also verify it's not suspiciously short (sanity check)
    assert token_count > 500, \
        f"System prompt suspiciously short: {token_count} tokens"


def test_email_keywords_in_prompt():
    """Check for key email-related terms in system prompt."""
    prompt = get_windriver_system_prompt()
    
    # Core functionality keywords
    required_keywords = [
        "send_conversation_summary",  # Tool name
        "email",                       # Core concept
        "summary",                     # Core concept
        "summary_notes",               # Parameter name
    ]
    
    for keyword in required_keywords:
        assert keyword.lower() in prompt.lower(), \
            f"System prompt missing required keyword: '{keyword}'"


def test_email_guidance_includes_examples():
    """Verify email guidance includes practical examples."""
    prompt = get_windriver_system_prompt()
    
    # Extract the email summary section
    start_idx = prompt.find("## Sending Conversation Summaries")
    end_idx = prompt.find("## Communication Guidelines")
    
    assert start_idx != -1, "Email summary section not found"
    assert end_idx != -1, "Communication Guidelines section not found"
    
    email_section = prompt[start_idx:end_idx]
    
    # Check for practical examples
    assert "Can you email me" in email_section, \
        "Missing practical example: 'Can you email me'"
    
    assert "What's your email address" in email_section, \
        "Missing email collection example"
    
    # Check for summary_notes guidance
    assert "What to include in summary_notes parameter" in email_section, \
        "Missing summary_notes parameter guidance"


def test_email_guidance_placement():
    """Verify email guidance is placed appropriately in prompt structure."""
    prompt = get_windriver_system_prompt()
    
    # Check that email section comes after tool selection guide
    tool_guide_idx = prompt.find("### Tool Selection Guide")
    email_section_idx = prompt.find("## Sending Conversation Summaries")
    
    assert tool_guide_idx != -1, "Tool Selection Guide section not found"
    assert email_section_idx != -1, "Email section not found"
    assert email_section_idx > tool_guide_idx, \
        "Email guidance should come after Tool Selection Guide"
    
    # Check that email section comes before Communication Guidelines
    comm_guidelines_idx = prompt.find("## Communication Guidelines")
    assert comm_guidelines_idx != -1, "Communication Guidelines not found"
    assert email_section_idx < comm_guidelines_idx, \
        "Email guidance should come before Communication Guidelines"


def test_email_guidance_when_to_offer():
    """Verify guidance includes when to proactively offer summaries."""
    prompt = get_windriver_system_prompt()
    
    email_section_start = prompt.find("## Sending Conversation Summaries")
    email_section = prompt[email_section_start:email_section_start + 2000]  # Next ~2000 chars
    
    # Check for proactive offering guidance
    when_to_offer_triggers = [
        "complex medical information",
        "multiple services",
        "save or reference",
        "contact information"
    ]
    
    found_triggers = sum(1 for trigger in when_to_offer_triggers if trigger.lower() in email_section.lower())
    
    assert found_triggers >= 3, \
        f"Email guidance should mention at least 3 triggers for offering summaries (found {found_triggers})"

