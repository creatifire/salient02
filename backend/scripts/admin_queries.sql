-- ============================================================================
-- Epic 0022 - Multi-Tenant Architecture Admin Queries
-- ============================================================================
-- Quick reference queries for manual testing and debugging during Epic 0022
-- Phase 1a implementation. Copy/paste into Adminer or psql.
--
-- Usage: Replace placeholder values (e.g., 'acme', 'simple-chat-support')
--        with actual slugs from your database.
-- ============================================================================

-- ============================================================================
-- SECTION 1: ACCOUNTS OVERVIEW
-- ============================================================================

-- List all accounts with instance and session counts
SELECT 
    a.slug,
    a.name,
    a.subscription_tier,
    a.status,
    COUNT(DISTINCT ai.id) as instance_count,
    COUNT(DISTINCT s.id) as session_count,
    a.created_at
FROM accounts a
LEFT JOIN agent_instances ai ON ai.account_id = a.id
LEFT JOIN sessions s ON s.account_id = a.id
GROUP BY a.id, a.slug, a.name, a.subscription_tier, a.status, a.created_at
ORDER BY a.created_at DESC;

-- Show account with cost summary
SELECT 
    a.slug,
    a.name,
    COUNT(DISTINCT ai.id) as instance_count,
    COUNT(DISTINCT s.id) as session_count,
    COUNT(lr.id) as llm_request_count,
    COALESCE(SUM(lr.computed_cost), 0) as total_cost
FROM accounts a
LEFT JOIN agent_instances ai ON ai.account_id = a.id
LEFT JOIN sessions s ON s.account_id = a.id
LEFT JOIN llm_requests lr ON lr.account_id = a.id
GROUP BY a.id, a.slug, a.name
ORDER BY total_cost DESC;

-- ============================================================================
-- SECTION 2: AGENT INSTANCES
-- ============================================================================

-- List all agent instances across all accounts
SELECT 
    a.slug as account,
    ai.instance_slug,
    ai.agent_type,
    ai.display_name,
    ai.status,
    COUNT(DISTINCT s.id) as session_count,
    COUNT(DISTINCT m.id) as message_count,
    ai.last_used_at,
    ai.created_at
FROM agent_instances ai
JOIN accounts a ON ai.account_id = a.id
LEFT JOIN sessions s ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.agent_instance_id = ai.id
GROUP BY ai.id, a.slug, ai.instance_slug, ai.agent_type, ai.display_name, 
         ai.status, ai.last_used_at, ai.created_at
ORDER BY a.slug, ai.instance_slug;

-- Agent instances for a specific account (replace 'acme')
SELECT 
    ai.instance_slug,
    ai.agent_type,
    ai.display_name,
    ai.status,
    COUNT(DISTINCT s.id) as session_count,
    COUNT(DISTINCT m.id) as message_count,
    COALESCE(SUM(lr.computed_cost), 0) as total_cost,
    ai.last_used_at
FROM agent_instances ai
JOIN accounts a ON ai.account_id = a.id
LEFT JOIN sessions s ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.agent_instance_id = ai.id
LEFT JOIN llm_requests lr ON lr.agent_instance_id = ai.id
WHERE a.slug = 'default'  -- REPLACE WITH YOUR ACCOUNT SLUG
GROUP BY ai.id, ai.instance_slug, ai.agent_type, ai.display_name, 
         ai.status, ai.last_used_at
ORDER BY ai.instance_slug;

-- Most active agent instances (by message count)
SELECT 
    a.slug as account,
    ai.instance_slug,
    ai.agent_type,
    COUNT(m.id) as message_count,
    ai.last_used_at
FROM agent_instances ai
JOIN accounts a ON ai.account_id = a.id
LEFT JOIN messages m ON m.agent_instance_id = ai.id
GROUP BY ai.id, a.slug, ai.instance_slug, ai.agent_type, ai.last_used_at
ORDER BY message_count DESC
LIMIT 10;

-- ============================================================================
-- SECTION 3: SESSIONS
-- ============================================================================

-- Recent sessions with account and instance details
SELECT 
    s.session_key,
    a.slug as account,
    ai.instance_slug as agent_instance,
    s.user_id,
    s.is_anonymous,
    s.email,
    COUNT(m.id) as message_count,
    s.last_activity_at,
    s.created_at
FROM sessions s
JOIN accounts a ON s.account_id = a.id
LEFT JOIN agent_instances ai ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.session_id = s.id
GROUP BY s.id, s.session_key, a.slug, ai.instance_slug, s.user_id,
         s.is_anonymous, s.email, s.last_activity_at, s.created_at
ORDER BY s.last_activity_at DESC
LIMIT 20;

-- Sessions for a specific account (replace 'acme')
SELECT 
    s.session_key,
    ai.instance_slug,
    COUNT(m.id) as message_count,
    s.is_anonymous,
    s.email,
    s.last_activity_at
FROM sessions s
JOIN accounts a ON s.account_id = a.id
LEFT JOIN agent_instances ai ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.session_id = s.id
WHERE a.slug = 'default'  -- REPLACE WITH YOUR ACCOUNT SLUG
GROUP BY s.id, s.session_key, ai.instance_slug, s.is_anonymous, 
         s.email, s.last_activity_at
ORDER BY s.last_activity_at DESC;

-- Active sessions (activity in last hour)
SELECT 
    a.slug as account,
    ai.instance_slug,
    s.session_key,
    s.last_activity_at,
    COUNT(m.id) as message_count
FROM sessions s
JOIN accounts a ON s.account_id = a.id
LEFT JOIN agent_instances ai ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.session_id = s.id
WHERE s.last_activity_at > NOW() - INTERVAL '1 hour'
GROUP BY s.id, a.slug, ai.instance_slug, s.session_key, s.last_activity_at
ORDER BY s.last_activity_at DESC;

-- ============================================================================
-- SECTION 4: MESSAGES & CONVERSATIONS
-- ============================================================================

-- Recent messages with context (account, instance, session)
SELECT 
    a.slug as account,
    ai.instance_slug as agent,
    s.session_key,
    m.role,
    LEFT(m.content, 100) as content_preview,
    m.created_at
FROM messages m
JOIN sessions s ON m.session_id = s.id
JOIN accounts a ON s.account_id = a.id
LEFT JOIN agent_instances ai ON m.agent_instance_id = ai.id
ORDER BY m.created_at DESC
LIMIT 50;

-- Conversation history for a specific session (replace session_key)
SELECT 
    m.role,
    m.content,
    m.metadata,
    m.created_at
FROM messages m
JOIN sessions s ON m.session_id = s.id
WHERE s.session_key = 'YOUR_SESSION_KEY_HERE'  -- REPLACE
ORDER BY m.created_at ASC;

-- Messages by agent instance
SELECT 
    a.slug as account,
    ai.instance_slug,
    m.role,
    COUNT(*) as count
FROM messages m
JOIN agent_instances ai ON m.agent_instance_id = ai.id
JOIN accounts a ON ai.account_id = a.id
GROUP BY a.slug, ai.instance_slug, m.role
ORDER BY a.slug, ai.instance_slug, m.role;

-- ============================================================================
-- SECTION 5: LLM COST TRACKING
-- ============================================================================

-- Cost summary by account
SELECT 
    a.slug as account,
    COUNT(*) as request_count,
    SUM(lr.prompt_tokens) as total_prompt_tokens,
    SUM(lr.completion_tokens) as total_completion_tokens,
    SUM(lr.total_tokens) as total_tokens,
    SUM(lr.computed_cost) as total_cost,
    AVG(lr.latency_ms) as avg_latency_ms
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
GROUP BY a.slug
ORDER BY total_cost DESC;

-- Cost breakdown by account and agent instance
SELECT 
    a.slug as account,
    ai.instance_slug,
    lr.agent_type,
    lr.model,
    COUNT(*) as request_count,
    SUM(lr.total_tokens) as total_tokens,
    SUM(lr.computed_cost) as total_cost
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
GROUP BY a.slug, ai.instance_slug, lr.agent_type, lr.model
ORDER BY total_cost DESC;

-- Recent LLM requests with full context
SELECT 
    a.slug as account,
    ai.instance_slug as agent,
    s.session_key,
    lr.model,
    lr.completion_status,
    lr.prompt_tokens,
    lr.completion_tokens,
    lr.computed_cost,
    lr.latency_ms,
    lr.created_at
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
JOIN sessions s ON lr.session_id = s.id
ORDER BY lr.created_at DESC
LIMIT 20;

-- LLM requests for specific account/instance (replace slugs)
SELECT 
    s.session_key,
    lr.model,
    lr.completion_status,
    lr.prompt_tokens,
    lr.completion_tokens,
    lr.computed_cost,
    lr.latency_ms,
    lr.created_at
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
JOIN sessions s ON lr.session_id = s.id
WHERE a.slug = 'default'  -- REPLACE
  AND ai.instance_slug = 'simple-chat'  -- REPLACE
ORDER BY lr.created_at DESC
LIMIT 20;

-- Failed/partial LLM requests (for debugging)
SELECT 
    a.slug as account,
    ai.instance_slug,
    lr.completion_status,
    lr.model,
    lr.latency_ms,
    lr.created_at
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
WHERE lr.completion_status IN ('partial', 'error')
ORDER BY lr.created_at DESC;

-- Model usage and cost comparison
SELECT 
    lr.model,
    COUNT(*) as request_count,
    SUM(lr.total_tokens) as total_tokens,
    SUM(lr.computed_cost) as total_cost,
    AVG(lr.latency_ms) as avg_latency_ms,
    AVG(lr.computed_cost) as avg_cost_per_request
FROM llm_requests lr
GROUP BY lr.model
ORDER BY total_cost DESC;

-- ============================================================================
-- SECTION 6: DATA INTEGRITY & VALIDATION
-- ============================================================================

-- Check for orphaned sessions (missing account_id - should be none after migration)
SELECT COUNT(*) as orphaned_sessions
FROM sessions 
WHERE account_id IS NULL;

-- Check for messages without agent_instance_id (should be none after Phase 1a)
SELECT COUNT(*) as messages_without_instance
FROM messages 
WHERE agent_instance_id IS NULL;

-- Check for llm_requests without account attribution (should be none)
SELECT COUNT(*) as llm_requests_without_account
FROM llm_requests 
WHERE account_id IS NULL OR agent_instance_id IS NULL;

-- Verify denormalized columns match FKs (account_slug should match account.slug)
SELECT 
    COUNT(*) as mismatched_account_slugs
FROM sessions s
JOIN accounts a ON s.account_id = a.id
WHERE s.account_slug != a.slug;

-- Verify denormalized columns match FKs (agent_instance_slug)
SELECT 
    COUNT(*) as mismatched_instance_slugs
FROM llm_requests lr
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
WHERE lr.agent_instance_slug != ai.instance_slug;

-- Check all accounts have at least one agent instance
SELECT 
    a.slug,
    a.name,
    COUNT(ai.id) as instance_count
FROM accounts a
LEFT JOIN agent_instances ai ON ai.account_id = a.id
GROUP BY a.id, a.slug, a.name
HAVING COUNT(ai.id) = 0;

-- ============================================================================
-- SECTION 7: COMPLETE DATA DRILL-DOWN (FOR SPECIFIC ACCOUNT)
-- ============================================================================

-- Full account hierarchy (replace 'acme' with your account slug)
-- Copy and run this to see complete data for one account
WITH target_account AS (
    SELECT id, slug, name FROM accounts WHERE slug = 'default'  -- REPLACE
)
SELECT 
    'Account' as entity_type,
    ta.slug as identifier,
    ta.name as description,
    NULL as count_value,
    NULL as created_at
FROM target_account ta

UNION ALL

SELECT 
    'Agent Instance',
    ai.instance_slug,
    ai.agent_type || ' - ' || ai.display_name,
    NULL,
    ai.created_at
FROM agent_instances ai
JOIN target_account ta ON ai.account_id = ta.id

UNION ALL

SELECT 
    'Session',
    s.session_key,
    'Messages: ' || COUNT(DISTINCT m.id)::text,
    COUNT(DISTINCT m.id),
    s.created_at
FROM sessions s
JOIN target_account ta ON s.account_id = ta.id
LEFT JOIN messages m ON m.session_id = s.id
GROUP BY s.id, s.session_key, s.created_at

ORDER BY entity_type, created_at DESC;

-- ============================================================================
-- SECTION 8: PHASE 1B - AUTHENTICATION & AUTHORIZATION (FOR FUTURE USE)
-- ============================================================================
-- Uncomment these queries when Phase 1b (users, roles, user_roles) is implemented

-- -- List users with their account roles
-- SELECT 
--     u.email,
--     u.full_name,
--     a.slug as account,
--     r.name as role,
--     ur.created_at as granted_at
-- FROM user_roles ur
-- JOIN users u ON ur.user_id = u.id
-- JOIN accounts a ON ur.account_id = a.id
-- JOIN roles r ON ur.role_id = r.id
-- ORDER BY u.email, a.slug;

-- -- Users in a specific account (replace 'acme')
-- SELECT 
--     u.email,
--     u.full_name,
--     r.name as role,
--     r.permissions
-- FROM user_roles ur
-- JOIN users u ON ur.user_id = u.id
-- JOIN accounts a ON ur.account_id = a.id
-- JOIN roles r ON ur.role_id = r.id
-- WHERE a.slug = 'acme'  -- REPLACE
-- ORDER BY r.name, u.email;

-- -- User permissions across all accounts
-- SELECT 
--     u.email,
--     a.slug as account,
--     r.name as role,
--     r.permissions
-- FROM user_roles ur
-- JOIN users u ON ur.user_id = u.id
-- JOIN accounts a ON ur.account_id = a.id
-- JOIN roles r ON ur.role_id = r.id
-- WHERE u.email = 'user@example.com'  -- REPLACE
-- ORDER BY a.slug;

-- ============================================================================
-- SECTION 9: PERFORMANCE & OPTIMIZATION QUERIES
-- ============================================================================

-- Most expensive sessions (by LLM cost)
SELECT 
    s.session_key,
    a.slug as account,
    ai.instance_slug,
    COUNT(lr.id) as request_count,
    SUM(lr.computed_cost) as total_cost,
    SUM(lr.total_tokens) as total_tokens
FROM sessions s
JOIN accounts a ON s.account_id = a.id
LEFT JOIN agent_instances ai ON s.agent_instance_id = ai.id
LEFT JOIN llm_requests lr ON lr.session_id = s.id
GROUP BY s.id, s.session_key, a.slug, ai.instance_slug
ORDER BY total_cost DESC
LIMIT 20;

-- Slowest LLM requests (for performance monitoring)
SELECT 
    a.slug as account,
    ai.instance_slug,
    lr.model,
    lr.latency_ms,
    lr.total_tokens,
    lr.created_at
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
ORDER BY lr.latency_ms DESC
LIMIT 20;

-- Agent instance usage over time (last 7 days)
SELECT 
    DATE(lr.created_at) as date,
    a.slug as account,
    ai.instance_slug,
    COUNT(*) as request_count,
    SUM(lr.computed_cost) as daily_cost
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
JOIN agent_instances ai ON lr.agent_instance_id = ai.id
WHERE lr.created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(lr.created_at), a.slug, ai.instance_slug
ORDER BY date DESC, daily_cost DESC;

-- ============================================================================
-- SECTION 10: QUICK LOOKUPS (MOST COMMONLY USED)
-- ============================================================================

-- Quick: Show me everything for the default account
SELECT 'Use this as starting point' as note;

-- Quick: List all my agent instances
SELECT a.slug, ai.instance_slug, ai.agent_type, ai.status
FROM agent_instances ai
JOIN accounts a ON ai.account_id = a.id
ORDER BY a.slug, ai.instance_slug;

-- Quick: Show recent activity
SELECT 
    s.last_activity_at,
    a.slug as account,
    ai.instance_slug,
    COUNT(m.id) as messages
FROM sessions s
JOIN accounts a ON s.account_id = a.id
LEFT JOIN agent_instances ai ON s.agent_instance_id = ai.id
LEFT JOIN messages m ON m.session_id = s.id
WHERE s.last_activity_at > NOW() - INTERVAL '1 hour'
GROUP BY s.id, s.last_activity_at, a.slug, ai.instance_slug
ORDER BY s.last_activity_at DESC;

-- Quick: Total costs today
SELECT 
    a.slug as account,
    COUNT(*) as requests,
    SUM(lr.computed_cost) as cost_today
FROM llm_requests lr
JOIN accounts a ON lr.account_id = a.id
WHERE DATE(lr.created_at) = CURRENT_DATE
GROUP BY a.slug
ORDER BY cost_today DESC;

-- ============================================================================
-- END OF ADMIN QUERIES
-- ============================================================================

