BEGIN TRANSACTION;

-- Attach the item photo to Signal messages (downloaded and base64-encoded).
INSERT OR IGNORE INTO parameters (key, value)
VALUES ('signal_include_image', 'True');

UPDATE parameters SET value = '1.0.5.7' WHERE key = 'version';

COMMIT;
