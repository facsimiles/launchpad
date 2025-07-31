-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

ALTER TABLE distroarchseries
    ADD COLUMN underlying_architecturetag text;

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 44, 0);
