--
-- This will DESTROY your database and create a fresh one
--

/*

  CONVENTIONS
        - all dates and timestamps MUST be in UTC
  TODO
        - re-evalutate some of the "text" field types, they might need
	  to be "bytea"
	  unless we can guarantee utf-8
	- make sure names are only [a-z][0-9][-.+] and can only start
	  with [a-z]
	- set DEFAULT's for datestamps (now) and others
	- create custom schema systems for components, etc.
        - add Series to products and projects
	- setup translatable package descriptions
	  - mirror recent changes to dia
  GROUCH
	- TranslationEffortPOTemplate.category must be from a
	  schema that matches TranslationEffort.categories
  CHANGES


  v0.99-dev:
        - add BugAttachmentContent.id for Stuart Bishop
	- and move the BugAttachment.name to BugAttachmentContent
        - make ProductRelease.version NOT NULL and add a .changelog
        - don't require homepageurl for Project or Product
        - add ChangesetFileHash.id for Robert Weir
        - rename UpstreamRelease to ProductRelease
        - rename BugExternalref -> BugExternalRef
        - add BugExternalRef.id
        - rename ProductBugsystem -> ProductBugSystem
        - add BugSubscription.id
        - add ProductBugAssignment.id, moving existing pk to unique constraint
        - add SourcepackageBugAssignment.id, and add unique constraint
	- add POMsgSet.flagscomment for Carlos
	- rename TranslationEffortPOTemplateRelationship to
	  TranslationEffortPOTemplate
	- add TranslationEffort.categories
	- add TranslationEffortPOTemplate.category
	- add POFile.filename and POFile.variant
	- add Project.shortdesc
	- add Project.wikiurl and homepageurl
	- remove POTemplate.project (we have .product)
	- make Country.title and .description NULLable
	- add POTranslationSighting.source ENUM
	- add DOAP-related tables ProductCVSModule, ProductBKBranch
	  and ProductSVNModule
	- add ProjectRole and ProductRole
	- add DOAP fields for Product:
	  - screenshotsurl, wikiurl, listurl, programminglang
	  - downloadurl, lastdoap
	- rewire BinarypackageUpload to point to DistroArchRelease
	  instead of DistroRelease
	- rename POMsgSet.iscurrent to POMsgSet.iscomplete
	   -> .iscurrent is now represented by .sequence>0
	- make POTemplate.branch NOT NULL
	- add POFile.fuzzyheader
	- remove Language.pluralform
	- add Language.pluralformexpresion
	- add Language.pluralforms
  v0.98:
        - merge SourceSource table from Andrew Bennetts
	- change SourceSource.homepageurl to SourceSource.product
	- BugInfestation: dateverified and verifiedby need to be NULL
	  if its not verified
	- set a lot of datecreated and lastverified etc fields to
	  DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')
	- use Andrew Bennett's way of putting comments inside the table
	  def, above the
	  line being commented, it makes lines shorter.
	- use foreign keys instead of the EITHER/OR stuff on:
	  - ManifestEntry
	  - ArchConfigEntry
	- clean up comments to fit inside 72 character terminals
	- add Changeset.name for Robert Weir
	- add ArchNamespace and move attributes there from Branch
	- Add BugActivity.id as a primary key for Andrew Veitch
	- Fix typo BugInfestation.createor -> BugInfestation.creator
	- add an owner to SourceSource
	- major Rosetta changes:
	  - remove Filters and Inheritance (don't need it for phase 1)
	  - rename POTFile -> POTemplate
	  - rename POTSubscription POSubscription
	  - add POTemplate.product
	  - add POMsgSet table
	  - rename POTMsgIDSighting -> POMsgIDSighting
	  - add owner and pluralforms to POFile
	  - merge RosettaPOTranslationSighting and POTranslationSighting
	  - move add POMsgSet.current
	  - add POTranslationSighting.deprecated
	  - rename POTranslationSighting.lastseen -> .lasttouched
	- make Project.product NOT NULL
	- add stats gathering to POTemplate and POFile
  v0.97:
        - rename Membership.label to Membership.role
	- rename EmailAddress.label to EmailAddress.status
	- move fields of Packaging around and rename Packaging.label
	  to Packaging.packaging
        - restructure recursive relationships to be
	  "subject - label - object"
	  - BranchRelationship
	  - ProjectRelationship
	  - CodereleaseRelationship
	  - SourcepackageRelationship
	  - BugRelationship
	  - Packaging
	- removed releasestatus from DistroArchRelease (we already
	  have it on DistroRelease)
	- moved releasedate to DistroArchRelease (simplify but lose
	  ability to release different arches at different dates)
	- remove ProjectTranslationEffortRelationship table altogether
	- add a TranslationEffort.project field
	- rename BugInfestation.affected to BugInfestation.infestation
  v0.96:
	- split categorybranchversion into category, branch and version
	- rename SourcepackageBug to SourcepackageBugAssignment
	- rename ProductBug to ProductBugAssignment
	- rename CodeReleaseBug to BugInfestation
	- eliminated BugSourcepackageRelationship since we made victimization
	  a kind of BugInfestation.affected
	- MASSIVE Table.id renaming of autogenerated primary keys
	- renaming of timestamp fields to "datecreated" or "daterevised"
	  style
	- consistency check between DIA and SQL, they should now be the same
  v0.95:
        - move bug priority from CodereleaseBug to SourcepackageBug
	- remove wontfix since it is now a bug priority ("wontfix")
	- add name to bugattachment
	- refactor bug attachments:
	  - don't have a relationship, each attachment on only one bug
	  - allow for revisions to attachments
	- rename BugRef to BugExternalref and remove bugref field
	- create a link ProjectBugsystem between Project's and BugSystem's
	- remove BugMessageSighting, each BugMessage now belongs to one 
	  and only one bug
	- add a nickname (optional unique name) to the Bug table
	- change the "summary" field of Bug to "title" for consistency
	- rename some tables:
	  - ReleaseBugStatus -> CodereleaseBug
	  - SourcepackageBugStatus -> SourcepackageBug
	  - ProductBugStatus -> ProductBug
        - add a createdate to project and product
  v0.94:
        - rename soyuz.sql to launchpad.sql
	- make Schema.extensible DEFAULT false (thanks spiv)
  v0.93:
        - add a manifest to Sourcepackage and Product, for the mutable
	  HEAD manifest
	- add a manifest to Coderelease
	- rename includeas to entrytype in ManifestEntry
	- remove "part" from ManifestEntry
	- add hints in Manifest table so sourcerer knows how to name
	  patch branches
	- fix my brain dead constraints for mutual exlcusivity on
	  branch/changeset specs
	- for a ManifestEntry, branch AND changeset can now both be null,
	  to allow for Scott's virtual entries
	- add the Packaging table to indicate the relationship between a
	  Product and a Sourcepackage
  v0.92:
        - make Schema and Label have name, title, description
        - added filenames for ProductreleaseFile, SourcepackageFile
	  and BinarypackageBuildFile
        - linked BinarypackageBuild to DistroRelease instead of
	  DistroArchRelease
        - add the Country table for a list of countries
	- add the SpokenIn table to link countries and languages
        - rename TranslationProject to TranslationEffort
        - add iscurrent (boolean) field to the POTFiles table, current
	  POTFiles
	    will be displayed in project summary pages.
        - add ChangesetFile, ChangesetFilename and ChangesetFileHash
	  tables
        - rename Release to Coderelease (and all dependent tables)
        - refactor Processor and ProcessorFamily:
	  - the distroarchrelease now has a processorfamily field
	  - the binarypackage (deb) now records its processor
	- refactor the allocation of binarypackage's (debs) to
	  distroarchrelease's
	  - create a new table BinarypackageUpload that stores the
	    packagearchivestatus
	  - remove that status from the BinarypackageBuild table
	- refactor sourcepackage upload status
	  - move changes and urgency to sourcepackagerelease
	  - add builddependsindep so sourcepackagerelease

  v0.91:
        - remove Translation_POTFileRelationship
	- ...and replace with a "project" field in POTFile
	- add a commenttext field to the POTMsgIDSighting table so we can
	  track comments in POT files too

  v0.9:
         6 July 2004
       - first versioned release
*/

/*
  DESTROY ALL TABLES
*/
-- remove 25/8/04
DROP TABLE BugAttachmentContent;
DROP TABLE ProductBranchRelationship;
DROP TABLE PackageSelection;
DROP TABLE SourcepackageBugAssignment;
DROP TABLE ArchArchiveLocationSigner;
DROP TABLE BugSubscription;
DROP TABLE SpokenIn;
DROP TABLE Country;
DROP TABLE TranslationEffortPOTemplate;
DROP TABLE POComment;
DROP TABLE BranchRelationship;
DROP TABLE ProjectBugsystem;
DROP TABLE BugWatch;
DROP TABLE BugSystem;
DROP TABLE POTranslationSighting;
DROP TABLE POMsgIDSighting;
DROP TABLE POMsgSet;
DROP TABLE POFile;
DROP TABLE POSubscription;
DROP TABLE POTemplate;
DROP TABLE License;
DROP TABLE BugRelationship;
DROP TABLE BugAttachment;
DROP TABLE BugMessage;
DROP TABLE BugExternalref;
DROP TABLE BugLabel;
DROP TABLE BugInfestation;
DROP TABLE ProductBugAssignment;
DROP TABLE BugActivity;
DROP TABLE BugSystemType;
DROP TABLE Bug;
DROP TABLE Packaging;
DROP TABLE CodereleaseRelationship;
DROP TABLE Coderelease;
DROP TABLE OSFileInPackage;
DROP TABLE OSFile;
DROP TABLE SourceSource;
DROP TABLE BinarypackageFile;
DROP TABLE PackagePublishing;
DROP TABLE Binarypackage;
DROP TABLE BinarypackageName;
DROP TABLE Build;
DROP TABLE SourcepackageReleaseFile;
DROP TABLE SourcepackageRelationship;
DROP TABLE SourcepackageUpload;
DROP TABLE SourcepackageRelease;
DROP TABLE SourcepackageLabel;
DROP TABLE Sourcepackage;
DROP TABLE SourcepackageName;
DROP TABLE Section;
DROP TABLE Component;
DROP TABLE ArchConfigEntry;
DROP TABLE ArchConfig;
DROP TABLE ProductReleaseFile;
DROP TABLE ProductSeries;
DROP TABLE ProductRelease;
DROP TABLE ChangesetFileHash;
DROP TABLE ChangesetFile;
DROP TABLE ChangesetFileName;
DROP TABLE ManifestEntry;
DROP TABLE Manifest;
DROP TABLE Changeset;
DROP TABLE BranchLabel;
DROP TABLE Branch;
DROP TABLE ArchNamespace;
DROP TABLE ArchArchiveLocation;
DROP TABLE ArchArchive;
DROP TABLE ProductCVSModule;
DROP TABLE ProductSVNModule;
DROP TABLE ProductBKBranch;
DROP TABLE ProductLabel;
DROP TABLE ProductRole;
DROP TABLE Product;
DROP TABLE POTranslation;
DROP TABLE ProjectRelationship;
DROP TABLE POMsgID;
DROP TABLE Language;
DROP TABLE TranslationEffort;
DROP TABLE ProjectRole;
DROP TABLE Project;
DROP TABLE EmailAddress;
DROP TABLE GPGKey;
DROP TABLE ArchUserID;
DROP TABLE Membership;
DROP TABLE WikiName;
DROP TABLE JabberID;
DROP TABLE IRCID;
DROP TABLE PersonLabel;
DROP TABLE TeamParticipation;
DROP TABLE Builder;
DROP TABLE DistroArchRelease;
DROP TABLE Processor;
DROP TABLE ProcessorFamily;
DROP TABLE DistributionRole;
DROP TABLE DistroReleaseRole;
DROP TABLE DistroRelease;
DROP TABLE Distribution;
DROP TABLE LibraryFileAlias;
DROP TABLE LibraryFileContent;
DROP TABLE Label;
DROP TABLE Schema;
DROP TABLE Person;



/*
  FOAF: MODEL OF A PERSON IN LAUNCHPAD
  Based on the FOAF ("Friend of a Friend") model
  from Ed Dumbill.
*/


/*
  Person
  This is a person in the Launchpad system. A Person can also be a
  team if the teamowner is not NULL. Note that we will create a
  Person entry whenever we see an email address we didn't know
  about, or a GPG key we didn't know about... and if we later
  link that to a real Launchpad person we will update all the tables
  that refer to that temporary person.

  A Person is one of these automatically created people if it
  has a NULL password and is not a team.
  
  It's created first so that a Schema can have an owner, we'll
  then define Schemas and Labels a bit later.
*/
CREATE TABLE Person (
  id                    serial PRIMARY KEY,
  presentationname      text,
  givenname             text,
  familyname            text,
  password              text,
  teamowner             integer REFERENCES Person,
  teamdescription       text,
  karma                 integer,
  karmatimestamp        timestamp
);



/*
  EmailAddress
  A table of email addresses for Launchpad people.
*/
CREATE TABLE EmailAddress (
  id          serial PRIMARY KEY,
  email       text NOT NULL UNIQUE,
  person      integer NOT NULL REFERENCES Person,
  -- see Email Address Status schema
  status      integer NOT NULL
);



/*
  GPGKey
  A table of GPGKeys, mapping them to Launchpad users.
*/
CREATE TABLE GPGKey (
  id          serial PRIMARY KEY,
  person      integer NOT NULL REFERENCES Person,
  keyid       text NOT NULL UNIQUE,
  fingerprint text NOT NULL UNIQUE,
  pubkey      text NOT NULL,
  revoked     boolean NOT NULL
);



/*
  ArchUserID
  A table of Arch user id's
*/
CREATE TABLE ArchUserID (
  id         serial PRIMARY KEY,
  person     integer NOT NULL REFERENCES Person,
  archuserid text NOT NULL UNIQUE
);



/*
  WikiName
  The identity a person uses on one of the Launchpad wiki's.
*/
CREATE TABLE WikiName (
  id         serial PRIMARY KEY,
  person     integer NOT NULL REFERENCES Person,
  wiki       text NOT NULL,
  wikiname   text NOT NULL,
  UNIQUE ( wiki, wikiname )
);



/*
  JabberID
  A person's Jabber ID on our network.
*/
CREATE TABLE JabberID (
  id          serial PRIMARY KEY,
  person      integer NOT NULL REFERENCES Person,
  jabberid    text NOT NULL UNIQUE
);



/*
  IrcID
  A person's irc nick's.
*/
CREATE TABLE IRCID (
  id           serial PRIMARY KEY,
  person       integer NOT NULL REFERENCES Person,
  network      text NOT NULL,
  nickname     text NOT NULL
);




/*
  Membership
  A table of memberships. It's only valid to have a membership
  in a team, not a non-team person.
*/
CREATE TABLE Membership (
  id          serial PRIMARY KEY,
  person      integer NOT NULL REFERENCES Person,
  team        integer NOT NULL REFERENCES Person,
  /* see Membership Role schema */
  role        integer NOT NULL, 
  /* see Membership Status schema */
  status      integer NOT NULL,
  -- a person can only have one membership in
  -- a given team
  UNIQUE ( person, team )
);



/*
  TeamParticipation
  This is a table which shows all the memberships
  of a person. Effectively it collapses team hierarchies
  and flattens them to a straight team-person relation.
  People are also members of themselves. This allows
  us to query against a person entry elsewhere in Launchpad
  and quickly find the things a person is an owner of.
*/
CREATE TABLE TeamParticipation (
  id           serial PRIMARY KEY,
  team         integer NOT NULL REFERENCES Person,
  person       integer NOT NULL REFERENCES Person,
  -- a person can only have one participation in a
  -- team.
  UNIQUE ( team, person )
);



/*
  REVELATION. THE SOYUZ METADATA
*/


/*
  Schema
  This is the (finger finger) "metadata" (finger finger).
*/
CREATE TABLE Schema (
  id             serial PRIMARY KEY,
  name           text NOT NULL,
  title          text NOT NULL,
  description    text NOT NULL,
  owner          integer NOT NULL REFERENCES Person,
  extensible     boolean NOT NULL DEFAULT false
);



/*
  Label
  The set of labels in all schemas
*/
CREATE TABLE Label (
  id             serial PRIMARY KEY,
  schema         integer NOT NULL REFERENCES Schema,
  name           text NOT NULL,
  title          text NOT NULL,
  description    text NOT NULL
);



/*
  PersonLabel
  A neat way to attach tags to people... this table is
  here, not in the FOAF section, because we need to 
  define Label before we can use it.
*/
CREATE TABLE PersonLabel (
  person       integer NOT NULL REFERENCES Person,
  label        integer NOT NULL REFERENCES Label
);



/*
  DOAP. DESCRIPTION OF A PROJECT
  This is the Launchpad subsystem that models the open source world
  of projects and products.
*/



/*
 The Project table. This stores information about an open
 source project, which can be translated or packaged, or
 about which bugs can be filed.
*/
CREATE TABLE Project (
    id           serial PRIMARY KEY,
    owner        integer NOT NULL REFERENCES Person,
    name         text NOT NULL UNIQUE,
    title        text NOT NULL,
    description  text NOT NULL,
    datecreated  timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    homepageurl  text,
    wikiurl      text,
    -- the last DOAP we received for this project
    lastdoap     text
    );


/*
 The ProjectRelationship table. This stores information about
 the relationships between open source projects. For example,
 the Gnome project aggregates the GnomeMeeting project.
*/
CREATE TABLE ProjectRelationship (
  id            serial PRIMARY KEY,
  subject       integer NOT NULL REFERENCES Project,
  -- see Project Relationships schema
  label         integer NOT NULL,
  object        integer NOT NULL REFERENCES Project
);



/*
  ProjectRole
  The roles that a person can take on in a project.
*/
CREATE TABLE ProjectRole (
  id            serial PRIMARY KEY,
  person        integer NOT NULL REFERENCES Person,
  -- see Project Role schema
  role          integer NOT NULL,
  project       integer NOT NULL REFERENCES Project
);


/*
  Product
  A table of project products. A product is something that
  can be built, or a branch of code that is useful elsewhere, or
  a set of docs... some distinct entity. Products can be made
  up of other products, but that is not reflected in this
  database. For example, Firefax includes Gecko, both are
  products.
*/
CREATE TABLE Product (
  id               serial PRIMARY KEY,
  project          integer NOT NULL REFERENCES Project,
  owner            integer NOT NULL REFERENCES Person,
  name             text NOT NULL,
  title            text NOT NULL,
  description      text NOT NULL,
  datecreated      timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  homepageurl      text,
  screenshotsurl   text,
  wikiurl          text,
  listurl          text,
  programminglang  text,
  downloadurl      text,
  -- the last DOAP we received for this product
  lastdoap         text,
  UNIQUE ( project, name ),
  -- ( id, project ) must be unique so it can be a foreign key
  UNIQUE ( id, project )
);



/*
  ProductLabel
  A label or metadata on a Product.
*/
CREATE TABLE ProductLabel (
  id         serial PRIMARY KEY,
  product    integer NOT NULL REFERENCES Product,
  label      integer NOT NULL REFERENCES Label,
  UNIQUE ( product, label )
);



/*
  Product Role
  The roles that a person has with regard to a
  product.
*/
CREATE TABLE ProductRole (
  id        serial PRIMARY KEY,
  person    integer NOT NULL REFERENCES Person,
  -- see the Product Role schema
  role      integer NOT NULL,
  product   integer NOT NULL REFERENCES Product
);


/*
  ProductSeries
  A series of releases for this product. Typically
  open source projects have a number of different
  active branches of development, which turn into
  releases. For example, Mozilla currently has
  builds from the trunk ("HEAD"), 1.7 and 1.6
  series.
*/
CREATE TABLE ProductSeries (
  id            serial PRIMARY KEY,
  product       integer NOT NULL REFERENCES Product,
  name          text NOT NULL,
  displayname   text NOT NULL,
  UNIQUE ( product, name )
);



/*
  ProductRelease
  A specific tarball release of Product.
*/
CREATE TABLE ProductRelease (
  id               serial PRIMARY KEY,
  product          integer NOT NULL REFERENCES Product,
  datereleased     timestamp NOT NULL,
  -- the version without anything else, "1.3.29"
  version          text NOT NULL,
  -- the GSV Name "The Warty Web Release"
  title            text,
  description      text,
  changelog        text,
  owner            integer NOT NULL REFERENCES Person,
  UNIQUE ( product, version )
);



/*
  ProductCVSModule
  A CVS Module, initially based on the DOAP
  model. this is specifically tied to a Product
*/
CREATE TABLE ProductCVSModule (
  id           serial PRIMARY KEY,
  product      integer NOT NULL REFERENCES Product,
  anonroot     text NOT NULL,
  module       text NOT NULL,
  weburl       text
);



/*
  ProductBKBranch
  A BitKeeper Branch, initially based on the DOAP
  model. This is specifically associated with a
  Product.
*/
CREATE TABLE ProductBKBranch (
  id           serial PRIMARY KEY,
  product      integer NOT NULL REFERENCES Product,
  locationurl  text NOT NULL,
  weburl       text
);



/*
  ProductSVNModule
  A Subversion module, again tied to a Product. This
  came from the DOAP model.
*/
CREATE TABLE ProductSVNModule (
  id           serial PRIMARY KEY,
  product      integer NOT NULL REFERENCES Product,
  locationurl  text NOT NULL,
  weburl       text
);



/*
  BUTTRESS. THE ARCH REPOSITORY.
  This is the Launchpad subsystem that handles the storing and
  cataloguing of all of our Arch branches.
*/



/*
  ArchArchive
  A table of all known Arch Archives.
*/
CREATE TABLE ArchArchive (
  id            serial PRIMARY KEY,
  name          text NOT NULL,
  title         text NOT NULL,
  description   text NOT NULL,
  visible       boolean NOT NULL,
  owner         integer REFERENCES Person
);



/*
  ArchArchiveLocation
  A table of known Arch archive locations.
*/
CREATE TABLE ArchArchiveLocation (
  id            serial PRIMARY KEY,
  archive       integer NOT NULL REFERENCES ArchArchive,
  /* see the Arch Archive Type schema */
  archivetype   integer NOT NULL,
  url           text NOT NULL,
  gpgsigned     boolean NOT NULL
);



/*
  ArchArchiveLocationSigner
  A table of keys used to sign Arch Archive Locations
*/
CREATE TABLE ArchArchiveLocationSigner (
  archarchivelocation   integer NOT NULL REFERENCES ArchArchiveLocation,
  gpgkey                integer NOT NULL REFERENCES GPGKey
);




/*
  ArchNamespace
  This is a table to capture the vagaries of the Arch
  namespace. Branch is a "place we hang changesets"
  but each Branch needs a Namespace where it lives. If
  the TLA naming system were to change later we would
  only need to change ArchNamespace, not Branch. Also,
  A Branch is guaranteed to be a place where changesets
  can be put, not just a placeholder.
*/
CREATE TABLE ArchNamespace (
  id                     serial PRIMARY KEY,
  archarchive            integer NOT NULL REFERENCES ArchArchive,
  category               text NOT NULL,
  branch                 text,
  version                text,
  visible                boolean NOT NULL
);



/*
  Branch
  An Arch Branch in the Launchpad system.
*/
CREATE TABLE Branch (
  id                     serial PRIMARY KEY,
  archnamespace          integer NOT NULL REFERENCES ArchNamespace,
  title                  text NOT NULL,
  description            text NOT NULL,
  owner                  integer REFERENCES Person,
  product                integer REFERENCES Product
);




/*
  Changeset
  An Arch changeset.
*/
CREATE TABLE Changeset (
  id             serial PRIMARY KEY,
  branch         integer NOT NULL REFERENCES Branch,
  datecreated    timestamp NOT NULL,
  name           text NOT NULL,
  logmessage     text NOT NULL,
  archid         integer REFERENCES ArchUserID,
  gpgkey         integer REFERENCES GPGKey,
  /* We need the id / branch pair to be UNIQUE so that
     it can be a FOREIGN KEY in other tables */
  UNIQUE ( id, branch )
);



/*
  ChangesetFileName
  A filename in an arch changeset.
*/
CREATE TABLE ChangesetFileName (
  id         serial PRIMARY KEY,
  filename   text NOT NULL UNIQUE
);



/*
  ChangesetFile
  A file in an arch changeset.
*/
CREATE TABLE ChangesetFile (
  id                 serial PRIMARY KEY,
  changeset          integer NOT NULL REFERENCES Changeset,
  changesetfilename  integer NOT NULL REFERENCES ChangesetFileName,
  filecontents       bytea NOT NULL,
  filesize           integer NOT NULL,
  UNIQUE ( changeset, changesetfilename )
);



/*
  ChangesetFileHash
  A cryptographic hash of a changeset file.
*/
CREATE TABLE ChangesetFileHash (
  id                serial PRIMARY KEY,
  changesetfile     integer NOT NULL REFERENCES ChangesetFile,
  /* see Hash Algorithms schema */
  hashalg           integer NOT NULL,
  hash              bytea NOT NULL,
  UNIQUE ( changesetfile, hashalg )
);



/*
  BranchRelationship
  A table of relationships between branches. For example:
  "subject is a debianization-branch-of object"
  "subject is-a-patch-branch-of object"
*/
CREATE TABLE BranchRelationship (
  subject       integer NOT NULL REFERENCES Branch,
  /* see the Branch Relationships schema */
  label         integer NOT NULL,
  object        integer NOT NULL REFERENCES Branch,
  PRIMARY KEY ( subject, object )
);




/*
  BranchLabel
  A table of labels on branches.
*/
CREATE TABLE BranchLabel (
  branch       int NOT NULL REFERENCES Branch,
  label        int NOT NULL REFERENCES Label
);



/*
  ProductBranchRelationship
  This is where we can store a mapping between
  a product and a branch.
*/
CREATE TABLE ProductBranchRelationship (
  id         serial PRIMARY KEY,
  product    integer NOT NULL REFERENCES Product,
  branch     integer NOT NULL REFERENCES Branch,
  -- XXX need to create the Product Branch Relationship schema
  label      integer NOT NULL
);


/*
  Manifest
  A release manifest. This is sort of an Arch config
  on steroids. A Manifest is a set of ManifestEntry's
*/
CREATE TABLE Manifest (
  id               serial PRIMARY KEY,
  datecreated      timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  owner            integer NOT NULL REFERENCES Person
);




/*
  ManifestEntry
  An entry in a Manifest. each entry specifies either a branch or
  a specific changeset (revision) on a branch, as well as how that
  piece of code (revision) is brought into the release.
*/
CREATE TABLE ManifestEntry (
  id              serial PRIMARY KEY,
  manifest        integer NOT NULL REFERENCES Manifest,
  sequence        integer NOT NULL,
  branch          integer REFERENCES Branch NOT NULL,
  changeset       integer REFERENCES Changeset,
  /* see Manifest Entry Type schema */
  entrytype       integer NOT NULL,
  path            text NOT NULL,
  patchon         integer,
  dirname         text,
  -- sequence must be a positive integer
  CHECK ( sequence > 0 ),
  /* if we specified a changeset make sure it is on the same
     branch as we also specified */
  FOREIGN KEY ( branch, changeset ) REFERENCES Changeset ( branch, id ),
  /* the "patchon" must be another manifestentry from the same
     manifest, and a different sequence */
  FOREIGN KEY ( manifest, patchon ) REFERENCES ManifestEntry ( manifest, sequence ),
  CHECK ( patchon <> sequence ),
  UNIQUE ( manifest, sequence )
);



/*
   BUTTRESS phase 2
*/


/*
  ArchConfig
  A table to model Arch configs.
*/
CREATE TABLE ArchConfig (
  id               serial PRIMARY KEY,
  name             text NOT NULL,
  title            text NOT NULL,
  description      text NOT NULL,
  productrelease   integer REFERENCES ProductRelease,
  owner            integer REFERENCES Person
);



/*
  ArchConfigEntry
  A table to represent the entries in an Arch config. Each
  row is a separate entry in the arch config.
*/
CREATE TABLE ArchConfigEntry (
  archconfig    integer NOT NULL REFERENCES ArchConfig,
  path          text NOT NULL,
  branch        integer NOT NULL REFERENCES Branch,
  changeset     integer REFERENCES Changeset,
  /* enforce referential integrity if both branch and changeset
     were given */
  FOREIGN KEY ( branch, changeset ) REFERENCES Changeset ( branch, id )
);



/*
  SOYUZ. THE PACKAGES AND DISTRIBUTION MANAGER.
*/



/*
  ProcessorFamily
  A family of CPU's, which are all compatible. In other words, code
  compiled for any one of these processors will run on any of the
  others.
*/
CREATE TABLE ProcessorFamily (
  id                 serial PRIMARY KEY,
  name               text NOT NULL UNIQUE,
  title              text NOT NULL,
  description        text NOT NULL,
  owner              integer NOT NULL REFERENCES Person
);



/*
  Processor
  This is a table of system architectures. A DistroArchRelease needs
  to be one of these.
*/
CREATE TABLE Processor (
  id                 serial PRIMARY KEY,
  family             integer NOT NULL REFERENCES ProcessorFamily,
  name               text NOT NULL UNIQUE,
  title              text NOT NULL,
  description        text NOT NULL,
  owner              integer NOT NULL REFERENCES Person
);



/*
  Builder
  A build daemon, one of Lamont's babies.
*/
CREATE TABLE Builder (
  id                 serial PRIMARY KEY,
  processor          integer NOT NULL REFERENCES Processor,
  fqdn               text NOT NULL,
  name               text NOT NULL,
  title              text NOT NULL,
  description        text NOT NULL,
  owner              integer NOT NULL REFERENCES Person,
  UNIQUE ( fqdn, name )
);



/*
  Component
  Distributions divide their packages into a set
  of "components" which have potentially different
  policies and practices.
*/
CREATE TABLE Component (
  id                 serial PRIMARY KEY,
  name               text NOT NULL UNIQUE
);



/*
  Section
  For historical reasons, each package can be assigned
  to a particular section within the distribution.
*/
CREATE TABLE Section (
  id                serial PRIMARY KEY,
  name              text NOT NULL UNIQUE
);



/*
  Distribution
  An open source distribution. Collection of packages, the reason
  for Launchpad existence.
*/
CREATE TABLE Distribution (
  id               serial PRIMARY KEY,
  name             text NOT NULL,
  title            text NOT NULL,
  description      text NOT NULL,
  -- the domain name of the distribution. we use
  -- this so we know how to map "soyuz.distro.net"
  -- for example: ubuntu.com, debian.org, redhat.com
  domainname       text NOT NULL,
  owner            integer NOT NULL REFERENCES Person
);



/*
  Distribution Role
  A person can take on a number of roles within a
  distribution. These are documented in the
  DistributionRole schema, and recorded here.
*/
CREATE TABLE DistributionRole (
  person          integer NOT NULL REFERENCES Person,
  distribution    integer NOT NULL REFERENCES Distribution,
  role            integer NOT NULL
);



/*
  DistroRelease
  These are releases of the various distributions in the system. For
  example: warty, hoary, grumpy, woody, potato, slink, sarge, fc1,
  fc2.
*/
CREATE TABLE DistroRelease (
  id              serial PRIMARY KEY,
  distribution    integer NOT NULL REFERENCES Distribution,
  name            text NOT NULL, -- "warty"
  title           text NOT NULL, -- "Ubuntu 4.10 (The Warty Warthog Release)"
  description     text NOT NULL,
  version         text NOT NULL, -- "4.10"
  components      integer NOT NULL REFERENCES Schema,
  sections        integer NOT NULL REFERENCES Schema,
  -- see Distribution Release State schema
  releasestate    integer NOT NULL,
  datereleased    timestamp,
  -- the Ubuntu distrorelease from which this distrorelease
  -- is derived. This needs to point at warty, hoary, grumpy
  -- etc.
  parentrelease   integer REFERENCES DistroRelease,
  owner           integer NOT NULL REFERENCES Person
);



/*
  DistroReleaseRole
  A person can have roles within a Distribution, and sometimes
  these roles are specific to a single release. In general
  roles should be recorded in the DistributionRole table unless
  they really are limited to a specific distribution release,
  in which case they should be recorded here.
*/
CREATE TABLE DistroReleaseRole (
  person         integer NOT NULL REFERENCES Person,
  distrorelease  integer NOT NULL REFERENCES DistroRelease,
  -- see the DistributionRole schema
  role           integer NOT NULL
);


/*
  DistroArchRelease
  This is a distrorelease for a particular architecture, for example,
  warty-i386.
*/
CREATE TABLE DistroArchRelease (
  id                serial PRIMARY KEY,
  distrorelease     integer NOT NULL REFERENCES DistroRelease,
  processorfamily   integer NOT NULL REFERENCES ProcessorFamily,
  architecturetag   text NOT NULL,
  owner             integer NOT NULL REFERENCES Person
);


/*
  LibraryFileContent
  A pointer to file content in the librarian. We store the sha1 hash
  to allow us to do duplicate detection, size so web applications can
  warn users of the download size, and some timestamps. The mirrored
  timestamp, if set, tells us that the file has been mirrored onto
  the aukland server.
 
  Other tables do not reference this content directly - they should
  reference LibraryFile which cointains the filename and mimetype

  Note that the sha1 column is not unique - we are dealing with enough
  files that we may get collisions, so this is used mearly as method
  of identifying which files need to be compared.
*/
CREATE TABLE LibraryFileContent (
    id            serial PRIMARY KEY,
    datecreated   timestamp NOT NULL 
                    DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
    datemirrored  timestamp,
    filesize      int NOT NULL,
    sha1          character(40) NOT NULL
);
CREATE INDEX idx_LibraryFileContent_sha1 ON LibraryFileContent(sha1);


/*
  LibraryFileAlias
  A filename and mimetype that we can serve some given binary content with.
  We seperate LibraryFileContent and LibraryFileAlias so the same file
  can be reused multiple times with different names and/or mimetypes
*/
CREATE TABLE LibraryFileAlias (
    id            serial PRIMARY KEY,
    content       int NOT NULL REFERENCES LibraryFileContent,
    filename      text NOT NULL,
    mimetype      text NOT NULL
);


/*
  ProductReleaseFile
  A file from an Product Coderelease. Usually this would be a tarball.
*/
CREATE TABLE ProductReleaseFile (
  productrelease integer NOT NULL REFERENCES ProductRelease,
  libraryfile    integer NOT NULL REFERENCES LibraryFileAlias,
  -- see Product File Type schema
  filetype        integer NOT NULL
);



/*
  SourcepackageName
  Source packages can share names, so these are stored
  in a separate table.
*/
CREATE TABLE SourcepackageName (
  id               serial PRIMARY KEY,
  name             text NOT NULL UNIQUE
);



/*
  Sourcepackage
  A distribution source package. In RedHat or Debian this is the name
  of the source package, in Gentoo it's the Ebuild name.
*/
CREATE TABLE Sourcepackage (
  id               serial PRIMARY KEY,
  maintainer       integer NOT NULL REFERENCES Person,
  name             text NOT NULL,
  title            text NOT NULL,
  description      text NOT NULL,
  -- the "head manifest" if this package is being
  -- maintained in HCT
  manifest         integer REFERENCES Manifest,
  -- the distribution to which this package was
  -- origininally uploaded, or ubuntu if it is
  -- not a derivative distro package.
  distro           integer REFERENCES Distribution
);



/*
  SourcepackageRelationship
  The relationship between two source packages. For example, if a source
  package in Ubuntu is derived from a source package in Debian, we would
  reflect that here.
*/
CREATE TABLE SourcepackageRelationship (
  subject      integer NOT NULL REFERENCES Sourcepackage,
  -- see Source Package Relationship schema
  label        integer NOT NULL,
  object       integer NOT NULL REFERENCES Sourcepackage,
  CHECK ( subject <> object ),
  PRIMARY KEY ( subject, object )
);



/*
  SourcepackageLabel
  A tag or label on a source package.
*/
CREATE TABLE SourcepackageLabel (
  sourcepackage     integer NOT NULL REFERENCES Sourcepackage,
  label             integer NOT NULL REFERENCES Label
);




/*
  Packaging
  This is really the relationship between a Product and a
  Sourcepackage. For example, it allows us to say that
  the apache2 source package is a packaging of the
  httpd Product from the Apache Group.
*/
CREATE TABLE Packaging (
  sourcepackage   integer NOT NULL REFERENCES Sourcepackage,
  -- see the Packaging schema
  packaging       integer NOT NULL,
  product         integer NOT NULL REFERENCES Product
);




/*
  SourcepackageRelease
  A SourcepackageRelease is a specific release of a Sourcepackage, which is
  associated with one or more distribution releases. So apache2__2.0.48-3 can
  be in both ubuntu/warty and debian/sarge.
*/
CREATE TABLE SourcepackageRelease (
  id                     serial PRIMARY KEY,
  sourcepackage          integer NOT NULL REFERENCES Sourcepackage,
  -- see Source Package Format schema
  srcpackageformat       integer NOT NULL,
  creator                integer NOT NULL REFERENCES Person,
  -- "2.0.48-3"
  version                text NOT NULL,
  dateuploaded           timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  -- see Source Package Urgency schema
  urgency                integer NOT NULL,
  dscsigningkey          integer REFERENCES GPGKey,
  component              integer REFERENCES Label,
  changelog              text,
  builddepends           text,
  builddependsindep      text,
  architecturehintlist   text,
  dsc                    text
);



/*
  SourcepackageReleaseFile
  A file associated with a sourcepackagerelease. For example, could be
  a .dsc file, or an orig.tar.gz, or a diff.gz...
*/
CREATE TABLE SourcepackageReleaseFile (
  sourcepackagerelease  integer NOT NULL REFERENCES SourcepackageRelease,
  libraryfile           integer NOT NULL REFERENCES LibraryFileAlias,
  -- see Source Package File Types schema
  filetype              integer NOT NULL
);



/*
  SourcepackageUpload
  This table indicates which sourcepackagereleases are present in a
  given distrorelease. It also indicates their status in that release
  (for example, whether or not that sourcepackagerelease has been
  withdrawn, or is currently published, in that archive).
*/
CREATE TABLE SourcepackageUpload (
  distrorelease          integer NOT NULL REFERENCES DistroRelease,
  sourcepackagerelease   integer NOT NULL REFERENCES SourcepackageRelease,
  -- see Source Upload Status schema
  uploadstatus           integer NOT NULL,
  PRIMARY KEY ( distrorelease, sourcepackagerelease )
);


/*
  Build
  This table describes a build (or upload if the binary packages
  were built elsewhere and then uploaded to us. If we need to build
  then we create an entry in this table and the Build Scheduler will
  figure out who gets to do the work.
*/
CREATE TABLE Build (
  id                serial PRIMARY KEY,
  datecreated       timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  processor         integer NOT NULL REFERENCES Processor,
  distroarchrelease integer NOT NULL REFERENCES DistroArchRelease,
  buildstate        integer NOT NULL,
  datebuilt         timestamp,
  buildduration     interval,
  buildlog          integer REFERENCES LibraryFileAlias,
  builder           integer REFERENCES Builder,
  gpgsigningkey     integer REFERENCES GPGKey,
  changes           text
);



/*
  BinarypackageName
  This is a binary package name... not an actual built package
*/
CREATE TABLE BinarypackageName (
  id               serial PRIMARY KEY,
  name             text NOT NULL UNIQUE
);




/*
  Binarypackage
  This is an actual package, built on a specific architecture,
  ready for installation.
*/
CREATE TABLE Binarypackage (
  id                     serial PRIMARY KEY,
  sourcepackagerelease   integer NOT NULL REFERENCES SourcepackageRelease,
  binarypackagename      integer NOT NULL REFERENCES BinarypackageName,
  version                text NOT NULL,
  shortdesc              text NOT NULL,
  description            text NOT NULL,
  build                  integer NOT NULL REFERENCES Build,
  -- see Binary Package Formats schema
  binpackageformat       integer NOT NULL,
  component              integer NOT NULL REFERENCES Component,
  section                integer NOT NULL REFERENCES Section,
  -- see Binary Package Priority schema
  priority               integer,
  shlibdeps              text,
  depends                text,
  recommends             text,
  suggests               text,
  conflicts              text,
  replaces               text,
  provides               text,
  essential              boolean,
  installedsize          integer,
  copyright              text,
  licence                text,
  UNIQUE ( binarypackagename, version )
);



/*
  BinarypackageBuildFile
  This is a file associated with a built binary package. Could
  be a .deb or an rpm, or something similar from a gentoo box.
*/
CREATE TABLE BinarypackageFile (
  binarypackage     integer NOT NULL REFERENCES Binarypackage,
  libraryfile       integer NOT NULL REFERENCES LibraryFileAlias,
  -- see Binary Package File Type schema
  filetype          integer NOT NULL
);



/*
  PackagePublishing
  This table records the status of a binarypackage (deb) in a
  distroarchrelease (woody i386)
*/
CREATE TABLE PackagePublishing (
  id                     serial PRIMARY KEY,
  binarypackage          integer NOT NULL REFERENCES Binarypackage,
  distroarchrelease      integer NOT NULL REFERENCES DistroArchRelease,
  -- see Package Upload Status schema
  component              integer NOT NULL REFERENCES Component,
  section                integer NOT NULL REFERENCES Section,
  -- see Binary Package Priority schema
  priority               integer NOT NULL
);



/*
  PackageSelection
  This table records the policy of a distribution in terms
  of packages they will accept and reject.
*/
CREATE TABLE PackageSelection (
  id                     serial PRIMARY KEY,
  distrorelease          integer NOT NULL REFERENCES DistroRelease,
  sourcepackagename      integer REFERENCES SourcepackageName,
  binarypackagename      integer REFERENCES BinarypackageName,
  action                 integer NOT NULL,
  component              integer REFERENCES Component,
  section                integer REFERENCES Section,
  -- see the Binary Package Priority schema
  priority               integer
);



/*
  LIBRARIAN. TRACKING UPSTREAM AND SOURCE PACKAGE RELEASES.
  This section is devoted to data that tracks product and distribution
  SOURCE PACKAGE releases. So, for example, Apache 2.0.48 is an
  ProductRelease. Apache 2.0.48-3 is a Debian SourcepackageRelease.
  We have data tables for both of those, and the Coderelease table is
  the data that is common to any kind of Coderelease. This subsystem also
  keeps track of the actual files associated with Codereleases, such as
  tarballs and deb's and .dsc files and changelog files...
*/



/*
  Coderelease
  A release of software. Could be an Product release or
  a SourcepackageRelease.
*/
CREATE TABLE Coderelease (
  id                   serial PRIMARY KEY,
  productrelease      integer REFERENCES ProductRelease,
  sourcepackagerelease integer REFERENCES SourcepackageRelease,
  manifest             integer REFERENCES Manifest,
  CHECK ( NOT ( productrelease IS NULL AND sourcepackagerelease IS NULL ) ),
  CHECK ( NOT ( productrelease IS NOT NULL AND sourcepackagerelease IS NOT NULL ) )
); -- EITHER productrelease OR sourcepackagerelease must not be NULL




/*
  CodereleaseRelationship
  Maps the relationships between releases (product and
  sourcepackage).
*/
CREATE TABLE CodereleaseRelationship (
  subject       integer NOT NULL REFERENCES Coderelease,
  -- see Coderelease Relationships schema
  label         integer NOT NULL,
  object        integer NOT NULL REFERENCES Coderelease,
  CHECK ( subject <> object ),
  PRIMARY KEY ( subject, object )
);





/*
  OSFile
  This is a file in one of the OS's managed in Launchpad.
*/
CREATE TABLE OSFile (
  id        serial PRIMARY KEY,
  path      text NOT NULL UNIQUE
);



/*
  OSFileInPackage
  This table tells us all the files that are in a given binary package
  build. It also includes information about the files, such as their
  unix permissions, and whether or not they are a conf file.
*/
CREATE TABLE OSFileInPackage (
  osfile               integer NOT NULL REFERENCES OSFile,
  binarypackage        integer NOT NULL REFERENCES Binarypackage,
  unixperms            integer NOT NULL,
  conffile             boolean NOT NULL,
  createdoninstall     boolean NOT NULL
);






/*
  ROSETTA. THE TRANSLATION SUPER-PORTAL
  This is the Launchpad subsystem that coordinates and manages
  the translation of open source software and documentation.
*/




/*
  TranslationFilter
  A set of "sunglasses" through which we see translations. We only want
  to see translations that are compatible with this filter in terms
  of licence, review and contribution criteria. This will not be
  implemented in Rosetta v1.0
CREATE TABLE TranslationFilter (
  id                serial PRIMARY KEY,
  owner             integer NOT NULL REFERENCES Person,
  name              text NOT NULL UNIQUE,
  title             text NOT NULL,
  description       text NOT NULL
);
*/




/*
  POMsgID
  A PO or POT File MessageID
*/
CREATE TABLE POMsgID (
  id                   serial PRIMARY KEY,
  msgid                text NOT NULL UNIQUE
);



/*
  POTranslation
  A PO translation. This is just a piece of text, where the
  "translation" might in fact be the original language.
*/
CREATE TABLE POTranslation (
  id                    serial PRIMARY KEY,
  translation           text NOT NULL UNIQUE
);



/*
  Language
  A table of languages, for Rosetta.
*/
CREATE TABLE Language (
  id                    serial PRIMARY KEY,
  code                  text NOT NULL UNIQUE,
  englishname           text,
  nativename            text,
  pluralforms           integer,
  pluralexpresion	text,
  CHECK ( ( pluralforms IS NOT NULL AND pluralexpresion IS NOT NULL) OR
          ( pluralforms IS NULL AND pluralexpresion IS NULL ) )
);




/*
  Country
  A list of countries.
*/
CREATE TABLE Country (
  id                  serial PRIMARY KEY,
  iso3166code2        char(2) NOT NULL,
  iso3166code3        char(3) NOT NULL,
  name                text NOT NULL,
  title               text,
  description         text
);



/*
  SpokenIn
  A table linking countries the languages spoken in them.
*/
CREATE TABLE SpokenIn (
  language           integer NOT NULL REFERENCES Language,
  country            integer NOT NULL REFERENCES Country,
  PRIMARY KEY ( language, country )
);



/*
  POTInheritance
  A handle on an inheritance sequence for POT files.
CREATE TABLE POTInheritance (
  id                    serial PRIMARY KEY,
  title                 text,
  description           text
);
*/



/*
  License
  A license. We need quite a bit more in the long term
  to track licence compatibility etc.
*/
CREATE TABLE License (
  id                    serial PRIMARY KEY,
  legalese              text NOT NULL
);



/*
  POTemplate
  A PO Template File, which is the first thing that Rosetta will set
  about translating.
*/
CREATE TABLE POTemplate (
  id                    serial PRIMARY KEY,
  product               integer NOT NULL REFERENCES Product,
  -- see Translation Priority schema
  priority              integer NOT NULL,
  branch                integer NOT NULL REFERENCES Branch,
  changeset             integer REFERENCES Changeset,
  name                  text NOT NULL UNIQUE,
  title                 text NOT NULL,
  description           text NOT NULL,
  copyright             text NOT NULL,
  license               integer NOT NULL REFERENCES License,
  datecreated           timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  path                  text NOT NULL,
  iscurrent             boolean NOT NULL,
  -- the total number of POMsgSet's associated with this POTemplate
  -- when we last parsed the Template.
  messagecount          integer NOT NULL,
  owner                 integer REFERENCES Person,
  -- make sure that a potemplate name is unique in
  -- a given product
  UNIQUE ( product, name ),
  -- if we refer to a changeset make sure that it's
  -- one where the branch is consistent for that changeset.
  FOREIGN KEY ( changeset, branch ) REFERENCES Changeset ( id, branch )
);



/*
  POFile
  A PO File. This is a language-specific set of translations.
*/
CREATE TABLE POFile (
  id                   serial PRIMARY KEY,
  potemplate           integer NOT NULL REFERENCES POTemplate,
  language             integer NOT NULL REFERENCES Language,
  title                text,
  description          text,
  topcomment           text,  -- the comment at the top of the file
  header               text,  -- the contents of the NULL msgstr
  fuzzyheader          boolean NOT NULL,
  lasttranslator       integer REFERENCES Person,
  license              integer REFERENCES License,
  -- the number of msgsets matched to the potemplate that have a
  -- non-fuzzy translation in the PO file when we last parsed it
  currentcount         integer NOT NULL,
  -- the number of msgsets where we have a newer translation in
  -- rosetta than the one in the PO file when we last parsed it
  updatescount         integer NOT NULL,
  -- the number of msgsets where we have a translation in rosetta
  -- but there was no translation in the PO file when we last parsed it
  rosettacount         integer NOT NULL,
  -- the timestamp when we last parsed this PO file
  lastparsed           timestamp,
  owner                integer REFERENCES Person,
  -- the number of plural forms needed to translate this
  -- pofile.
  pluralforms          integer NOT NULL,
  -- the dialect or other variation
  variant              text,
  -- the filename within the branch where we find this
  -- PO file
  filename             text,
  -- needs to be UNIQUE so POMsgSet can refer to this
  -- tuple
  UNIQUE (id, potemplate )
);



/*
  POMsgSet
  Each POTemplate and POFile is made up of a set of POMsgSets
  each of which has both msgid's and translations.
*/
CREATE TABLE POMsgSet (
  id                  serial PRIMARY KEY,
  primemsgid          integer NOT NULL REFERENCES POMsgID,
  sequence            integer NOT NULL,
  potemplate          integer NOT NULL REFERENCES POTemplate,
  pofile              integer REFERENCES POFile,
  iscomplete          boolean NOT NULL,
  obsolete            boolean NOT NULL,
  fuzzy               boolean NOT NULL,
  -- the free text comment of the msgset
  commenttext         text,
  -- references to the specific lines of code that
  -- use this messageset
  filereferences      text,
  -- The comment included in the source code
  sourcecomment       text,
  -- For example: c-source, python-source etc
  flagscomment        text,
  FOREIGN KEY ( pofile, potemplate ) REFERENCES POFile ( id, potemplate ),
  UNIQUE ( potemplate, pofile, primemsgid )
);



/*
  POMsgIDSighting
  Table that documents the sighting of a particular msgid in a pot file.
*/
CREATE TABLE POMsgIDSighting (
  id                  serial PRIMARY KEY,
  pomsgset            integer NOT NULL REFERENCES POMsgSet,
  pomsgid             integer NOT NULL REFERENCES POMsgID,
  firstseen           timestamp NOT NULL,
  lastseen            timestamp NOT NULL,
  inpofile            boolean NOT NULL,
  -- 0 for English singular, 1 for English plural
  pluralform          integer NOT NULL,
  -- we only want one sighting of an id in a msgset
  UNIQUE ( pomsgset, pomsgid )
);



/*
  POTranslationSighting
  A sighting of a translation in a PO file. Could have come
  from the web or from an actual PO file in RCS.
*/
CREATE TABLE POTranslationSighting (
  id                    serial PRIMARY KEY,
  pomsgset              integer NOT NULL REFERENCES POMsgSet,
  potranslation         integer NOT NULL REFERENCES POTranslation,
  license               integer NOT NULL REFERENCES License,
  firstseen             timestamp NOT NULL,
  lasttouched           timestamp NOT NULL,
  inpofile              boolean NOT NULL,
  pluralform            integer NOT NULL,
  deprecated            boolean NOT NULL DEFAULT FALSE,
  -- where this translation came from, see the
  -- Rosetta Translation Origin schema
  origin                integer NOT NULL,
  person                integer REFERENCES Person,
  CHECK ( pluralform >= 0 ),
  -- these are the things that really define a translation
  UNIQUE ( pomsgset, potranslation, license, person )
);



/*
  RosettaPOTranslationSighting
  A record of a translation given to Rosetta through the web, or
  web service, or otherwise.
  
  DEPRECATED, this is all handled in POTranslationSighting.
  
CREATE TABLE RosettaPOTranslationSighting (
  id                   serial PRIMARY KEY,
  person               integer NOT NULL REFERENCES Person,
  potemplate              integer NOT NULL REFERENCES POTemplate,
  pomsgid              integer NOT NULL REFERENCES POMsgID,
  language             integer NOT NULL REFERENCES Language,
  potranslation        integer NOT NULL REFERENCES POTranslation,
  license              integer NOT NULL REFERENCES License,
  dateprovided         timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  datetouched          timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  pluralform           integer,
  CHECK ( pluralform >= 0 )
);
*/



/*
  POComment
  A table of comments provided by translators and the translation
  system (these are extracted from PO files as well as provided to
  us through the web and web services API).
*/
CREATE TABLE POComment (
  id                  serial PRIMARY KEY,
  potemplate             integer NOT NULL REFERENCES POTemplate,
  pomsgid             integer REFERENCES POMsgID,
  language            integer REFERENCES Language,
  potranslation       integer REFERENCES POTranslation,
  commenttext         text NOT NULL,
  datecreated         timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  person              integer REFERENCES Person
);




/*
 The TranslationEffort table. Stores information about each active
 translation effort. Note, a translationeffort is an aggregation of
 resources. For example, the Gnome Translation Project, which aims to
 translate the PO files for many gnome applications. This is a point
 for the translation team to rally around.
*/
CREATE TABLE TranslationEffort (
  id                    serial PRIMARY KEY,
  owner                 integer NOT NULL REFERENCES Person,
  project               integer NOT NULL REFERENCES Project,
  name                  text NOT NULL UNIQUE,
  title                 text NOT NULL,
  shortdesc             text NOT NULL,
  description           text NOT NULL,
  categories            integer REFERENCES Schema
);



/*
  TranslationEffortPOTemplate
  A translation project incorporates a POTfile that is under translation.
  The inheritance pointer allows this project to specify a custom
  translation inheritance sequence.
*/
CREATE TABLE TranslationEffortPOTemplate (
  translationeffort  integer NOT NULL REFERENCES TranslationEffort ON DELETE CASCADE,
  potemplate         integer NOT NULL REFERENCES POTemplate,
  -- see Translation Priority schema
  priority           integer NOT NULL,
  category           integer REFERENCES Label,
  UNIQUE (translationeffort , potemplate)
);




/*
  POSubscription
  Records the people who have subscribed to a POT File. They can
  subscribe to the POT file and get all the PO files, or just the PO
  files for a specific language.
*/
CREATE TABLE POSubscription (
  id                   serial PRIMARY KEY,
  person               integer NOT NULL REFERENCES Person,
  potemplate           integer NOT NULL REFERENCES POTemplate,
  language             integer REFERENCES Language,
  -- the frequency with which a user prefers to be
  -- sent the POFiles in the subscription. If NULL
  -- then send on demand.
  notificationinterval interval,
  -- the timestamp of the last time the user was
  -- sent the updated PO files from this
  -- subscription
  lastnotified         timestamp,
  -- a person can only have one subscription to a
  -- particular PO Template for a given language.
  UNIQUE ( person, potemplate, language )
);



/*
  MALONE. THE BUG TRACKING SYSTEM.
  This is the Launchpad subsystem that handles bug 
  tracking for all the distributions we know about.
*/


/*
  Bug
  The core bug entry.
*/
CREATE TABLE Bug (
  id                      serial PRIMARY KEY,
  datecreated             timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  nickname                text UNIQUE,
  title                   text NOT NULL,
  description             text NOT NULL,
  owner                   integer NOT NULL,
  duplicateof             integer REFERENCES Bug,
  communityscore          integer NOT NULL,
  communitytimestamp      timestamp NOT NULL,
  activityscore           integer NOT NULL,
  activitytimestamp       timestamp NOT NULL,
  hits                    integer NOT NULL,
  hitstimestamp           timestamp NOT NULL
);



/*
  BugSubscription
  The relationship between a person and a bug.
*/
CREATE TABLE BugSubscription (
  id             serial PRIMARY KEY,
  person         integer NOT NULL REFERENCES Person,
  bug            integer NOT NULL REFERENCES Bug,
  subscription   integer NOT NULL -- watch, cc, ignore
);



/*
  BugInfestation
  This is a bug status scorecard. It's not a global status for the
  bug, this is usually attached to a release, or a sourcepackage in
  a distro. So these tell you the status of a bug SOMEWHERE. The
  pointer to this tells you which bug, and on what thing (the 
  SOMEWHERE) the status is being described.
*/
CREATE TABLE BugInfestation (
  bug              integer NOT NULL REFERENCES Bug,
  coderelease      integer NOT NULL REFERENCES Coderelease,
  explicit         boolean NOT NULL,
  -- see Bug Infestation Status schema
  infestation      integer NOT NULL,
  datecreated      timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  creator          integer NOT NULL REFERENCES Person,
  dateverified     timestamp,
  verifiedby       integer REFERENCES Person,
  lastmodified     timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  lastmodifiedby   integer NOT NULL REFERENCES Person,
  PRIMARY KEY ( bug, coderelease )
);



/*
  SourcepackageBugAssignment
  The status of a bug with regard to a source package. This is different
  to the status on a specific release, because it includes the concept
  of workflow or prognosis ("what we intend to do with this bug") while
  the release bug status is static ("is the bug present or not").
*/
CREATE TABLE SourcepackageBugAssignment (
  id                 serial PRIMARY KEY,
  bug                integer NOT NULL REFERENCES Bug,
  sourcepackage      integer NOT NULL REFERENCES Sourcepackage,
  -- see Bug Assignment Status schema
  bugstatus          integer NOT NULL,
  -- See Bug Priority schema
  priority           integer NOT NULL,
  /* see BugSeverity schema, in theory this belongs on BugInfestation
     but it would be a UI challenge */
  severity           integer NOT NULL,
  binarypackage      integer REFERENCES Binarypackage,
  UNIQUE ( bug, sourcepackage )
);





/*
  ProductBugAssignment
  The status of a bug with regard to a product. This is different
  to the status on a specific release, because it includes the concept
  of workflow or prognosis ("what we intend to do with this bug") while
  the release bug status is static ("is the bug present or not").
*/
CREATE TABLE ProductBugAssignment (
  id                 serial PRIMARY KEY,
  bug                integer NOT NULL REFERENCES Bug,
  product            integer NOT NULL REFERENCES Sourcepackage,
  -- see Bug Assignment Status schema
  bugstatus          integer NOT NULL,
  -- see Bug Priority schema
  priority           integer NOT NULL,
  -- see Bug Severity schema
  severity           integer NOT NULL,
  UNIQUE ( bug, product )
);




/*
  BugActivity
  A log of all the things that have happened to a bug, as Dave wants
  to keep track of it.
*/
CREATE TABLE BugActivity (
  id            serial PRIMARY KEY,
  bug           integer NOT NULL REFERENCES Bug,
  datechanged   timestamp NOT NULL,
  person        integer NOT NULL,
  whatchanged   text NOT NULL,
  oldvalue      text NOT NULL,
  newvalue      text NOT NULL,
  message       text
);




/*
  BugExternalRef
  A table of external references for a bug, that are NOT remote
  bug system references, except where the remote bug system is
  not supported by the BugWatch table.
 XXX can we set the default timestamp to "now"
*/
CREATE TABLE BugExternalRef (
  id          serial PRIMARY KEY,
  bug         integer NOT NULL REFERENCES Bug,
  -- see the Bug External Reference Types schema
  bugreftype  integer NOT NULL,
  data        text NOT NULL,
  description text NOT NULL,
  datecreated timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  owner       integer NOT NULL REFERENCES Person
);



/*
  BugSystemType
  This is a table of bug tracking system types. We don't have much
  version granularity (Bugzilla 2.15 is treated the same as Bugzilla 2.17
  unless you create them as two separate bug system types). This table is
  used by the BugSystem table to indicate the type of a remote bug system.
*/
CREATE TABLE BugSystemType (
  id              serial PRIMARY KEY,
  name            text NOT NULL UNIQUE,
  title           text NOT NULL,
  description     text NOT NULL,
  homepage        text,
  -- the Launchpad person who knows most about these
  owner           integer NOT NULL REFERENCES Person
);


/*
  BugSystem
  A table of remote bug systems (for example, Debian's DebBugs, and
  Mozilla's Bugzilla, and SourceForge's tracker...). The baseurl is the
  top of the bug system's tree, from which the URL to a given bug
  status can be determined.
*/
CREATE TABLE BugSystem (
  id               serial PRIMARY KEY,
  bugsystemtype    integer NOT NULL REFERENCES BugSystemType,
  name             text NOT NULL,
  title            text NOT NULL,
  description      text NOT NULL,
  baseurl          text NOT NULL,
  owner            integer NOT NULL REFERENCES Person
);



/*
  BugWatch
  This is a table of bugs in remote bug systems (for example, upstream
  bugzilla instances) which we want to monitor for status changes.
*/
CREATE TABLE BugWatch (
  id               serial PRIMARY KEY,
  bug              integer NOT NULL REFERENCES Bug,
  bugsystem        integer NOT NULL REFERENCES BugSystem,
  remotebug        text NOT NULL, -- unique identifier of bug in that system
  remotestatus     text NOT NULL, -- textual representation of status
  lastchanged      timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  lastchecked      timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  datecreated      timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  owner            integer NOT NULL REFERENCES Person
);




/*
  ProjectBugsystem
  A link between the Project table and the Bugsystem table. This allows
  us to setup a bug system and then easily create watches once a bug
  has been assigned to an upstream product.
*/
CREATE TABLE ProjectBugSystem (
  project         integer NOT NULL REFERENCES Project,
  bugsystem       integer NOT NULL REFERENCES BugSystem,
  PRIMARY KEY ( project, bugsystem )
);
  


/*
  BugLabel
  Allows us to attach arbitrary metadata to a bug.
*/
CREATE TABLE BugLabel (
  bug       integer NOT NULL REFERENCES Bug,
  label     integer NOT NULL REFERENCES Label,
  PRIMARY KEY ( bug, label )
);




/*
  BugRelationship
  The relationship between two bugs, with a label.
*/
CREATE TABLE BugRelationship (
  subject        integer NOT NULL REFERENCES Bug,
  -- see the Bug Relationships schema
  label          integer NOT NULL,
  object         integer NOT NULL REFERENCES Bug
);



/*
  BugMessage
  A table of messages about bugs. Could be from the web
  forum, or from email, we don't care and treat them both
  equally. A message can apply to multiple forums.
*/
CREATE TABLE BugMessage (
  id                   serial PRIMARY KEY,
  bug                  integer NOT NULL REFERENCES Bug,
  datecreated          timestamp NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  -- short title or subject of comment / message
  title                text NOT NULL,
  -- the message or full email with headers
  contents             text NOT NULL,
  personmsg            integer REFERENCES Person, -- NULL if we don't know it
  parent               integer REFERENCES BugMessage, -- gives us threading
  distribution         integer REFERENCES Distribution,
  rfc822msgid          text
);


/*
  BugAttachment
  A table of attachments to BugMessages. These are typically patches,
  screenshots, mockups, or other documents. We need to ensure that only
  valid attachments get automatically added into the database, stripping
  
*/
CREATE TABLE BugAttachment (
  id              serial PRIMARY KEY,
  bugmessage      integer NOT NULL REFERENCES BugMessage,
  name            text,
  description     text,
  libraryfile     int NOT NULL REFERENCES LibraryFileAlias,
  datedeactivated timestamp
);




/* SourceSource
   A table of sources of source code from upstream locations.  This might be
   CVS, SVN or Arch repositories, or even a tarball of a CVS repository.
   This table is what defines the import daemon's work, for initial imports,
   sync jobs, and for finding new upstream releases.
*/
CREATE TABLE SourceSource (
  id	                    serial PRIMARY KEY,
  name                      text NOT NULL,
  title                     text NOT NULL,
  description               text NOT NULL,
  product                   integer NOT NULL REFERENCES Product,
  cvsroot                   text,
  cvsmodule                 text,
  cvstarfile                integer REFERENCES LibraryFileAlias,
  cvstarfileurl             text,
  cvsbranch                 text,
  svnrepository             text,
  -- The URL of the directory (usually FTP) where they have releases
  releaseroot               text,
  releaseverstyle           integer,
  releasefileglob           text,
  -- The arch branch from which these release tarballs may have been derived
  releaseparentbranch       integer REFERENCES Branch,
  sourcepackage             integer REFERENCES Sourcepackage,
  -- The arch branch this source is imported to
  branch                    integer REFERENCES Branch UNIQUE,
  -- NULL means never, i.e. this is an import job
  lastsynced                timestamp,
  syncinterval              interval,
  -- see Revision Control Systems schema
  rcstype                   integer NOT NULL,
  hosted                    text,
  upstreamname              text,
  processingapproved        timestamp,
  syncingapproved           timestamp,
  /* These columns are used to create new archives/branches in the DB based on
     values imported from .info files */
  newarchive                text,
  newbranchcategory         text,
  newbranchbranch           text,
  newbranchversion          text,
  packagedistro		    text,
  packagefiles_collapsed    text,
  owner                     integer NOT NULL REFERENCES Person
);


