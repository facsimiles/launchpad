SET client_min_messages=ERROR;

-- Store the row index of bug messages so we don't have to calculate it all the time.
ALTER TABLE BugMessage ADD COLUMN index integer;

-- BugMessage.indexes must be unique per bug (index can be added post-rollout
-- if its slow).
CREATE UNIQUE INDEX bugmessage__bug_index_unique ON BugMessage (bug, index);


INSERT INTO LaunchpadDatabaseRevision VALUES (2208, 99, 0);
