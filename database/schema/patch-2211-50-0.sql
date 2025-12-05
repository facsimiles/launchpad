-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

CREATE TABLE CTDeliveryJob (
    id serial PRIMARY KEY,
    job integer NOT NULL REFERENCES job,
    job_type integer NOT NULL,
    publishing_history integer NOT NULL REFERENCES ArchivePublishingHistory,
    json_data jsonb
);

ALTER TABLE CTDeliveryJob ADD CONSTRAINT ctdeliveryjob__job__key UNIQUE (job);
CREATE INDEX ctdeliveryjob__job_type__idx ON CTDeliveryJob
  USING btree (job_type);
CREATE INDEX ctdeliveryjob__publishing_history__idx ON CTDeliveryJob
  USING btree (publishing_history);

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 50, 0);
