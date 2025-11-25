-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

CREATE TABLE PublisherRun(
    id serial PRIMARY KEY,
    date_started timestamp without time zone NOT NULL,
    date_finished timestamp without time zone NOT NULL
);

CREATE INDEX publisherrun__date_started__idx ON PublisherRun
  USING btree (date_started);
CREATE INDEX publisherrun__date_finished__idx ON PublisherRun
  USING btree (date_finished);

COMMENT ON COLUMN PublisherRun.date_started IS
  'Start timestamp for the publisher run.';
COMMENT ON COLUMN PublisherRun.date_finished IS
  'End timestamp for the publisher run.';

CREATE TABLE PublishingHistory(
    id serial PRIMARY KEY,
    archive integer NOT NULL REFERENCES archive,
    publisher_run integer NOT NULL REFERENCES PublisherRun
);

CREATE INDEX publishinghistory__archive__idx ON PublishingHistory
  USING btree (archive);
CREATE INDEX publishinghistory__publisher_run__idx ON PublishingHistory
  USING btree (publisher_run);

COMMENT ON COLUMN PublishingHistory.archive IS
  'Archive id that was published.';
COMMENT ON COLUMN PublishingHistory.publisher_run IS
  'Publisher run during which the archive was published.';

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 49, 0);
