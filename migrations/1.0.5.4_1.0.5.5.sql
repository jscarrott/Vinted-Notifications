BEGIN TRANSACTION;

INSERT OR IGNORE INTO parameters (key, value)
VALUES ('signal_enabled', 'False'),
       ('signal_api_url', ''),
       ('signal_phone', ''),
       ('signal_recipient', ''),
       ('signal_process_running', 'False');

UPDATE parameters
SET value = '1.0.5.5'
WHERE key = 'version';

COMMIT;
