-- Migration: Remove DB Preisagent (Deutsche Bahn price agent) feature
-- Date: 2026-08-21
-- Description: Drops the three price-agent tables and removes the single
--              `feature:db_agent:view` permission. The feature was an
--              admin-only alpha tile that scraped bahn.de for one hardcoded
--              route (Dortmund Hbf <-> Nuernberg Hbf); nothing else in LLARS
--              referenced these tables, so no data has to be migrated.

-- ---------------------------------------------------------------------------
-- 1. Price agent tables
--    Entries first: db_price_entries.scan_id has an FK on db_price_scans.id,
--    so dropping the parent first would fail on engines that enforce the
--    constraint. db_trip_searches has no FKs and can go last.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS db_price_entries;
DROP TABLE IF EXISTS db_price_scans;
DROP TABLE IF EXISTS db_trip_searches;

-- ---------------------------------------------------------------------------
-- 2. Price agent permission
--    role_permissions / user_permissions reference permissions.id with
--    ON DELETE CASCADE, but the joins are spelled out explicitly so the cleanup
--    also works on databases where the FKs were never created.
--    permission_audit_log keeps its rows: it stores permission_key as plain
--    text and is a historical record.
-- ---------------------------------------------------------------------------
DELETE rp FROM role_permissions rp
    JOIN permissions p ON p.id = rp.permission_id
    WHERE p.permission_key = 'feature:db_agent:view';

DELETE up FROM user_permissions up
    JOIN permissions p ON p.id = up.permission_id
    WHERE p.permission_key = 'feature:db_agent:view';

DELETE FROM permissions WHERE permission_key = 'feature:db_agent:view';
