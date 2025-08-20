-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

CREATE TABLE VulnerabilityJob (
    id serial PRIMARY KEY,
    job integer NOT NULL REFERENCES job,
    handler integer NOT NULL,
    job_type integer NOT NULL,
    json_data jsonb
);

ALTER TABLE VulnerabilityJob ADD CONSTRAINT vulnerabilityjob__job__key UNIQUE (job);
CREATE INDEX vulnerabilityjob__handler__idx ON VulnerabilityJob USING btree (handler);
CREATE INDEX vulnerabilityjob__job_type__idx ON VulnerabilityJob USING btree (job_type);

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 45, 0);
