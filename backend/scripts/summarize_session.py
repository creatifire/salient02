#!/usr/bin/env python3
"""
Summarize a conversation session using OpenRouter and config-driven model settings.

This script:
1. Loads a session from the database by session_id
2. Retrieves all messages in the conversation thread
3. Reads model settings from a specified config.yaml file
4. Uses OpenRouter to generate an email-formatted conversation summary
5. Outputs the summary (print, file, or email via Mailgun)

Usage:
    python summarize_session.py <session_id> <config_path> [options]
    
Examples:
    # Print summary to stdout (English, default)
    python summarize_session.py abc123 backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml
    
    # French summary
    python summarize_session.py abc123 config.yaml --language french
    
    # Spanish HTML email
    python summarize_session.py abc123 config.yaml --language spanish --format html --email user@example.com
    
    # Save German summary to file
    python summarize_session.py abc123 config.yaml -l german --output summary.txt
    
    # All options
    python summarize_session.py abc123 config.yaml -l french --output summary.txt --email user@example.com --format html
"""
"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import yaml

# Add backend to path for imports
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession as SQLAsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import database models
from app.models.session import Session
from app.models.message import Message

# Import OpenRouter client
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()


class SessionSummarizer:
    """Generate conversation summaries using OpenRouter."""
    
    def __init__(
        self,
        session_id: str,
        config_path: str,
        openrouter_api_key: Optional[str] = None
    ):
        """
        Initialize summarizer with session and config.
        
        Args:
            session_id: Database session ID or session_key to summarize
            config_path: Path to agent config.yaml file with model_settings
            openrouter_api_key: OpenRouter API key (defaults to env var)
        """
        self.session_id = session_id
        self.config_path = Path(config_path)
        self.api_key = openrouter_api_key or os.getenv('OPENROUTER_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenRouter API key required (set OPENROUTER_API_KEY env var)")
        
        # OpenRouter client
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        # Loaded from config
        self.config: Optional[Dict[str, Any]] = None
        self.model_name: Optional[str] = None
        self.temperature: float = 0.7
        self.max_tokens: int = 2000
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Extract model settings
        model_settings = self.config.get('model_settings', {})
        self.model_name = model_settings.get('model', 'openai/gpt-4o-mini')
        self.temperature = model_settings.get('temperature', 0.7)
        self.max_tokens = model_settings.get('max_tokens', 2000)
        
        print(f"✓ Loaded config from: {self.config_path}")
        print(f"  Model: {self.model_name}")
        print(f"  Temperature: {self.temperature}")
        print(f"  Max tokens: {self.max_tokens}")
        
        return self.config
    
    async def load_session(self) -> Session:
        """Load session from database."""
        # Create database engine and session directly
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in environment")
        
        engine = create_async_engine(database_url, echo=False)
        async_session_factory = sessionmaker(engine, class_=SQLAsyncSession, expire_on_commit=False)
        
        async with async_session_factory() as db_session:
            # Try to find by ID (UUID) or session_key
            query = select(Session).options(
                selectinload(Session.messages)
            )
            
            # Check if session_id is a UUID or session_key
            try:
                # Try UUID format first
                from uuid import UUID
                uuid_val = UUID(self.session_id)
                query = query.where(Session.id == uuid_val)
            except ValueError:
                # Fall back to session_key
                query = query.where(Session.session_key == self.session_id)
            
            result = await db_session.execute(query)
            session = result.scalar_one_or_none()
            
            if not session:
                raise ValueError(f"Session not found: {self.session_id}")
            
            # Load messages separately with proper ordering
            messages_query = (
                select(Message)
                .where(Message.session_id == session.id)
                .order_by(Message.created_at.asc())
            )
            messages_result = await db_session.execute(messages_query)
            messages = list(messages_result.scalars().all())
            
            print(f"\n✓ Loaded session: {session.id}")
            print(f"  Session key: {session.session_key}")
            print(f"  Created: {session.created_at}")
            print(f"  Messages: {len(messages)}")
            print(f"  Account: {session.account_slug}")
            print(f"  Agent: {session.agent_instance_slug}")
            
            # Attach messages to session for easy access
            session.messages = messages
            
            return session
    
    def format_conversation(self, session: Session) -> str:
        """Format conversation messages for summarization."""
        lines = []
        lines.append(f"Conversation from {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Account: {session.account_slug}")
        lines.append(f"Agent: {session.agent_instance_slug}")
        lines.append(f"Total messages: {len(session.messages)}\n")
        lines.append("=" * 80)
        lines.append("")
        
        for msg in session.messages:
            role_label = msg.role.upper()
            timestamp = msg.created_at.strftime('%H:%M:%S')
            lines.append(f"[{timestamp}] {role_label}:")
            lines.append(msg.content)
            lines.append("")
        
        return "\n".join(lines)
    
    async def generate_summary(
        self,
        session: Session,
        format_type: str = "text",
        language: str = "english"
    ) -> str:
        """
        Generate conversation summary using OpenRouter.
        
        Args:
            session: Session with loaded messages
            format_type: Output format ("text" or "html")
            language: Target language for summary (natural language name)
            
        Returns:
            Generated summary text
        """
        # Build conversation context
        conversation_text = self.format_conversation(session)
        
        # Create system prompt for summarization
        if format_type == "html":
            format_instructions = """
Generate an HTML-formatted email summary with:
- Professional email styling
- Clear section headings
- Bullet points for key topics
- Highlighted important information
- Proper HTML structure (use <h2>, <p>, <ul>, <li>, <strong>)
"""
        else:
            format_instructions = """
Generate a clear, professional text summary with:
- Brief introduction
- Key topics discussed (bullet points)
- Important details or outcomes
- Next steps or action items (if any)
"""
        
        # Language instruction
        language_instruction = f"""
IMPORTANT: Generate the entire summary in {language.title()}.
All text, headings, and content must be in {language.title()}.
"""
        
        system_prompt = f"""You are an expert at summarizing conversations for email delivery.

{language_instruction}

{format_instructions}

Keep the summary concise (200-400 words) but comprehensive. Focus on:
1. Main topics discussed
2. Key information provided
3. Questions asked and answered
4. Any action items or follow-ups

Be professional and clear. The recipient should understand the conversation without reading the full transcript."""

        # Create messages for OpenRouter
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please summarize this conversation:\n\n{conversation_text}"}
        ]
        
        print(f"\n⏳ Generating summary with {self.model_name}...")
        
        # Call OpenRouter
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            extra_body={
                "usage": {"include": True}  # Enable cost tracking
            }
        )
        
        # Extract summary
        summary = response.choices[0].message.content
        
        # Log usage information
        usage = response.usage
        if usage:
            print(f"✓ Summary generated")
            print(f"  Tokens - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
        
        return summary
    
    async def save_to_file(self, summary: str, output_path: str):
        """Save summary to file."""
        with open(output_path, 'w') as f:
            f.write(summary)
        print(f"✓ Summary saved to: {output_path}")
    
    async def send_email(
        self,
        summary: str,
        recipient: str,
        session: Session,
        format_type: str = "text"
    ):
        """Send summary via Mailgun."""
        try:
            import requests
        except ImportError:
            print("✗ Error: requests library required for email. Install: pip install requests")
            return
        
        mailgun_api_key = os.getenv('MAILGUN_API_KEY')
        mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        
        if not mailgun_api_key or not mailgun_domain:
            print("✗ Error: MAILGUN_API_KEY and MAILGUN_DOMAIN required for email")
            return
        
        # Prepare email
        subject = f"Conversation Summary - {session.account_slug} - {session.created_at.strftime('%Y-%m-%d')}"
        
        if format_type == "html":
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Conversation Summary</h1>
            <p><strong>Date:</strong> {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Account:</strong> {session.account_slug}</p>
        </div>
        
        {summary}
        
        <div class="footer">
            <p>This summary was automatically generated from your conversation.</p>
        </div>
    </div>
</body>
</html>
"""
            # Send HTML email
            response = requests.post(
                f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                auth=("api", mailgun_api_key),
                data={
                    "from": f"Salient Chat <noreply@{mailgun_domain}>",
                    "to": [recipient],
                    "subject": subject,
                    "html": html_body
                }
            )
        else:
            # Send text email
            text_body = f"""
Conversation Summary
Date: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Account: {session.account_slug}

{summary}

---
This summary was automatically generated from your conversation.
"""
            response = requests.post(
                f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                auth=("api", mailgun_api_key),
                data={
                    "from": f"Salient Chat <noreply@{mailgun_domain}>",
                    "to": [recipient],
                    "subject": subject,
                    "text": text_body
                }
            )
        
        if response.status_code == 200:
            print(f"✓ Email sent to: {recipient}")
        else:
            print(f"✗ Email failed: {response.status_code} - {response.text}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Summarize a conversation session using OpenRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print summary to stdout (English, default)
  python summarize_session.py abc123 backend/config/agent_configs/windriver/windriver_info_chat1/config.yaml
  
  # French summary
  python summarize_session.py abc123 config.yaml --language french
  
  # Spanish HTML email
  python summarize_session.py abc123 config.yaml --language spanish --format html --email user@example.com
  
  # Save German summary to file
  python summarize_session.py abc123 config.yaml -l german --output zusammenfassung.txt
  
  # All options
  python summarize_session.py abc123 config.yaml -l french --output summary.txt --email user@example.com --format html
"""
    )
    
    parser.add_argument(
        'session_id', 
        help='Session ID (UUID) or session_key to summarize'
    )
    
    parser.add_argument(
        'config_path',
        help='Path to agent config.yaml file with model_settings'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Save summary to file (path)',
        metavar='FILE'
    )
    
    parser.add_argument(
        '--email', '-e',
        help='Send summary via email to this address',
        metavar='EMAIL'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['text', 'html'],
        default='text',
        help='Output format (text or html, default: text)'
    )
    
    parser.add_argument(
        '--language', '-l',
        default='english',
        help='Language for summary (e.g., english, french, spanish, german, default: english)',
        metavar='LANG'
    )
    
    parser.add_argument(
        '--api-key', '-k',
        help='OpenRouter API key (defaults to OPENROUTER_API_KEY env var)',
        metavar='KEY'
    )
    
    args = parser.parse_args()
    
    # Create summarizer
    try:
        summarizer = SessionSummarizer(
            session_id=args.session_id,
            config_path=args.config_path,
            openrouter_api_key=args.api_key
        )
        
        # Load config
        summarizer.load_config()
        
        # Load session
        session = await summarizer.load_session()
        
        if len(session.messages) == 0:
            print("\n⚠ Warning: No messages found in this session")
            return
        
        # Generate summary
        summary = await summarizer.generate_summary(
            session, 
            format_type=args.format,
            language=args.language
        )
        
        # Output summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(summary)
        print("=" * 80)
        
        # Save to file if requested
        if args.output:
            await summarizer.save_to_file(summary, args.output)
        
        # Send email if requested
        if args.email:
            await summarizer.send_email(summary, args.email, session, format_type=args.format)
        
        print("\n✓ Done!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
