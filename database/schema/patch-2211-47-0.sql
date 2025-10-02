-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

ALTER TABLE Cve
    ADD COLUMN metadata jsonb;
COMMENT ON COLUMN Cve.metadata
    IS 'CVE metadata.';

ALTER TABLE vulnerability
    ADD COLUMN metadata jsonb;
COMMENT ON COLUMN vulnerability.metadata
    IS 'Vulnerability metadata.';

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 47, 0);
