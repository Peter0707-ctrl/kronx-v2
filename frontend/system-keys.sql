-- ==============================================================================
-- KRONX / COPETRA MACHINE-TO-MACHINE (SYSTEM) CREDENTIALS
-- Database Migration & Direct Insert Script
-- Generated: 2026-10-07
-- ==============================================================================

-- 1. Ensure the system_api_keys table and index exist
CREATE TABLE IF NOT EXISTS system_api_keys (
  id VARCHAR(255) PRIMARY KEY,
  system_name VARCHAR(255) NOT NULL,
  api_key VARCHAR(255) UNIQUE NOT NULL,
  api_secret_hash VARCHAR(255) NOT NULL,
  secret_prefix VARCHAR(32) NOT NULL,
  permissions JSONB DEFAULT '["*"]'::jsonb,
  rate_limit_rpm INTEGER DEFAULT 120,
  is_active BOOLEAN DEFAULT TRUE,
  last_used_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_api_keys_api_key ON system_api_keys(api_key);

-- 2. Insert Generated System Credentials (SHA-256 hashed secrets)

-- (1) Backend FastAPI & Core Services
INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, rate_limit_rpm, is_active)
VALUES (
  'sys_754df122-aa28-45c9-8816-3835d0f4bb27',
  'Backend FastAPI & Core Services',
  'cpk_sys_dcf0db22cc53ff48312ff092a78947bf2ad0658f',
  '13a98f9b6e443c85cfbb1403c17f9cafaf519239b07925443ca7df7eafc777ea',
  'cps_sec_3e8e',
  '["*"]'::jsonb,
  300,
  TRUE
)
ON CONFLICT (api_key) DO UPDATE SET is_active = TRUE;

-- (2) Payment & Billing Webhook Service
INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, rate_limit_rpm, is_active)
VALUES (
  'sys_9db41fec-52a7-4cac-b871-5e15cf1257e5',
  'Payment & Billing Webhook Service',
  'cpk_sys_039b1dce21defcfa328f3a5591f72e6eee6f41ac',
  '547c7dfa64c597c05b4ce86d697603d7e457f5148aaf25c50cbb1c5729a36198',
  'cps_sec_8ba9',
  '["billing.*", "webhooks.*"]'::jsonb,
  120,
  TRUE
)
ON CONFLICT (api_key) DO UPDATE SET is_active = TRUE;

-- (3) ERP & CRM Integration Engine
INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, rate_limit_rpm, is_active)
VALUES (
  'sys_039b1c34-5e6c-4bc3-93f8-adc94da243ab',
  'ERP & CRM Integration Engine',
  'cpk_sys_87d0124cd8dd661673af10350d691c3c2b431b4c',
  'de6a3f44233cf8db3588b8ca2d9ba3ae74247743d344937a25dddd8f548af70e',
  'cps_sec_d7ee',
  '["erp.*", "sync.*"]'::jsonb,
  120,
  TRUE
)
ON CONFLICT (api_key) DO UPDATE SET is_active = TRUE;

-- (4) Background Automation & Cron Worker
INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, rate_limit_rpm, is_active)
VALUES (
  'sys_0c1719c0-fad4-4d50-afc9-fead5161a406',
  'Background Automation & Cron Worker',
  'cpk_sys_dc663b7e2fa163b076c946c53890da32291214a9',
  '5f0c0149ea890127509198cff7ab98296f315bd83e6fd4f8e93141e5e3808d72',
  'cps_sec_f461',
  '["cron.*", "tasks.*"]'::jsonb,
  200,
  TRUE
)
ON CONFLICT (api_key) DO UPDATE SET is_active = TRUE;

-- (5) External Bots & AI Integrations
INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, rate_limit_rpm, is_active)
VALUES (
  'sys_220cd658-9b27-4f71-9f26-f1444212567f',
  'External Bots & AI Integrations',
  'cpk_sys_20841b4150051e8cf866e8bdda7a430013e6a831',
  'b556a456ea3b55dc30d59f1cfe07b88a97d96c2399bca97544c86d870e10553f',
  'cps_sec_3f74',
  '["chat.*", "bot.*"]'::jsonb,
  120,
  TRUE
)
ON CONFLICT (api_key) DO UPDATE SET is_active = TRUE;

-- (6) Mobile & Third-Party Client Gateway
INSERT INTO system_api_keys (id, system_name, api_key, api_secret_hash, secret_prefix, permissions, rate_limit_rpm, is_active)
VALUES (
  'sys_a60d847d-0c56-4343-a71a-d4e5d6487939',
  'Mobile & Third-Party Client Gateway',
  'cpk_sys_f06a1cfe3fe52e8ba888a7c927d11572711f15c7',
  '7d0df86302889877ec942029b3433fbc36c0e9e9203150c6fc6607b9193ab005',
  'cps_sec_4e91',
  '["client.*", "mobile.*"]'::jsonb,
  120,
  TRUE
)
ON CONFLICT (api_key) DO UPDATE SET is_active = TRUE;

-- Verify inserted credentials
SELECT id, system_name, api_key, secret_prefix, is_active, created_at FROM system_api_keys;
