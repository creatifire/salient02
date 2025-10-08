"""
Agent instance loader for multi-tenant architecture.

Loads agent instances from database + config files, validating existence,
status, and updating usage timestamps.

Architecture:
- Database: Metadata (account, instance, status, timestamps)
- Config Files: Agent configuration (model, tools, prompts)

Path: {configs_directory}/{account_slug}/{instance_slug}/config.yaml
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

import yaml
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db_session


@dataclass
class AgentInstance:
    """Agent instance with database metadata + config file data."""
    
    # Database fields
    id: UUID
    account_id: UUID
    account_slug: str
    instance_slug: str
    agent_type: str
    display_name: str
    status: str
    last_used_at: Optional[datetime]
    
    # Config file data
    config: dict
    system_prompt: Optional[str] = None


async def load_agent_instance(
    account_slug: str,
    instance_slug: str,
    session: Optional[AsyncSession] = None
) -> AgentInstance:
    """
    Load agent instance from database and config files.
    
    This function:
    1. Validates instance exists in database and is active
    2. Loads configuration from file system
    3. Updates last_used_at timestamp
    4. Returns AgentInstance with all metadata + config
    
    Args:
        account_slug: Account identifier (e.g., 'default_account', 'acme')
        instance_slug: Instance identifier (e.g., 'simple_chat1', 'acme_chat1')
        session: Optional AsyncSession (will create if not provided)
    
    Returns:
        AgentInstance with database metadata + loaded config
    
    Raises:
        ValueError: If account/instance doesn't exist or instance is inactive
        FileNotFoundError: If config file is missing
        yaml.YAMLError: If config file is invalid YAML
    
    Example:
        instance = await load_agent_instance('default_account', 'simple_chat1')
        print(f"Loaded: {instance.display_name}")
        print(f"Model: {instance.config['model_settings']['model']}")
    """
    logger.info(
        f"Loading agent instance: account={account_slug}, instance={instance_slug}"
    )
    
    # Get or create session
    session_provided = session is not None
    if not session_provided:
        session = await anext(get_db_session())
    
    try:
        # Step 1: Query database for instance metadata
        from ..models.agent_instance import AgentInstanceModel
        from ..models.account import Account
        
        query = (
            select(AgentInstanceModel, Account)
            .join(Account, AgentInstanceModel.account_id == Account.id)
            .where(Account.slug == account_slug)
            .where(AgentInstanceModel.instance_slug == instance_slug)
        )
        
        result = await session.execute(query)
        row = result.first()
        
        if not row:
            logger.error(
                f"Agent instance not found: account={account_slug}, instance={instance_slug}"
            )
            raise ValueError(
                f"Agent instance not found: {account_slug}/{instance_slug}"
            )
        
        instance_model, account_model = row
        
        # Step 2: Validate instance is active
        if instance_model.status != 'active':
            logger.error(
                f"Agent instance is not active: {account_slug}/{instance_slug} "
                f"(status={instance_model.status})"
            )
            raise ValueError(
                f"Agent instance is not active: {account_slug}/{instance_slug} "
                f"(status={instance_model.status})"
            )
        
        logger.debug(
            f"Found active instance: id={instance_model.id}, "
            f"type={instance_model.agent_type}, "
            f"display_name={instance_model.display_name}"
        )
        
        # Step 3: Load config file
        config_path = _get_config_path(account_slug, instance_slug)
        logger.debug(f"Loading config from: {config_path}")
        
        if not config_path.exists():
            logger.error(f"Config file not found: {config_path}")
            raise FileNotFoundError(
                f"Config file not found: {config_path}"
            )
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config file {config_path}: {e}")
            raise
        
        logger.debug(f"Config loaded successfully from {config_path}")
        
        # Step 4: Load system prompt if exists
        system_prompt = None
        system_prompt_path = config_path.parent / "system_prompt.md"
        if system_prompt_path.exists():
            logger.debug(f"Loading system prompt from: {system_prompt_path}")
            with open(system_prompt_path, 'r') as f:
                system_prompt = f.read()
        
        # Step 5: Update last_used_at timestamp
        update_stmt = (
            update(AgentInstanceModel)
            .where(AgentInstanceModel.id == instance_model.id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await session.execute(update_stmt)
        await session.commit()
        
        logger.info(
            f"Successfully loaded instance: {account_slug}/{instance_slug} "
            f"(type={instance_model.agent_type}, id={instance_model.id})"
        )
        
        # Step 6: Return AgentInstance dataclass
        return AgentInstance(
            id=instance_model.id,
            account_id=instance_model.account_id,
            account_slug=account_slug,
            instance_slug=instance_slug,
            agent_type=instance_model.agent_type,
            display_name=instance_model.display_name,
            status=instance_model.status,
            last_used_at=datetime.now(timezone.utc),
            config=config,
            system_prompt=system_prompt
        )
    
    finally:
        # Only close session if we created it
        if not session_provided:
            await session.close()


def _get_config_path(account_slug: str, instance_slug: str) -> Path:
    """
    Get path to agent instance config file.
    
    Reads configs_directory from app.yaml and constructs full path.
    
    Args:
        account_slug: Account identifier
        instance_slug: Instance identifier
    
    Returns:
        Path to config.yaml file
    
    Example:
        path = _get_config_path('default_account', 'simple_chat1')
        # Returns: Path('backend/config/agent_configs/default_account/simple_chat1/config.yaml')
    """
    from ..config import load_config
    
    # Get configs directory from app.yaml
    app_config = load_config()
    configs_dir = app_config.get("agents", {}).get("configs_directory", "config/agent_configs")
    
    # Construct full path
    # If configs_dir is relative, it's relative to backend/ directory
    if not Path(configs_dir).is_absolute():
        # Get backend directory (parent of app/)
        backend_dir = Path(__file__).parent.parent.parent
        configs_dir = backend_dir / configs_dir
    else:
        configs_dir = Path(configs_dir)
    
    config_path = configs_dir / account_slug / instance_slug / "config.yaml"
    
    return config_path
