-- Copyright 2025 Canonical Ltd.  This software is licensed under the
-- GNU Affero General Public License version 3 (see the file LICENSE).

SET client_min_messages=ERROR;

-- StructuralSubscription
COMMENT ON COLUMN StructuralSubscription.product IS 'The subscription''s target, when it is a product.';
COMMENT ON COLUMN StructuralSubscription.productseries IS 'The subscription''s target, when it is a product series.';
COMMENT ON COLUMN StructuralSubscription.project IS 'The subscription''s target, when it is a project.';
COMMENT ON COLUMN StructuralSubscription.milestone IS 'The subscription''s target, when it is a milestone.';
COMMENT ON COLUMN StructuralSubscription.distribution IS 'The subscription''s target, when it is a distribution.';
COMMENT ON COLUMN StructuralSubscription.distroseries IS 'The subscription''s target, when it is a distribution series.';
COMMENT ON COLUMN StructuralSubscription.sourcepackagename IS 'The subscription''s target, when it is a source-package.';

INSERT INTO LaunchpadDatabaseRevision VALUES (2211, 46, 0);
