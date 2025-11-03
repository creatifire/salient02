-- Copyright (c) 2025 Ape4, Inc. All rights reserved.
-- Unauthorized copying of this file is strictly prohibited.

-- Setup PrepExcellence Account and Agent Instance
-- This script creates the database records needed for the PrepExcellence demo site

-- Create prepexcellence account
INSERT INTO accounts (slug, name, description, status, created_at, updated_at)
VALUES (
    'prepexcellence',
    'PrepExcellence',
    'SAT, ACT, and PSAT test preparation services with Dr. Kaisar Alam',
    'active',
    NOW(),
    NOW()
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Create prepexcel_info_chat1 agent instance
INSERT INTO agent_instances (
    account_id,
    instance_slug,
    agent_type,
    display_name,
    description,
    status,
    created_at,
    updated_at
)
VALUES (
    (SELECT id FROM accounts WHERE slug = 'prepexcellence'),
    'prepexcel_info_chat1',
    'simple_chat',
    'PrepExcellence Assistant',
    'Test preparation and college admissions assistant for PrepExcellence',
    'active',
    NOW(),
    NOW()
)
ON CONFLICT (account_id, instance_slug) DO UPDATE SET
    agent_type = EXCLUDED.agent_type,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Verify the records were created
SELECT 
    a.slug as account_slug,
    a.name as account_name,
    ai.instance_slug,
    ai.display_name,
    ai.agent_type,
    ai.status
FROM accounts a
JOIN agent_instances ai ON a.id = ai.account_id
WHERE a.slug = 'prepexcellence'
ORDER BY ai.created_at;

