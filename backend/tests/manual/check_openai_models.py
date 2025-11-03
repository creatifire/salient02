"""
Copyright (c) 2025 Ape4, Inc. All rights reserved.
Unauthorized copying of this file is strictly prohibited.
"""

import sys
import os
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

import httpx
from dotenv import load_dotenv

env_path = backend_dir.parent / ".env"
load_dotenv(env_path)

response = httpx.get(
    'https://openrouter.ai/api/v1/models',
    headers={
        'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}',
        'HTTP-Referer': 'http://localhost:8000'
    },
    timeout=10.0
)

models = response.json()['data']
openai_models = [m for m in models if 'openai' in m['id'].lower() or ('gpt' in m['id'].lower() and 'openai' not in m['id'].lower())]

print(f"Found {len(openai_models)} OpenAI/GPT models:\n")
for m in sorted(openai_models, key=lambda x: x['id'])[:20]:
    print(f"{m['id']:<50} (context: {m.get('context_length', 'N/A'):,})")

