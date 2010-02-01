SET client_min_messages=ERROR;

CREATE TABLE ApportJob(
    id serial NOT NULL PRIMARY KEY,
    job integer NOT NULL REFERENCES Job(id),
    blob integer NOT NULL REFERENCES TemporaryBlobStorage(id),
    job_type integer NOT NULL,
    json_data text
);

INSERT INTO LaunchpadDatabaseRevision VALUES (2207, 99, 0)
