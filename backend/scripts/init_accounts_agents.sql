-- Copyright (c) 2025 Ape4, Inc. All rights reserved.
-- Unauthorized copying of this file is strictly prohibited.

-- ============================================================================
-- Initialize Accounts and Agent Instances
-- ============================================================================
-- Idempotent script to seed foundational multi-tenant data.
-- Safe to run multiple times (uses ON CONFLICT DO NOTHING).
--
-- Usage:
--   psql $DATABASE_URL -f backend/scripts/init_accounts_agents.sql
--
-- or from Python:
--   python -c "import asyncio; from app.database import get_database_service; \
--              asyncio.run(get_database_service().execute_sql_file('backend/scripts/init_accounts_agents.sql'))"
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- ACCOUNTS
-- ----------------------------------------------------------------------------
-- Insert foundational accounts for multi-tenant architecture
-- UUIDs match existing production data for consistency

INSERT INTO accounts (id, slug, name, created_at, updated_at) VALUES
    ('b401b3bb-c006-463a-98d3-b06527bb47c9', 'default_account', 'Default Account', NOW(), NOW()),
    ('a9f448d7-be82-4923-950d-0e393316f7a6', 'acme', 'Acme Corporation', NOW(), NOW()),
    ('1f9f3810-3da7-46fc-a7bb-f83d743a4584', 'agrofresh', 'AgroFresh Solutions', NOW(), NOW()),
    ('481d3e72-c0f5-47dd-8d6e-291c5a44a5c7', 'wyckoff', 'Wyckoff Hospital', NOW(), NOW()),
    ('6af9bba6-4623-4005-8ec5-33e04af8a63a', 'prepexcellence', 'PrepExcellence', NOW(), NOW()),
    ('7c2a8d4e-9f1b-4a5c-8d3e-2f6b7c8d9e0a', 'windriver', 'Windriver Hospital', NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

-- ----------------------------------------------------------------------------
-- AGENT INSTANCES
-- ----------------------------------------------------------------------------
-- Insert agent instances linked to accounts
-- Each instance must have corresponding config files at:
--   backend/config/agent_configs/{account_slug}/{instance_slug}/config.yaml
--   backend/config/agent_configs/{account_slug}/{instance_slug}/system_prompt.md

INSERT INTO agent_instances (id, account_id, instance_slug, agent_type, display_name, created_at, updated_at) VALUES
    -- Default Account Agents
    ('e0a59657-6514-4989-a08e-c191c77e4659', 
     'b401b3bb-c006-463a-98d3-b06527bb47c9', 
     'simple_chat1', 
     'simple_chat', 
     'Simple Chat 1', 
     NOW(), NOW()),
    
    ('28d891db-23b7-43c1-aa48-6d6ae286bd04', 
     'b401b3bb-c006-463a-98d3-b06527bb47c9', 
     'simple_chat2', 
     'simple_chat', 
     'Simple Chat 2', 
     NOW(), NOW()),
    
    -- Acme Corporation
    ('6a3f8c71-6efa-4368-95e0-174c7109725d', 
     'a9f448d7-be82-4923-950d-0e393316f7a6', 
     'acme_chat1', 
     'simple_chat', 
     'Acme Chat 1', 
     NOW(), NOW()),
    
    -- AgroFresh Solutions
    ('ecbceba4-39c6-4464-90d3-eedf27ddb1e6', 
     '1f9f3810-3da7-46fc-a7bb-f83d743a4584', 
     'agro_info_chat1', 
     'simple_chat', 
     'AgroFresh Assistant', 
     NOW(), NOW()),
    
    -- Wyckoff Hospital
    ('5dc7a769-bb5e-485b-9f19-093b95dd404d', 
     '481d3e72-c0f5-47dd-8d6e-291c5a44a5c7', 
     'wyckoff_info_chat1', 
     'simple_chat', 
     'Wyckoff Hospital Assistant', 
     NOW(), NOW()),
    
    -- PrepExcellence
    ('4c28d9b7-45e0-45ee-9232-88ab173dea9c', 
     '6af9bba6-4623-4005-8ec5-33e04af8a63a', 
     'prepexcel_info_chat1', 
     'simple_chat', 
     'PrepExcellence Assistant', 
     NOW(), NOW()),
    
    -- Windriver Hospital
    ('8d3e9f2a-1b4c-5d6e-7f8a-9b0c1d2e3f4a', 
     '7c2a8d4e-9f1b-4a5c-8d3e-2f6b7c8d9e0a', 
     'windriver_info_chat1', 
     'simple_chat', 
     'Windriver Hospital Assistant', 
     NOW(), NOW())
ON CONFLICT (account_id, instance_slug) DO NOTHING;

COMMIT;

-- ============================================================================
-- Summary
-- ============================================================================
-- Accounts:     6 (default_account, acme, agrofresh, wyckoff, prepexcellence, windriver)
-- Agents:       7 (2 default, 1 acme, 1 agrofresh, 1 wyckoff, 1 prepexcellence, 1 windriver)
-- 
-- Next steps:
-- 1. Verify config files exist for each agent instance
-- 2. Run seed_directory.py to populate directory data (doctors, products, etc.)
-- 3. Test agent endpoints: GET /accounts/{account}/agents
-- ============================================================================

