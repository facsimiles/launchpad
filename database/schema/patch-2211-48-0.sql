-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR; 

ALTER TABLE Webhook ADD COLUMN archive integer REFERENCES archive; 

CREATE INDEX webhook__archive__id__idx 
    ON Webhook (archive, id) WHERE archive IS NOT NULL; 

ALTER TABLE Webhook DROP CONSTRAINT one_target; 
ALTER TABLE Webhook ADD CONSTRAINT one_target CHECK ( 
    (public.null_count(ARRAY[git_repository, branch, snap, livefs, oci_recipe, charm_recipe, rock_recipe, craft_recipe, project, distribution, archive]) = 10) AND 
    (source_package_name IS NULL OR distribution IS NOT NULL) 
); 

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 48, 0);
