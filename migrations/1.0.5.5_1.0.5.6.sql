BEGIN TRANSACTION;

-- Per-query Signal recipients: semicolon-separated phone numbers. When empty,
-- the query falls back to the global default recipient(s).
ALTER TABLE queries ADD COLUMN signal_recipients TEXT;

-- Named Signal contacts (JSON array of {"name","number"}) used to build the
-- per-query recipient checkboxes, plus a Signal-specific message template.
INSERT OR IGNORE INTO parameters (key, value) VALUES
    ('signal_contacts', '[]'),
    ('signal_message_template', '🆕 {title}
💶 Price: {price}
🏷️ Brand: {brand}
📏 Size: {size}
🔗 {url}');

UPDATE parameters SET value = '1.0.5.6' WHERE key = 'version';

COMMIT;
