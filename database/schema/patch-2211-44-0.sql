-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

ALTER TABLE distroarchseries
    ADD COLUMN underlying_architecturetag text;

CREATE INDEX distroarchseries__distroseries__underlying_architecturetag__idx
    ON distroarchseries (distroseries, underlying_architecturetag);

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 44, 0);
