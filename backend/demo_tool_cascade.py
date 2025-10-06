#!/usr/bin/env python
"""
Demonstration of tool configuration cascade functionality.

Shows how per-agent tool enable/disable and parameter configuration works
using the generic cascade infrastructure.
"""

import asyncio
from app.agents.config_loader import get_agent_tool_config


async def main():
    print("=" * 80)
    print("Tool Configuration Cascade Demonstration")
    print("=" * 80)
    print()
    
    # Demonstrate vector_search tool configuration
    print("1. Vector Search Tool Configuration:")
    print("-" * 80)
    vector_config = await get_agent_tool_config("simple_chat", "vector_search")
    for key, value in vector_config.items():
        print(f"   {key:25} = {value}")
    print()
    
    # Demonstrate web_search tool configuration  
    print("2. Web Search Tool Configuration:")
    print("-" * 80)
    web_config = await get_agent_tool_config("simple_chat", "web_search")
    for key, value in web_config.items():
        print(f"   {key:25} = {value}")
    print()
    
    # Demonstrate conversation_management tool configuration
    print("3. Conversation Management Tool Configuration:")
    print("-" * 80)
    conv_config = await get_agent_tool_config("simple_chat", "conversation_management")
    for key, value in conv_config.items():
        print(f"   {key:25} = {value}")
    print()
    
    # Demonstrate fallback behavior for unconfigured tools
    print("4. Profile Capture Tool (using fallback):")
    print("-" * 80)
    profile_config = await get_agent_tool_config("simple_chat", "profile_capture")
    for key, value in profile_config.items():
        print(f"   {key:25} = {value}")
    print()
    
    # Demonstrate fallback behavior for email summary
    print("5. Email Summary Tool (using fallback):")
    print("-" * 80)
    email_config = await get_agent_tool_config("simple_chat", "email_summary")
    for key, value in email_config.items():
        print(f"   {key:25} = {value}")
    print()
    
    # Summary
    print("=" * 80)
    print("Summary:")
    print("- Tools 1-3 are configured in agent config with specific parameters")
    print("- Tools 4-5 use fallback values (disabled by default)")
    print("- Each parameter cascades independently (mixed inheritance)")
    print("- Comprehensive audit trail logging happens behind the scenes")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

