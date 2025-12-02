-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

CREATE TABLE ArchivePublisherRun(
    id serial PRIMARY KEY,
    date_started timestamp without time zone NOT NULL,
    date_finished timestamp without time zone,
    status integer NOT NULL
);

CREATE INDEX archivepublisherrun__date_started__idx ON ArchivePublisherRun
  USING btree (date_started);
CREATE INDEX archivepublisherrun__date_finished__idx ON ArchivePublisherRun
  USING btree (date_finished);
CREATE INDEX archivepublisherrun__status__idx ON ArchivePublisherRun
 USING btree (status);

COMMENT ON COLUMN ArchivePublisherRun.date_started IS
  'Start timestamp for the publisher run.';
COMMENT ON COLUMN ArchivePublisherRun.date_finished IS
  'End timestamp for the publisher run.';
COMMENT ON COLUMN ArchivePublisherRun.status IS
  'Status of the publisher run.';

CREATE TABLE ArchivePublishingHistory(
    id serial PRIMARY KEY,
    archive integer NOT NULL REFERENCES archive,
    publisher_run integer NOT NULL REFERENCES ArchivePublisherRun
);

CREATE INDEX archivepublishinghistory__archive__idx ON ArchivePublishingHistory
  USING btree (archive);
CREATE INDEX archivepublishinghistory__publisher_run__idx ON ArchivePublishingHistory
  USING btree (publisher_run);

COMMENT ON COLUMN ArchivePublishingHistory.archive IS
  'Archive id that was published.';
COMMENT ON COLUMN ArchivePublishingHistory.publisher_run IS
  'Archive publisher run during which the archive was published.';

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 49, 0);
