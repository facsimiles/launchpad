
SET client_min_messages=ERROR;

ALTER TABLE branch ADD COLUMN mirror_request_time TIMESTAMP WITHOUT TIME ZONE;

INSERT INTO LaunchpadDatabaseRevision VALUES (67, 99, 0);
