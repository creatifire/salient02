"""
Test what search_directory returns for Cardiology query.
"""
import asyncio
import sys
import os
sys.path.insert(0, '/Users/arifsufi/Documents/GitHub/OpenThought/salient02/backend')

# Set env for database
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres@localhost/salient_dev')

from app.agents.tools.directory_tools import search_directory
from app.agents.base.dependencies import SessionDependencies
from pydantic_ai import RunContext
from app.agents.config_loader import get_agent_config
from app.core.database import get_database_service
from app.models.account import Account
from sqlalchemy import select


async def test_search():
    """Test search_directory for Cardiology."""
    
    # Get account_id for Wyckoff
    db_service = get_database_service()
    await db_service.initialize()
    
    async with db_service.get_session() as session:
        result = await session.execute(
            select(Account).where(Account.slug == 'wyckoff')
        )
        account = result.scalar_one()
        account_id = account.id
    
    # Load Wyckoff config
    instance_config = get_agent_config('wyckoff', 'wyckoff_info_chat1')
    
    # Create deps
    deps = SessionDependencies(
        agent_config=instance_config,
        account_id=account_id,
        session_id=None
    )
    
    # Create context
    ctx = RunContext(deps=deps, retry=0, run_step=0)
    
    # Call the tool
    print("=" * 60)
    print("CALLING: search_directory(list_name='phone_directory', query='Cardiology')")
    print("=" * 60)
    
    result = await search_directory(
        ctx=ctx,
        list_name='phone_directory',
        query='Cardiology'
    )
    
    print("\nRESULT:")
    print(result)
    print("=" * 60)
    
    # Check if the correct phone number is in the result
    if '718-963-2000' in result:
        print("✅ CORRECT phone number (718-963-2000) is in the result")
    else:
        print("❌ CORRECT phone number (718-963-2000) is NOT in the result")
    
    if '718-963-7676' in result:
        print("⚠️  WRONG phone number (718-963-7676) is in the result - THIS SHOULDN'T BE HERE!")
    
    return result


if __name__ == '__main__':
    asyncio.run(test_search())

