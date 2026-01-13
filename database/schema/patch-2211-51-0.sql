-- Copyright 2026 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

ALTER TABLE CTDeliveryJob ALTER COLUMN publishing_history DROP NOT NULL;

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 51, 0);
