
SET client_encoding = 'UNICODE';
SET check_function_bodies = false;

SET search_path = public, pg_catalog;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'person'::pg_catalog.regclass;

INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (18, 'Ubuntu Gnome Team', NULL, NULL, NULL, 1, 'This Team is responsible for the GNOME releases Issues on whole Ubuntu Distribution', 0, '2004-10-12 06:57:28.753737', 'name18', NULL, '''team'':3 ''gnome'':2 ''ubuntu'':1', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (5, 'Scott James Remnant', 'Scott James', 'Remnant', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'keybuk', NULL, '''jame'':2,5 ''scott'':1,4 ''remnant'':3,6', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (27, 'Daniel Henrique Debonzi', 'Daniel', 'Henrique', 'DAJs/l1RrrYFPPd2mBY4b/aFjnTfodXOyg+L+U6uPxUy8rCp/IFC/w==', NULL, NULL, 0, '2005-01-10 13:08:28.753737', 'debonzi', NULL, '''daniel'':1,3 ''debonzi'':5 ''henriqu'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (3, 'Dave Miller', 'Dave', 'Miller', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'justdave', NULL, '''dave'':1,3 ''miller'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (8, 'James Blackwell', 'James', 'Blackwell', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'jblack', NULL, '''jame'':1,3 ''blackwel'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (12, 'Sample Person', 'Sample', 'Person', 'K7Qmeansl6RbuPfulfcmyDQOzp70OxVh5Fcf', NULL, NULL, 30, '2004-10-12 06:57:28.753737', 'name12', NULL, '''sampl'':1,3 ''person'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (30, 'Rosetta Administrators', NULL, NULL, NULL, 25, 'Rosetta Administrators', 0, '2005-03-07 13:05:56.480934', 'rosetta-admins', NULL, '''rosetta'':1 ''administr'':2', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (20, 'Warty Security Team', NULL, NULL, NULL, 1, 'This Team is responsible for Security Issues on Warty Distribution Release', 0, '2004-10-12 06:57:28.753737', 'name20', NULL, '''team'':3 ''secur'':2 ''warti'':1', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (13, 'Carlos Perelló Marín', 'Carlos', 'Perelló Marín', 'MdB+BoAdbza3BA6mIkMm6bFo1kv9hR2PKZ3U', NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'carlos', NULL, '''carlo'':1,4 ''marín'':3,6 ''perelló'':2,5', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (29, 'Guilherme Salgado', 'Guilherme', 'Salgado', 'DAJs/l1RrrYFPPd2mBY4b/aFjnTfodXOyg+L+U6uPxUy8rCp/IFC/w==', NULL, NULL, 0, '2005-01-10 13:08:28.753737', 'salgado', NULL, '''salgado'':2,4 ''guilherm'':1,3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (14, 'Dafydd Harries', 'Dafydd', 'Harries', 'EvSuSe4k4tkRHSp6p+g91vyQIwL5VJ3iTbRZ', NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'daf', NULL, '''harri'':2,4 ''dafydd'':1,3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (25, 'Launchpad Administrators', NULL, NULL, NULL, 1, 'Launchpad Administrators', 0, '2004-12-13 18:08:27.2609', 'admins', NULL, '''administr'':2 ''launchpad'':1', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (31, 'Ubuntu Translators', NULL, NULL, NULL, 30, 'Ubuntu Translators', 0, '2005-03-07 13:05:57.563047', 'ubuntu-translators', NULL, '''ubuntu'':1 ''translat'':2', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (26, 'Daniel Silverstone', 'Daniel', 'Silverstone', NULL, NULL, NULL, 0, '2004-12-13 18:10:17.294019', 'kinnison', NULL, '''daniel'':1,3 ''silverston'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (10, 'Alexander Limi', 'Alexander', 'Limi', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'limi', NULL, '''limi'':2,4 ''alexand'':1,3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (1, 'Mark Shuttleworth', 'Mark', 'Shuttleworth', 'K7Qmeansl6RbuPfulfcmyDQOzp70OxVh5Fcf', NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'sabdfl', NULL, '''mark'':1,3 ''shuttleworth'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (22, 'Stuart Bishop', 'Stuart', 'Bishop', 'I+lQozEFEr+uBuxQZuKGpL4jkiy6lE1dQsZx', NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'stub', NULL, '''bishop'':2,4 ''stuart'':1,3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (16, 'Foo Bar', 'Foo', 'Bar', 'K7Qmeansl6RbuPfulfcmyDQOzp70OxVh5Fcf', NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'name16', NULL, '''bar'':2,4 ''foo'':1,3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (23, 'David Allouche', 'David', 'Allouche', NULL, NULL, NULL, 0, '2004-12-09 17:59:07.717254', 'ddaa', NULL, '''david'':1,3 ''allouch'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (9, 'Christian Reis', 'Christian', 'Reis', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'kiko', NULL, '''rei'':2,4 ''christian'':1,3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (28, 'Celso Providelo', 'Celso', 'Providelo', 'DAJs/l1RrrYFPPd2mBY4b/aFjnTfodXOyg+L+U6uPxUy8rCp/IFC/w==', NULL, NULL, 0, '2005-01-10 13:08:28.753737', 'cprov', NULL, '''celso'':1,3 ''providelo'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (2, 'Robert Collins', 'Robert', 'Collins', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'lifeless', NULL, '''collin'':2,4 ''robert'':1,3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (11, 'Steve Alexander', 'Steve', 'Alexander', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'stevea', NULL, '''steve'':1,3 ''alexand'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (4, 'Colin Watson', 'Colin', 'Watson', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'kamion', NULL, '''colin'':1,3 ''watson'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (6, 'Jeff Waugh', 'Jeff', 'Waugh', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'jdub', NULL, '''jeff'':1,3 ''waugh'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (19, 'Warty Gnome Team', NULL, NULL, NULL, 1, 'This Team is responsible for GNOME release Issues on Warty Distribution Release', 0, '2004-10-12 06:57:28.753737', 'name19', NULL, '''team'':3 ''gnome'':2 ''warti'':1', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (21, 'Hoary Gnome Team', NULL, NULL, NULL, 1, 'This team is responsible for Security Issues on Hoary Distribution Release', 0, '2004-10-12 06:57:28.753737', 'name21', NULL, '''team'':3 ''gnome'':2 ''hoari'':1', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (24, 'Buttress Source Administrators', NULL, NULL, NULL, 2, 'Ultimate control of the Buttress systems', 666, '2004-12-09 17:59:38.607384', 'buttsource', NULL, '''sourc'':2 ''buttress'':1 ''administr'':3', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (17, 'Ubuntu Team', NULL, NULL, NULL, 1, 'This Team is responsible for the Ubuntu Distribution', 0, '2004-10-12 06:57:28.753737', 'name17', NULL, '''team'':2 ''ubuntu'':1', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (7, 'Andrew Bennetts', 'Andrew', 'Bennetts', NULL, NULL, NULL, 0, '2004-10-12 06:57:28.753737', 'spiv', NULL, '''andrew'':1,3 ''bennett'':2,4', NULL, NULL, 1, NULL);
INSERT INTO person (id, displayname, givenname, familyname, "password", teamowner, teamdescription, karma, karmatimestamp, name, "language", fti, defaultmembershipperiod, defaultrenewalperiod, subscriptionpolicy, merged) VALUES (32, 'GuadaMen', NULL, NULL, NULL, 16, 'The guadalinex maintainers team', 0, '2005-04-16 04:37:00.815842', 'guadamen', NULL, '''guadamen'':1', 700, 300, 1, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'person'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'emailaddress'::pg_catalog.regclass;

INSERT INTO emailaddress (id, email, person, status) VALUES (7, 'steve.alexander@ubuntulinux.com', 11, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (8, 'colin.watson@ubuntulinux.com', 4, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (9, 'scott.james.remnant@ubuntulinux.com', 5, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (10, 'andrew.bennetts@ubuntulinux.com', 7, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (11, 'james.blackwell@ubuntulinux.com', 8, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (12, 'christian.reis@ubuntulinux.com', 9, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (13, 'jeff.waugh@ubuntulinux.com', 6, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (14, 'dave.miller@ubuntulinux.com', 3, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (17, 'testtest@canonical.com', 12, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (18, 'testtesttest@canonical.com', 12, 3);
INSERT INTO emailaddress (id, email, person, status) VALUES (20, 'stuart.bishop@canonical.com', 22, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (22, 'david@canonical.com', 23, 2);
INSERT INTO emailaddress (id, email, person, status) VALUES (23, 'daniel.debonzi@canonical.com', 27, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (24, 'celso.providelo@canonical.com', 28, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (25, 'guilherme.salgado@canonical.com', 29, 1);
INSERT INTO emailaddress (id, email, person, status) VALUES (1, 'mark@hbd.com', 1, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (2, 'robertc@robertcollins.net', 2, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (3, 'carlos@canonical.com', 13, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (4, 'daf@canonical.com', 14, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (6, 'foo.bar@canonical.com', 16, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (21, 'david.allouche@canonical.com', 23, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (5, 'lalo@canonical.com', 15, 3);
INSERT INTO emailaddress (id, email, person, status) VALUES (15, 'justdave@bugzilla.org', 3, 3);
INSERT INTO emailaddress (id, email, person, status) VALUES (16, 'test@canonical.com', 12, 4);
INSERT INTO emailaddress (id, email, person, status) VALUES (19, 'testing@canonical.com', 12, 2);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'emailaddress'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'gpgkey'::pg_catalog.regclass;

INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (1, 1, '09F89725', 'XVHJOU77IYTD0982FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (2, 11, '09F89890', 'XVHJOU77IYTD0981FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (3, 10, '09F89321', 'XVHJOU77IYTD0983FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (4, 8, '09F89098', 'XVHJOU77IYTD0984FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (5, 9, '09F89123', 'XVHJOU77IYTD0985FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (6, 4, '09F89124', 'XVHJOU77IYTA0985FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (7, 5, '09F89125', 'XVHJOU77IYTQ0985FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (8, 7, '09F89126', 'XVHJOU77IYTX0985FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (9, 3, '09F89127', 'XVHJOU77IYTZ0985FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (10, 6, '09F89120', 'XVHJOU77IYTP0985FTG6OQFC0GF809POQW45MJ76', '<-- sample pubkey ??? -->', false, 17, 1024);
INSERT INTO gpgkey (id, "owner", keyid, fingerprint, pubkey, revoked, algorithm, keysize) VALUES (11, 28, '681B6469', 'C85826521A6EF6A6037BB3F79FF2583E681B6469', '<-- sample pubkey ??? -->', false, 17, 1024);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'gpgkey'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'archuserid'::pg_catalog.regclass;

INSERT INTO archuserid (id, person, archuserid) VALUES (1, 1, 'mark.shuttleworth');
INSERT INTO archuserid (id, person, archuserid) VALUES (2, 11, 'steve.alexander');
INSERT INTO archuserid (id, person, archuserid) VALUES (3, 10, 'alexander.limi');
INSERT INTO archuserid (id, person, archuserid) VALUES (4, 8, 'james.blackwell');
INSERT INTO archuserid (id, person, archuserid) VALUES (5, 9, 'christian.reis');
INSERT INTO archuserid (id, person, archuserid) VALUES (6, 4, 'colin.watson');
INSERT INTO archuserid (id, person, archuserid) VALUES (7, 5, 'scott.james.remnant');
INSERT INTO archuserid (id, person, archuserid) VALUES (8, 7, 'andrew.bennetts');
INSERT INTO archuserid (id, person, archuserid) VALUES (9, 3, 'dave.miller');
INSERT INTO archuserid (id, person, archuserid) VALUES (10, 6, 'jeff.waugh');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'archuserid'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'wikiname'::pg_catalog.regclass;

INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (1, 1, 'http://www.ubuntulinux.com/wiki/', 'MarkShuttleworth');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (2, 11, 'http://www.ubuntulinux.com/wiki/', 'SteveAlexander');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (3, 10, 'http://www.ubuntulinux.com/wiki/', 'AlexanderLimi');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (4, 8, 'http://www.ubuntulinux.com/wiki/', 'JamesBlackwell');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (5, 9, 'http://www.ubuntulinux.com/wiki/', 'ChristianReis');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (6, 4, 'http://www.ubuntulinux.com/wiki/', 'ColinWatson');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (7, 5, 'http://www.ubuntulinux.com/wiki/', 'ScottJamesRemnant');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (8, 7, 'http://www.ubuntulinux.com/wiki/', 'AndrewBennetts');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (9, 3, 'http://www.ubuntulinux.com/wiki/', 'DaveMiller');
INSERT INTO wikiname (id, person, wiki, wikiname) VALUES (10, 6, 'http://www.ubuntulinux.com/wiki/', 'JeffWaugh');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'wikiname'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'jabberid'::pg_catalog.regclass;

INSERT INTO jabberid (id, person, jabberid) VALUES (1, 1, 'markshuttleworth@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (2, 11, 'stevea@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (3, 10, 'limi@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (4, 8, 'jblack@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (5, 9, 'kiko@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (6, 4, 'colin@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (7, 5, 'scott@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (8, 7, 'spiv@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (9, 3, 'justdave@jabber.org');
INSERT INTO jabberid (id, person, jabberid) VALUES (10, 6, 'jeff@jabber.org');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'jabberid'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'ircid'::pg_catalog.regclass;

INSERT INTO ircid (id, person, network, nickname) VALUES (1, 1, 'irc.freenode.net', 'mark');
INSERT INTO ircid (id, person, network, nickname) VALUES (2, 11, 'irc.freenode.net', 'SteveA');
INSERT INTO ircid (id, person, network, nickname) VALUES (3, 10, 'irc.freenode.net', 'limi');
INSERT INTO ircid (id, person, network, nickname) VALUES (4, 8, 'irc.freenode.net', 'jblack');
INSERT INTO ircid (id, person, network, nickname) VALUES (5, 3, 'irc.freenode.net', 'justdave');
INSERT INTO ircid (id, person, network, nickname) VALUES (6, 9, 'irc.freenode.net', 'kiko');
INSERT INTO ircid (id, person, network, nickname) VALUES (7, 4, 'irc.freenode.net', 'Kamion');
INSERT INTO ircid (id, person, network, nickname) VALUES (8, 5, 'irc.freenode.net', 'Keybuk');
INSERT INTO ircid (id, person, network, nickname) VALUES (9, 6, 'irc.freenode.net', 'jeff');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'ircid'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'teammembership'::pg_catalog.regclass;

INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (1, 1, 17, 3, '2005-03-03 10:02:53.830191', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (2, 11, 17, 2, '2005-03-03 10:02:53.831231', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (3, 10, 17, 3, '2005-03-03 10:02:53.831725', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (4, 4, 17, 3, '2005-03-03 10:02:53.832216', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (5, 7, 17, 1, '2005-03-03 10:02:53.832809', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (6, 3, 17, 6, '2005-03-03 10:02:53.833299', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (7, 1, 18, 5, '2005-03-03 10:02:53.833759', '2005-03-13 10:02:53.833759', NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (8, 6, 18, 5, '2005-03-03 10:02:53.834248', '2005-03-13 10:02:53.833759', NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (9, 20, 17, 1, '2005-03-03 10:02:53.834789', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (10, 11, 18, 3, '2005-03-03 10:02:53.835303', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (11, 10, 18, 2, '2005-03-03 10:02:53.835792', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (12, 4, 18, 5, '2005-03-03 10:02:53.836299', '2005-03-13 10:02:53.833759', NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (13, 7, 18, 2, '2005-03-03 10:02:53.8368', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (14, 3, 18, 1, '2005-03-03 10:02:53.837284', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (15, 20, 18, 4, '2005-03-03 10:02:53.837789', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (16, 6, 17, 3, '2005-03-03 10:02:53.838301', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (17, 16, 17, 3, '2005-03-03 10:02:53.838806', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (18, 16, 18, 3, '2005-03-03 10:02:53.839322', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (19, 23, 24, 3, '2005-03-03 10:02:53.839822', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (20, 2, 24, 3, '2005-03-03 10:02:53.840339', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (21, 28, 25, 2, '2005-03-03 10:02:53.840813', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (22, 22, 25, 2, '2005-03-03 10:02:53.841292', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (23, 2, 25, 2, '2005-03-03 10:02:53.841836', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (24, 11, 25, 2, '2005-03-03 10:02:53.842335', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (25, 23, 25, 2, '2005-03-03 10:02:53.842821', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (26, 7, 25, 2, '2005-03-03 10:02:53.843319', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (27, 8, 25, 2, '2005-03-03 10:02:53.843811', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (28, 14, 25, 2, '2005-03-03 10:02:53.844315', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (29, 13, 25, 2, '2005-03-03 10:02:53.844834', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (30, 26, 25, 2, '2005-03-03 10:02:53.84533', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (31, 27, 25, 2, '2005-03-03 10:02:53.845844', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (32, 16, 25, 3, '2005-03-03 10:02:53.846352', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (33, 29, 25, 3, '2005-03-03 10:02:53.846864', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (34, 14, 30, 3, '2005-03-07 13:05:57.590333', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (35, 13, 30, 3, '2005-03-07 13:05:57.610314', NULL, NULL, NULL);
INSERT INTO teammembership (id, person, team, status, datejoined, dateexpires, reviewer, reviewercomment) VALUES (36, 16, 24, 2, '2005-04-14 00:00:00', NULL, 16, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'teammembership'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'teamparticipation'::pg_catalog.regclass;

INSERT INTO teamparticipation (id, team, person) VALUES (1, 17, 1);
INSERT INTO teamparticipation (id, team, person) VALUES (2, 17, 11);
INSERT INTO teamparticipation (id, team, person) VALUES (3, 17, 10);
INSERT INTO teamparticipation (id, team, person) VALUES (4, 17, 4);
INSERT INTO teamparticipation (id, team, person) VALUES (5, 18, 11);
INSERT INTO teamparticipation (id, team, person) VALUES (6, 18, 10);
INSERT INTO teamparticipation (id, team, person) VALUES (7, 18, 7);
INSERT INTO teamparticipation (id, team, person) VALUES (8, 17, 6);
INSERT INTO teamparticipation (id, team, person) VALUES (9, 17, 16);
INSERT INTO teamparticipation (id, team, person) VALUES (10, 18, 16);
INSERT INTO teamparticipation (id, team, person) VALUES (11, 24, 23);
INSERT INTO teamparticipation (id, team, person) VALUES (12, 24, 2);
INSERT INTO teamparticipation (id, team, person) VALUES (13, 25, 28);
INSERT INTO teamparticipation (id, team, person) VALUES (14, 25, 22);
INSERT INTO teamparticipation (id, team, person) VALUES (15, 25, 2);
INSERT INTO teamparticipation (id, team, person) VALUES (16, 25, 11);
INSERT INTO teamparticipation (id, team, person) VALUES (17, 25, 23);
INSERT INTO teamparticipation (id, team, person) VALUES (18, 25, 7);
INSERT INTO teamparticipation (id, team, person) VALUES (19, 25, 8);
INSERT INTO teamparticipation (id, team, person) VALUES (20, 25, 14);
INSERT INTO teamparticipation (id, team, person) VALUES (21, 25, 13);
INSERT INTO teamparticipation (id, team, person) VALUES (22, 25, 26);
INSERT INTO teamparticipation (id, team, person) VALUES (23, 25, 27);
INSERT INTO teamparticipation (id, team, person) VALUES (24, 25, 16);
INSERT INTO teamparticipation (id, team, person) VALUES (25, 25, 29);
INSERT INTO teamparticipation (id, team, person) VALUES (26, 30, 14);
INSERT INTO teamparticipation (id, team, person) VALUES (27, 30, 13);
INSERT INTO teamparticipation (id, team, person) VALUES (28, 2, 2);
INSERT INTO teamparticipation (id, team, person) VALUES (29, 5, 5);
INSERT INTO teamparticipation (id, team, person) VALUES (30, 26, 26);
INSERT INTO teamparticipation (id, team, person) VALUES (31, 27, 27);
INSERT INTO teamparticipation (id, team, person) VALUES (32, 29, 29);
INSERT INTO teamparticipation (id, team, person) VALUES (33, 3, 3);
INSERT INTO teamparticipation (id, team, person) VALUES (34, 8, 8);
INSERT INTO teamparticipation (id, team, person) VALUES (35, 10, 10);
INSERT INTO teamparticipation (id, team, person) VALUES (36, 13, 13);
INSERT INTO teamparticipation (id, team, person) VALUES (37, 14, 14);
INSERT INTO teamparticipation (id, team, person) VALUES (38, 23, 23);
INSERT INTO teamparticipation (id, team, person) VALUES (39, 9, 9);
INSERT INTO teamparticipation (id, team, person) VALUES (40, 1, 1);
INSERT INTO teamparticipation (id, team, person) VALUES (41, 15, 15);
INSERT INTO teamparticipation (id, team, person) VALUES (42, 22, 22);
INSERT INTO teamparticipation (id, team, person) VALUES (43, 16, 16);
INSERT INTO teamparticipation (id, team, person) VALUES (44, 28, 28);
INSERT INTO teamparticipation (id, team, person) VALUES (45, 7, 7);
INSERT INTO teamparticipation (id, team, person) VALUES (46, 6, 6);
INSERT INTO teamparticipation (id, team, person) VALUES (47, 11, 11);
INSERT INTO teamparticipation (id, team, person) VALUES (48, 4, 4);
INSERT INTO teamparticipation (id, team, person) VALUES (49, 12, 12);
INSERT INTO teamparticipation (id, team, person) VALUES (58, 24, 16);
INSERT INTO teamparticipation (id, team, person) VALUES (59, 32, 16);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'teamparticipation'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = '"schema"'::pg_catalog.regclass;

INSERT INTO "schema" (id, name, title, description, "owner", extensible) VALUES (2, 'schema', 'SCHEMA', 'description', 1, true);
INSERT INTO "schema" (id, name, title, description, "owner", extensible) VALUES (3, 'trema', 'XCHEMA', 'description', 1, true);
INSERT INTO "schema" (id, name, title, description, "owner", extensible) VALUES (4, 'enema', 'ENHEMA', 'description', 1, true);
INSERT INTO "schema" (id, name, title, description, "owner", extensible) VALUES (1, 'mark', 'TITLE', 'description', 1, true);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = '"schema"'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'label'::pg_catalog.regclass;

INSERT INTO label (id, "schema", name, title, description) VALUES (1, 1, 'blah', 'blah', 'blah');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'label'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'personlabel'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'personlabel'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'project'::pg_catalog.regclass;

INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (7, 16, 'aaa', 'the Test Project', 'The Test Project', 'This is a small project that has no purpose by to serve as a test data point. The only thing this project has ever produced is products, most of which are largely unheard of. This short description is long enough.', 'Of course, one can''t say enough about the Test Project. Not only is it always there, it''s often exactly in the same state that you saw it last. And it has an amazing ability to pop up in places where you just didn''t think you''d expect to find it. Very noticeable when you least want it noticed, that sort of thing.

It would be very interesting to know whether this second paragraph of text about the test project is in fact rendered as a second paragraph, or if it all blurs together in a haze of testing. Only time will tell.', '2004-10-03 22:27:25.02843', 'http://www.testmenow.com', NULL, NULL, NULL, NULL, false, true, '''d'':96 ''aaa'':1 ''one'':50 ''pop'':85 ''saw'':75 ''say'':53 ''abil'':83 ''amaz'':82 ''blur'':142 ''data'':23 ''didn'':92 ''ever'':31 ''fact'':132 ''find'':99 ''haze'':146 ''know'':119 ''larg'':39 ''last'':77 ''long'':46 ''serv'':19 ''sort'':110 ''tell'':152 ''test'':3,6,22,57,128,148 ''text'':125 ''time'':150 ''want'':106 ''alway'':63 ''cours'':49 ''exact'':68 ''least'':105 ''notic'':102,108 ''often'':67 ''place'':88 ''point'':24 ''short'':43 ''small'':11 ''state'':72 ''thing'':27,112 ''think'':94 ''would'':114 ''enough'':47,54 ''expect'':97 ''produc'':32 ''purpos'':16 ''render'':133 ''second'':122,136 ''togeth'':143 ''product'':34 ''project'':4,7,12,29,58,129 ''unheard'':40 ''whether'':120 ''descript'':44 ''interest'':117 ''paragraph'':123,137');
INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (2, 2, 'do-not-use-info-imports', 'DO NOT USE', 'DO NOT USE', 'DO NOT USE', 'TEMPORARY project till mirror jobs are assigned to correct project', '2004-09-24 20:58:00.637677', 'http://arch.ubuntu.com/', NULL, NULL, NULL, NULL, true, false, '''job'':20 ''use'':4,9,12,15 ''info'':5 ''till'':18 ''assign'':22 ''import'':6 ''mirror'':19 ''correct'':24 ''project'':17,25 ''temporari'':16 ''do-not-use-info-import'':1');
INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (5, 12, 'gnome', 'GNOME', 'The GNOME Project', 'The GNOME Project is an initiative to prduce a free desktop software framework. GNOME is more than a set of applications, it is a user interface standard (the Gnome HIG) and a set of libraries that allow applications to work together in a harmonious desktop-ish way.', 'The Gnome Project was founded (when?) to build on the success of early applications using the Gtk GUI toolkit. Many of those applications are still part of Gnome, and the Gtk toolkit remains an essential part of Gnome.

Gnome applications cover the full spectrum from office productivity applications to games, digital camera applications, and of course the Gnome Panel which acts as a launcher and general access point for apps on the desktop.', '2004-09-24 20:58:02.222154', 'http://www.gnome.org/', NULL, NULL, NULL, NULL, false, true, '''act'':114 ''app'':123 ''gtk'':70,84 ''gui'':71 ''hig'':35 ''ish'':52 ''set'':24,38 ''use'':68 ''way'':53 ''free'':15 ''full'':96 ''game'':103 ''mani'':73 ''part'':79,89 ''user'':30 ''work'':45 ''allow'':42 ''build'':61 ''cours'':109 ''cover'':94 ''digit'':104 ''earli'':66 ''found'':58 ''gnome'':1,2,4,7,19,34,55,81,91,92,111 ''initi'':11 ''offic'':99 ''panel'':112 ''point'':121 ''still'':78 ''access'':120 ''applic'':26,43,67,76,93,101,106 ''camera'':105 ''prduce'':13 ''remain'':86 ''togeth'':46 ''desktop'':16,51,126 ''essenti'':88 ''general'':119 ''harmoni'':49 ''librari'':40 ''product'':100 ''project'':5,8,56 ''softwar'':17 ''success'':64 ''toolkit'':72,85 ''interfac'':31 ''launcher'':117 ''spectrum'':97 ''standard'':32 ''framework'':18 ''desktop-ish'':50');
INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (8, 16, 'gimp', 'the GiMP Project', 'The GIMP Project', 'The GIMP Project works in the field of image manipulation and reproduction. The Project is responsible for several pieces of software, such as The GiMP and GiMP-Print.', 'Founded by Spencer Kimball in 1996 with the simple aim of producing a "paint" program, the GIMP project has become one of the defining projects of the open source world. The GIMP itself is an image manipulation program that is beginning to rival even Adobe Photoshop in features and functionality.

The project is loosely organised, with about 15 people making regular contributions. There is no fixed release schedule other than "when it is done".', '2004-10-03 22:27:45.283741', 'http://www.gimp.org/', NULL, NULL, NULL, NULL, false, true, '''15'':94 ''aim'':46 ''fix'':102 ''one'':57 ''1996'':42 ''adob'':81 ''done'':110 ''even'':80 ''gimp'':1,3,6,9,32,35,53,68 ''imag'':16,72 ''loos'':90 ''make'':96 ''open'':64 ''piec'':26 ''work'':11 ''becom'':56 ''begin'':77 ''defin'':60 ''field'':14 ''found'':37 ''paint'':50 ''peopl'':95 ''print'':36 ''rival'':79 ''sever'':25 ''simpl'':45 ''sourc'':65 ''world'':66 ''featur'':84 ''kimbal'':40 ''produc'':48 ''releas'':103 ''manipul'':17,73 ''organis'':91 ''program'':51,74 ''project'':4,7,10,21,54,61,88 ''regular'':97 ''respons'':23 ''schedul'':104 ''softwar'':28 ''spencer'':39 ''function'':86 ''contribut'':98 ''photoshop'':82 ''reproduct'':19 ''gimp-print'':34');
INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (1, 1, 'ubuntu', 'the Ubuntu Project', 'The Ubuntu Project', 'A community Linux distribution building a slick desktop for the global market. Ubuntu is absolutely free and will stay that way, contains no proprietary application software, always ships with the latest Gnome desktop software and Python integration.', 'The Ubuntu Project aims to create a freely redistributable OS that is easy to customize and derive from. Ubuntu is released every six months with contributions from a large community, especially the Gnome Project. While the full range of KDE and other desktop environments are available, Ubuntu''s Gnome desktop receives most of the polish and support work done for each release.

Ubuntu also includes work to unify the translation of common open source desktop applications and the tracking of bugs across multiple distributions.', '2004-09-24 20:58:00.633513', 'http://www.ubuntulinux.org/', NULL, NULL, NULL, NULL, false, true, '''os'':54 ''aim'':48 ''bug'':125 ''kde'':84 ''six'':67 ''way'':28 ''also'':108 ''done'':103 ''easi'':57 ''free'':23 ''full'':81 ''larg'':73 ''open'':117 ''rang'':82 ''ship'':35 ''stay'':26 ''work'':102,110 ''alway'':34 ''avail'':90 ''build'':12 ''creat'':50 ''deriv'':61 ''everi'':66 ''gnome'':39,77,93 ''linux'':10 ''month'':68 ''slick'':14 ''sourc'':118 ''track'':123 ''unifi'':112 ''across'':126 ''applic'':32,120 ''common'':116 ''commun'':9,74 ''custom'':59 ''especi'':75 ''freeli'':52 ''global'':18 ''includ'':109 ''integr'':44 ''latest'':38 ''market'':19 ''polish'':99 ''python'':43 ''receiv'':95 ''releas'':65,106 ''ubuntu'':1,3,6,20,46,63,91,107 ''absolut'':22 ''contain'':29 ''desktop'':15,40,87,94,119 ''environ'':88 ''multipl'':127 ''project'':4,7,47,78 ''softwar'':33,41 ''support'':101 ''translat'':114 ''contribut'':70 ''distribut'':11,128 ''proprietari'':31 ''redistribut'':53');
INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (6, 12, 'iso-codes', 'iso-codes', 'iso-codes', 'foo', 'bar', '2004-09-24 20:58:02.238443', 'http://www.gnome.org/', NULL, NULL, NULL, NULL, false, true, '''bar'':11 ''foo'':10 ''iso'':2,5,8 ''code'':3,6,9 ''iso-cod'':1,4,7');
INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (3, 2, 'launchpad-mirrors', 'Launchpad SCM Mirrors', 'The Launchpad Mirroring Project', 'launchpad mirrors various revision control archives, that mirroring is managed here', 'A project to mirror revision control archives into Arch.', '2004-09-24 20:58:00.65398', 'http://arch.ubuntu.com/', NULL, NULL, NULL, NULL, false, true, '''scm'':5 ''arch'':30 ''manag'':20 ''revis'':14,26 ''archiv'':16,28 ''mirror'':3,6,9,12,18,25 ''control'':15,27 ''project'':10,23 ''various'':13 ''launchpad'':2,4,8,11 ''launchpad-mirror'':1');
INSERT INTO project (id, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, wikiurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti) VALUES (4, 12, 'mozilla', 'the Mozilla Project', 'The Mozilla Project', 'The Mozilla Project is the largest open source web browser collaborative project. Founded when Netscape released the source code to its pioneering browser in 1999, the Mozilla Project continues to set the standard for web browser technology.', 'The Mozilla Project produces several internet applications that are very widely used, and is also a center for collaboration on internet standards work by open source groups.

The Project now has several popular products, including the Firefox web browser, the Thunderbird mail client and the libraries that enable them to run on many platforms.

Organisationally, the Mozilla Project is hosted by the Mozilla Foundation, a not-for-profit company incorporated in the US.', '2004-09-24 20:58:02.177698', 'http://www.mozilla.org/', NULL, NULL, NULL, NULL, false, true, '''us'':118 ''run'':95 ''set'':38 ''use'':56 ''web'':16,42,82 ''1999'':32 ''also'':59 ''code'':26 ''host'':104 ''mail'':86 ''mani'':97 ''open'':14,69 ''wide'':55 ''work'':67 ''enabl'':92 ''found'':20 ''group'':71 ''sever'':49,76 ''sourc'':15,25,70 ''applic'':51 ''center'':61 ''client'':87 ''includ'':79 ''produc'':48 ''profit'':113 ''releas'':23 ''browser'':17,30,43,83 ''compani'':114 ''continu'':36 ''firefox'':81 ''foundat'':108 ''largest'':13 ''librari'':90 ''mozilla'':1,3,6,9,34,46,101,107 ''netscap'':22 ''organis'':99 ''pioneer'':29 ''popular'':77 ''product'':78 ''project'':4,7,10,19,35,47,73,102 ''collabor'':18,63 ''incorpor'':115 ''internet'':50,65 ''platform'':98 ''standard'':40,66 ''technolog'':44 ''thunderbird'':85 ''not-for-profit'':110');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'project'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'projectrelationship'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'projectrelationship'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'product'::pg_catalog.regclass;

INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (9, 5, 16, 'applets', 'Gnome Applets', 'The Gnome Panel Applets', 'The Gnome Panel Applets are a collection of standard widgets that can be installed on your desktop Panel. These icons act as launchers for applications, or indicators of the status of your machine. For example, panel applets exist to show you your battery status or wifi network signal strength.', 'This is the collection of Panel Applets that is part of the default Gnome release. Additional Panel Applets are available from third parties. A complete set of Panel Applets is included in the Ubuntu OS, for example.

The Gnome Panel team includes Abel Kascinsky, Frederick Wurst and Andreas Andropovitch Axelsson.', '2004-10-03 16:46:09.113721', 'http://www.gnome.org/panel/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''os'':91 ''act'':28 ''set'':82 ''abel'':99 ''icon'':27 ''part'':66 ''show'':47 ''team'':97 ''wifi'':53 ''addit'':72 ''avail'':76 ''exist'':45 ''gnome'':2,5,9,70,95 ''indic'':34 ''panel'':6,10,25,43,62,73,84,96 ''parti'':79 ''third'':78 ''wurst'':102 ''andrea'':104 ''applet'':1,3,7,11,44,63,74,85 ''applic'':32 ''exampl'':42,93 ''includ'':87,98 ''instal'':21 ''machin'':40 ''releas'':71 ''signal'':55 ''status'':37,51 ''ubuntu'':90 ''widget'':17 ''batteri'':50 ''collect'':14,60 ''complet'':81 ''default'':69 ''desktop'':24 ''network'':54 ''axelsson'':106 ''launcher'':30 ''standard'':16 ''strength'':56 ''frederick'':101 ''kascinski'':100 ''andropovitch'':105', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (3, 3, 2, 'arch-mirrors', 'Arch mirrors', 'Arch archive mirrors', 'Arch Archive Mirroring project.', 'Arch archive full-archive mirror tasks', '2004-09-24 20:58:00.691047', 'http://arch.ubuntu.com/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''arch'':2,4,6,9,13 ''full'':16 ''task'':19 ''archiv'':7,10,14,17 ''mirror'':3,5,8,11,18 ''project'':12 ''full-arch'':15 ''arch-mirror'':1', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (2, 2, 2, 'unassigned', 'unassigned syncs', 'unassigned syncs', 'syncs still not assigned to a real product', 'unassigned syncs, will not be processed, to be moved to real projects ASAP.', '2004-09-24 20:58:00.674409', 'http://arch.ubuntu.com/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, false, '''asap'':26 ''move'':22 ''real'':12,24 ''sync'':3,5,6,15 ''still'':7 ''assign'':9 ''process'':19 ''product'':13 ''project'':25 ''unassign'':1,2,4,14', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (8, 4, 12, 'thunderbird', 'Mozilla Thunderbird', 'Mozilla Thunderbird', 'The Mozilla Thunderbird email client', 'The Mozilla Thunderbird email client', '2004-09-24 20:58:04.478988', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''email'':9,14 ''client'':10,15 ''mozilla'':2,4,7,12 ''thunderbird'':1,3,5,8,13', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (5, 5, 12, 'evolution', 'Evolution', 'The Evolution Groupware Application', 'Evolution is an email client, addressbook and calendar application that is very well integrated with the Gnome desktop. Evolution is the standard mail client in the Ubuntu distribution, and supports all current mail system standards.', 'Recently, Evolution has seen significant work to make it interoperable with the proprietary Microsoft Exchange Server protocols and formats, allowing organisations to replace Outlook on Windows with Evolution and Linux.

The current stable release series of Evolution is 2.0.', '2004-09-24 20:58:02.240163', 'http://www.gnome.org/evolution/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''2.0'':80 ''mail'':29,39 ''make'':49 ''seen'':45 ''seri'':76 ''well'':19 ''work'':47 ''allow'':61 ''email'':10 ''gnome'':23 ''linux'':71 ''stabl'':74 ''applic'':6,15 ''client'':11,30 ''evolut'':1,2,4,7,25,43,69,78 ''format'':60 ''integr'':20 ''recent'':42 ''releas'':75 ''replac'':64 ''server'':57 ''system'':40 ''ubuntu'':33 ''window'':67 ''current'':38,73 ''desktop'':24 ''exchang'':56 ''organis'':62 ''outlook'':65 ''support'':36 ''calendar'':14 ''groupwar'':5 ''protocol'':58 ''signific'':46 ''standard'':28,41 ''distribut'':34 ''interoper'':51 ''microsoft'':55 ''addressbook'':12 ''proprietari'':54', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (4, 4, 12, 'firefox', 'Mozilla Firefox', 'Mozilla Firefox', 'The Mozilla Firefox web browser', 'The Mozilla Firefox web browser', '2004-09-24 20:58:02.185708', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''web'':9,14 ''browser'':10,15 ''firefox'':1,3,5,8,13 ''mozilla'':2,4,7,12', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (10, NULL, 2, 'python-gnome2-dev', 'python gnome2 dev', 'python gnome2 dev', 'Python bindings for the GNOME desktop environment', 'Python bindings for the GNOME desktop environment', '2004-09-24 20:58:00.674409', 'http://www.daa.com.au/~james/software/pygtk/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, true, false, '''dev'':4,7,10 ''bind'':12,19 ''gnome'':15,22 ''gnome2'':3,6,9 ''python'':2,5,8,11,18 ''desktop'':16,23 ''environ'':17,24 ''python-gnome2-dev'':1', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (6, 5, 12, 'gnome-terminal', 'GNOME Terminal', 'The GNOME Terminal Emulator', 'Gnome Terminal is a simple terminal application for your Gnome desktop. It allows quick access to console applications, supports all console types, and has many useful features such as tabbed consoles (many consoles in a single window with quick switching between them).', 'The Gnome Terminal application fully supports Gnome 2 and is a standard part of the Gnome Desktop.', '2004-09-24 20:58:02.256678', 'http://www.gnome.org/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''2'':59 ''tab'':39 ''use'':35 ''emul'':9 ''mani'':34,41 ''part'':64 ''type'':31 ''allow'':22 ''fulli'':56 ''gnome'':2,4,7,10,19,53,58,67 ''quick'':23,48 ''simpl'':14 ''singl'':45 ''access'':24 ''applic'':16,27,55 ''consol'':26,30,40,42 ''featur'':36 ''switch'':49 ''termin'':3,5,8,11,15,54 ''window'':46 ''desktop'':20,68 ''support'':28,57 ''standard'':63 ''gnome-termin'':1', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (11, 5, 12, 'netapplet', 'NetApplet', 'Network Applet', 'The Novell Network Applet', 'Displays current network status and allows network switching', '2005-03-10 16:00:00', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''allow'':14 ''novel'':6 ''applet'':4,8 ''status'':12 ''switch'':16 ''current'':10 ''display'':9 ''network'':3,7,11,15 ''netapplet'':1,2', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (12, NULL, 16, 'a52dec', 'a52dec', 'Liba52 Test Decoder', 'a52dec is a test program for liba52.', 'This tool decodes ATSC A/52 streams, and also includes a demultiplexer for mpeg-1 and mpeg-2 program streams. The liba52 source code is always distributed in the a52dec package, to make sure it easier for people to test it.', '2005-04-14 00:00:00', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''1'':27 ''2'':31 ''a/52'':17 ''also'':20 ''atsc'':16 ''code'':37 ''make'':46 ''mpeg'':26,30 ''sure'':47 ''test'':4,9,53 ''tool'':14 ''alway'':39 ''decod'':5,15 ''peopl'':51 ''sourc'':36 ''a52dec'':1,2,6,43 ''easier'':49 ''includ'':21 ''liba52'':3,12,35 ''mpeg-1'':25 ''mpeg-2'':29 ''packag'':44 ''stream'':18,33 ''program'':10,32 ''distribut'':40 ''demultiplex'':23', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (1, 1, 17, 'ubuntu', 'Ubuntu', 'Ubuntu', 'An easy-to-install version of Linux that has a complete set of desktop applications ready to use immediately after installation.', 'Ubuntu is a desktop Linux that you can give your girlfriend to install. Works out of the box with recent Gnome desktop applications configured to make you productive immediately. Ubuntu is updated every six months, comes with security updates for peace of mind, and is available everywhere absolutely free of charge.', '2004-09-24 20:58:00.655518', 'http://www.ubuntu.com/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''box'':43 ''set'':16 ''six'':59 ''use'':22 ''come'':61 ''easi'':6 ''free'':74 ''give'':34 ''make'':51 ''mind'':68 ''peac'':66 ''work'':39 ''avail'':71 ''charg'':76 ''everi'':58 ''gnome'':46 ''linux'':11,30 ''month'':60 ''readi'':20 ''secur'':63 ''updat'':57,64 ''applic'':19,48 ''immedi'':23,54 ''instal'':8,25,38 ''recent'':45 ''ubuntu'':1,2,3,26,55 ''absolut'':73 ''complet'':15 ''desktop'':18,29,47 ''product'':53 ''version'':9 ''configur'':49 ''everywher'':72 ''girlfriend'':36 ''easy-to-instal'':5', false);
INSERT INTO product (id, project, "owner", name, displayname, title, shortdesc, description, datecreated, homepageurl, screenshotsurl, wikiurl, listurl, programminglang, downloadurl, lastdoap, sourceforgeproject, freshmeatproject, reviewed, active, fti, autoupdate) VALUES (7, 6, 12, 'iso-codes', 'iso-codes', 'The iso-codes', 'foo', 'bar', '2004-09-24 20:58:02.258743', 'http://www.novell.com/', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, true, '''bar'':12 ''foo'':11 ''iso'':2,5,9 ''code'':3,6,10 ''iso-cod'':1,4,8', false);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'product'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productlabel'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productlabel'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productseries'::pg_catalog.regclass;

INSERT INTO productseries (id, product, name, displayname, shortdesc, branch, importstatus, datelastsynced, syncinterval, rcstype, cvsroot, cvsmodule, cvsbranch, cvstarfileurl, svnrepository, bkrepository, releaseroot, releasefileglob, releaseverstyle, targetarcharchive, targetarchcategory, targetarchbranch, targetarchversion, dateautotested, dateprocessapproved, datesyncapproved, datestarted, datefinished) VALUES (1, 4, 'milestones', 'Milestone Releases', 'The Firefox milestone releases are development releases aimed at testing new features in the developer community. They are not intended for widespread end-user adoption, except among the very brave.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO productseries (id, product, name, displayname, shortdesc, branch, importstatus, datelastsynced, syncinterval, rcstype, cvsroot, cvsmodule, cvsbranch, cvstarfileurl, svnrepository, bkrepository, releaseroot, releasefileglob, releaseverstyle, targetarcharchive, targetarchcategory, targetarchbranch, targetarchversion, dateautotested, dateprocessapproved, datesyncapproved, datestarted, datefinished) VALUES (2, 4, '1.0', 'Mozilla Firefox', 'The 1.0 branch of the Mozilla web browser. Currently, this is the stable branch of Mozilla, and all stable releases are made off this branch.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO productseries (id, product, name, displayname, shortdesc, branch, importstatus, datelastsynced, syncinterval, rcstype, cvsroot, cvsmodule, cvsbranch, cvstarfileurl, svnrepository, bkrepository, releaseroot, releasefileglob, releaseverstyle, targetarcharchive, targetarchcategory, targetarchbranch, targetarchversion, dateautotested, dateprocessapproved, datesyncapproved, datestarted, datefinished) VALUES (5, 11, 'releases', 'NetApplet Releases', 'Releases of Network Applet', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO productseries (id, product, name, displayname, shortdesc, branch, importstatus, datelastsynced, syncinterval, rcstype, cvsroot, cvsmodule, cvsbranch, cvstarfileurl, svnrepository, bkrepository, releaseroot, releasefileglob, releaseverstyle, targetarcharchive, targetarchcategory, targetarchbranch, targetarchversion, dateautotested, dateprocessapproved, datesyncapproved, datestarted, datefinished) VALUES (6, 12, 'main', 'MAIN', 'The primary upstream development branch, from which all releases are made.', NULL, 2, NULL, NULL, 1, ':pserver:anonymous@cvs.sourceforge.net:/cvsroot/liba52', 'a52dec', 'MAIN', NULL, '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO productseries (id, product, name, displayname, shortdesc, branch, importstatus, datelastsynced, syncinterval, rcstype, cvsroot, cvsmodule, cvsbranch, cvstarfileurl, svnrepository, bkrepository, releaseroot, releasefileglob, releaseverstyle, targetarcharchive, targetarchcategory, targetarchbranch, targetarchversion, dateautotested, dateprocessapproved, datesyncapproved, datestarted, datefinished) VALUES (3, 5, 'main', 'MAIN', 'The primary "trunk" of development for this product. This series
was automatically created and represents the idea of a primary trunk
of software development without "stable branches". For most
products, releases in this series will be "milestone" or "test"
releases, and there should be other series for the stable releases
of the product.', 14, 5, NULL, NULL, 1, ':pserver:anonymous@anoncvs.gnome.org:/cvs/gnome', 'evolution', 'MAIN', '', '', NULL, '', '', NULL, 'gnome@arch.ubuntu.com', 'evolution', 'MAIN', '0', NULL, NULL, NULL, NULL, NULL);
INSERT INTO productseries (id, product, name, displayname, shortdesc, branch, importstatus, datelastsynced, syncinterval, rcstype, cvsroot, cvsmodule, cvsbranch, cvstarfileurl, svnrepository, bkrepository, releaseroot, releasefileglob, releaseverstyle, targetarcharchive, targetarchcategory, targetarchbranch, targetarchversion, dateautotested, dateprocessapproved, datesyncapproved, datestarted, datefinished) VALUES (4, 8, 'main', 'MAIN', 'The primary "trunk" of development for this product. This series
was automatically created and represents the idea of a primary trunk
of software development without "stable branches". For most
products, releases in this series will be "milestone" or "test"
releases, and there should be other series for the stable releases
of the product.', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productseries'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productrelease'::pg_catalog.regclass;

INSERT INTO productrelease (id, datereleased, "version", title, description, changelog, "owner", shortdesc, productseries, manifest) VALUES (6, '2005-02-28 00:00:00', '2.1.6', NULL, NULL, 'Bugzilla bugs fixed (see http://bugzilla.ximian.com/show_bug.cgi):

 * Addressbook
   #73005 - Cannot cancel ''Contact List Editor'' (Siva)
   #73005 - offline - setting/unsetting folder offline property is not working (Sushma)
   #70371 - Evolution crashes when adding contact list (Siva)
   #67724 - When unix user name, callendar points to old username (Siva)
   #54825 - Freeze on .vcf import from MacOS X AddressBook (Christophe Fergeau)
   #73013 - ''Right'' click on a ''Contact'' cannot select ''Cut'' (Siva)

 * Calendar
   #72958 - Unable to send delayed meeting (Chen)
   #72006 - Opened existing appointments with attachment - press cancel - popup info with save / discard / cancel changes (Chen)
   #63866 - Same name can be entered twice in invitations tab (JP)
   #67714 - Invitations Tab Allows Entry Of Empty Line (JP)
   #62089 - adding contact lists to meetings impossible (JP)
   #47747 - Changes to attendee not updated until click on different row (JP)
   #61495 - Existing text is placed off screen when editing attendee field (JP)
   #28947 - adding contact list to attendee list should expand it (JP)
   #67724 - When unix user name, callendar points to old username (Siva)
   #72038 - Changes meeting to appoinment after throwing warning invalid mail id (Rodrigo)
   #69556 - Crash attaching mime parts to calendar events (Harish)

 * Mail
   #66126 - attach File Chooser is modal (Michael)
   #68549 - Answering to Usenet article doesn''t consider the "Followup-To:" field (Michael)
   #71003 - threads still running at exit (Michael)
   #62109 - Inconsistent ways of determining 8-bit Subject: and From: header charsets (Jeff)
   #34153 - Confusing Outbox semantics for deleted outgoing messages (Michael)
   #71528 - Search Selection Widget Has Repeated Items (Michael)
   #71967 - Evolution delete mail from POP3 server even is checked the option "leave the mail on server (Michael)
   #40515 - Signature scripts do not allow switches (Michael)
   #68866 - Forward button doesn''t put newline between headers and body (Michael)
   #35219 - flag-for-followup crufting (Michael)
   #64987 - Go to next unread message doesn''t work when multiple messages are selected (Michael)
   #72337 - Evolution crashes if I click OK/Cancel on the password dialog after disabling the IMAP account (Michael)
   #70718 - Next and previous buttons don''t realize there''s new mail (Michael)
   #61363 - Setup wizard, IMAP for receiving server, sending default GW (Michael)
   #70795 - Next/Previous Message Should Only Display Listed Emails (Michael)
   #23822 - no copy text option when right-clicking on marked mail text (Rodney)
   #72266 - You shouldn''t be able to open more than one ''Select Folder'' dialog in the mail filters (Michael)
   #71429 - on NLD, menus in wrong order (Michae)l
   #72228 - cannot store into groupwise sent folder (Michael)
   #72209 - Evolution is crashing when you move a VFolder to a folder ''on this computer'' (Michael)
   #72275 - Can''t use Shift+F10 to popup context menu for link in message (Harry Lu)
   #54503 - "New" dropdown menu on toolbar has wrong widget style (Rodney)
   #72676 - Saved filter rule can''t be modified if it is selected with GOK. (Harry Lu)

 * SMIME
   #68592 - "Backup" buttons in certificate settings does nothing - work around (Michael)

 * Shell
   #33287 - "send/receive" button not greyed out when starting offline (JP)
   #48868 - Status bar changes its height when fonts are large (William Jon McCann)

 * Plugins
   #71527 - Save Calendar widget mixup between directory and file (Rodrigo)

Other bugs

 * Addressbook
   - Use new categories dialog in contact editor (Rodrigo)
   - HIG spacing fixes (Rodney)
   - Display warning dialog when GW server is old (Vivek)

 * Calendar
   - Always ensure default sources are available (Siva)
   - Don''t look up free/busy unless we need to (Harish)
   - Make sure new events don''t display twice (Chen)
   - Make sure double click opens attachments (Chen)

 * Mail
   - a11y fixes for composer (Harry Lu)
   - Use gnome-vfs API to launch external applications (Marco Pesenti Gritti)
   - New mailer context menus for messages (Rodney)

 * Shell
   - Fix leak (JP)
   - Use gnome-vfs API to open quick reference (Marco Pesenti Gritti)

 * Plugins
   - Make e-popup more robust (Michael)
   - Cleanup authors/descriptions (Björn Torkelsson)
   - out of office exchange fixes (Sushma)
   - retry send options if invalid session string (Chen)
   - set proper default port for shared folders (Vivek)

 * Miscellaneous
   - BSD runtime linking fixes (Hans)
   - distclean fixes (Björn Torkelsson)

Updated translations:
   - et (Priit Laes)
   - el (Kostas Papadimas, Nikos Charonitakis)
   - sv (Christian Rose)
   - es (Francisco Javier F. Serrador)
   - it (Luca Ferretti, Marco Ciampa)
   - da (Martin Willemoes Hansen)
   - ca (Josep Puigdemont, Xavi Conde)
   - nb (Kjartan Maraas)
   - no (Kjartan Maraas)
   - ru (Leonid Kanter)
   - gu (Ankit Patel)
   - cs (Miloslav Trmac)
   - nl (Vincent van Adrighem)
   - fi (Ilkka Tuohela)
   - pt (Duarte Loreto)
   - uk (Maxim Dziumanenko)
   - ko (Changwoo Ryu)
   - de (Frank Arnold)
   - fr (Vincent Carriere)
   - en_CA (Adam Weinberger)
   - cs (Miloslav Trmac)
   - pl (Artur Flinta)
   - bg (Vladimir Petkov)
   - ja (Takeshi AIHANA)
   - en_GB (David Lodge)
   - en_CA (Adam Weinberger)
   - lt (Zygimantas Berucka)', 12, NULL, 3, NULL);
INSERT INTO productrelease (id, datereleased, "version", title, description, changelog, "owner", shortdesc, productseries, manifest) VALUES (2, '2004-06-28 00:00:00', '0.8', NULL, NULL, NULL, 12, NULL, 4, NULL);
INSERT INTO productrelease (id, datereleased, "version", title, description, changelog, "owner", shortdesc, productseries, manifest) VALUES (7, '2005-03-10 16:20:00', '1.0', NULL, NULL, NULL, 12, NULL, 5, NULL);
INSERT INTO productrelease (id, datereleased, "version", title, description, changelog, "owner", shortdesc, productseries, manifest) VALUES (5, '2004-10-15 18:32:35.717695', '0.9.2', 'One (secure) Tree Hill', 'Security fixes

    * 250180 - [Windows] Disallow access to insecure shell: protocol.
', NULL, 16, 'This was a security fix release for 0.9.', 1, 1);
INSERT INTO productrelease (id, datereleased, "version", title, description, changelog, "owner", shortdesc, productseries, manifest) VALUES (4, '2004-10-15 18:31:19.164989', '0.9.1', 'One Tree Hill (v2)', '', NULL, 16, 'This was a bugfix release to patch up problems with the new extension system.', 1, 2);
INSERT INTO productrelease (id, datereleased, "version", title, description, changelog, "owner", shortdesc, productseries, manifest) VALUES (3, '2004-10-15 18:27:09.878302', '0.9', 'One Tree Hill', 'What''s New

Here''s what''s new in this release of Firefox:

    * New Default Theme

      An updated Default Theme now presents a uniform appearance across all three platforms - a new crisp, clear look for Windows users. Finetuning for GNOME will follow in future releases.
    * Comprehensive Data Migration

      Switching to Firefox has never been easier now that Firefox imports data like Favorites, History, Settings, Cookies and Passwords from Internet Explorer. Firefox can also import from Mozilla 1.x, Netscape 4.x, 6.x and 7.x, and Opera. MacOS X and Linux migrators for browsers like Safari, OmniWeb, Konqueror etc. will arrive in future releases.
    * Extension/Theme Manager

      New Extension and Theme Managers provide a convenient way to manage and update your add-ons. SmartUpdate also notifies you of updates to Firefox.
    * Smaller Download

      Windows users will find Firefox is now only 4.7MB to download.
    * Help

      A new online help system is available.
    * Lots of bug fixes and improvements

      Copy Image, the ability to delete individual items from Autocomplete lists, SMB/SFTP support on GNOME via gnome-vfs, better Bookmarks, Search and many other refinements fine tune the browsing experience.

For Linux/GTK2 Users

    * Installer

      Firefox now comes with an installer for Linux/GTK2 users. The new installer makes the installation process much simpler.
    * Look and Feel Updates

      Ongoing improvements have been made to improve the way Firefox adheres to your GTK2 themes, such as menus.
    * Talkback for GTK2

      Help us nail down crashes by submitting talkback reports with this crash reporting tool.

', NULL, 16, 'Release 0.9 of Firefox introduced a new theme as well as improved migration tools for people switching to Firefox.', 1, 3);
INSERT INTO productrelease (id, datereleased, "version", title, description, changelog, "owner", shortdesc, productseries, manifest) VALUES (1, '2004-06-28 00:00:00', '1.0.0', 'First Stable Release', '', '', 12, 'After four years of work the Mozilla project makes its first public stable release. Mozilla 1.0.0 is a major milestone in open source history.', 2, 4);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productrelease'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productcvsmodule'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productcvsmodule'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productbkbranch'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productbkbranch'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productsvnmodule'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productsvnmodule'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'archarchive'::pg_catalog.regclass;

INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (2, 'thunderbird@arch.ubuntu.com', 'Thunderbid', 'text', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (3, 'twisted@arch.ubuntu.com', 'Twisted', 'text', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (4, 'bugzilla@arch.ubuntu.com', 'Bugzilla', 'text', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (5, 'arch@arch.ubuntu.com', 'Arch', 'text', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (6, 'kiwi2@arch.ubuntu.com', 'Kiwi2', 'text', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (7, 'plone@arch.ubuntu.com', 'Plone', 'text', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (8, 'gnome@arch.ubuntu.com', 'GNOME', 'The GNOME Project', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (9, 'iso-codes@arch.ubuntu.com', 'iso-codes', 'The iso-codes', false, NULL);
INSERT INTO archarchive (id, name, title, description, visible, "owner") VALUES (1, 'mozilla@arch.ubuntu.com', 'Mozilla', 'text', false, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'archarchive'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'archarchivelocation'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'archarchivelocation'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'archarchivelocationsigner'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'archarchivelocationsigner'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'archnamespace'::pg_catalog.regclass;

INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (1, 1, 'mozilla', NULL, NULL, true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (2, 2, 'tunderbird', NULL, NULL, true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (3, 3, 'twisted', NULL, NULL, true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (4, 4, 'bugzila', NULL, NULL, true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (5, 5, 'arch', NULL, NULL, true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (6, 6, 'kiwi2', NULL, NULL, true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (7, 7, 'plone', NULL, NULL, true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (8, 8, 'gnome', 'evolution', '2.0', false);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (9, 9, 'iso-codes', 'iso-codes', '0.35', false);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (10, 1, 'mozilla', 'release', '0.9.2', true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (11, 1, 'mozilla', 'release', '0.9.1', true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (12, 1, 'mozilla', 'release', '0.9', true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (13, 1, 'mozilla', 'release', '0.8', true);
INSERT INTO archnamespace (id, archarchive, category, branch, "version", visible) VALUES (14, 8, 'evolution', 'MAIN', '0', true);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'archnamespace'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'branch'::pg_catalog.regclass;

INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (3, 3, 'Python Twisted 0.9.1', 'text', 7, NULL);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (4, 4, 'Bugzila 0.9.1', 'text', 3, NULL);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (5, 5, 'Arch 0.9.1', 'text', 8, NULL);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (6, 6, 'Kiwi2 0.9.1', 'text', 9, NULL);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (7, 7, 'Plone 0.9.1', 'text', 10, NULL);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (1, 1, 'Mozilla Firefox 0.9.1', 'text', 1, 4);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (2, 2, 'Mozilla Thunderbird 0.9.1', 'text', 11, 8);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (9, 9, 'Iso-codes 0.35', 'text', 13, 7);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (8, 8, 'Evolution 2.0', 'text', 13, 5);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (10, 10, 'Mozilla Firefox 0.9.2', 'text', 1, 4);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (11, 11, 'Mozilla Firefox 0.9.1', 'text', 1, 4);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (12, 12, 'Mozilla Firefox 0.9', 'text', 1, 4);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (13, 13, 'Mozilla Firefox 0.8', 'text', 1, 4);
INSERT INTO branch (id, archnamespace, title, description, "owner", product) VALUES (14, 14, 'Evolution HEAD', 'text', 1, 5);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'branch'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'changeset'::pg_catalog.regclass;

INSERT INTO changeset (id, branch, datecreated, name, logmessage, archid, gpgkey) VALUES (1, 10, '2005-03-09 15:45:00', 'base-0', 'Import of Mozilla Firefox 0.9.2', NULL, NULL);
INSERT INTO changeset (id, branch, datecreated, name, logmessage, archid, gpgkey) VALUES (2, 11, '2005-03-09 15:50:00', 'base-0', 'Import of Mozilla Firefox 0.9.1', NULL, NULL);
INSERT INTO changeset (id, branch, datecreated, name, logmessage, archid, gpgkey) VALUES (3, 12, '2005-03-09 15:55:00', 'base-0', 'Import of Mozilla Firefox 0.9', NULL, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'changeset'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'changesetfilename'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'changesetfilename'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'changesetfile'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'changesetfile'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'changesetfilehash'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'changesetfilehash'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'branchrelationship'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'branchrelationship'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'branchlabel'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'branchlabel'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productbranchrelationship'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productbranchrelationship'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'manifest'::pg_catalog.regclass;

INSERT INTO manifest (id, datecreated, uuid) VALUES (1, '2005-03-09 15:50:00', '24fce331-655a-4e17-be55-c718c7faebd0');
INSERT INTO manifest (id, datecreated, uuid) VALUES (2, '2005-03-09 15:55:00', 'bf819b15-10b3-4d1e-9963-b787753e8fb2');
INSERT INTO manifest (id, datecreated, uuid) VALUES (3, '2005-03-09 16:00:00', '2a18a3f1-eec5-4b72-b23c-fb46c8c12a88');
INSERT INTO manifest (id, datecreated, uuid) VALUES (4, '2005-03-09 16:05:00', '97b4ece8-b3c5-4e07-b529-6c76b59a5455');
INSERT INTO manifest (id, datecreated, uuid) VALUES (14, '2005-03-24 00:00:00', 'e0451064-b405-4f52-b387-ebfc1a7ee297');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'manifest'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'manifestentry'::pg_catalog.regclass;

INSERT INTO manifestentry (id, manifest, "sequence", branch, changeset, entrytype, "path", patchon, dirname) VALUES (1, 1, 1, 10, 1, 4, 'firefox-0.9.2.tar.gz', NULL, 'firefox-0.9.2/');
INSERT INTO manifestentry (id, manifest, "sequence", branch, changeset, entrytype, "path", patchon, dirname) VALUES (2, 2, 1, 11, 2, 4, 'firefox-0.9.1.tar.gz', NULL, 'firefox-0.9.1/');
INSERT INTO manifestentry (id, manifest, "sequence", branch, changeset, entrytype, "path", patchon, dirname) VALUES (3, 2, 2, NULL, NULL, 1, 'firefox-0.9.1.tar.gz/random/', NULL, NULL);
INSERT INTO manifestentry (id, manifest, "sequence", branch, changeset, entrytype, "path", patchon, dirname) VALUES (4, 3, 1, 12, 3, 5, 'firefox-0.9.zip', NULL, 'firefox-0.9/');
INSERT INTO manifestentry (id, manifest, "sequence", branch, changeset, entrytype, "path", patchon, dirname) VALUES (5, 3, 2, 12, NULL, 6, 'firefox-0.9_unix.patch', 1, 'firefox-0.9_unix/');
INSERT INTO manifestentry (id, manifest, "sequence", branch, changeset, entrytype, "path", patchon, dirname) VALUES (6, 4, 1, 13, NULL, 3, 'firefox-0.8.ar', NULL, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'manifestentry'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'archconfig'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'archconfig'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'archconfigentry'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'archconfigentry'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'processorfamily'::pg_catalog.regclass;

INSERT INTO processorfamily (id, name, title, description, "owner") VALUES (1, 'x86', 'Intel 386 compatible chips', 'Bring back the 8086!', 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'processorfamily'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'processor'::pg_catalog.regclass;

INSERT INTO processor (id, family, name, title, description, "owner") VALUES (1, 1, '386', 'Intel 386', 'Intel 386 and its many derivatives and clones, the basic 32-bit chip in the x86 family', 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'processor'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'builder'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'builder'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'component'::pg_catalog.regclass;

INSERT INTO component (id, name) VALUES (1, 'main');
INSERT INTO component (id, name) VALUES (2, 'restricted');
INSERT INTO component (id, name) VALUES (3, 'universe');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'component'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'section'::pg_catalog.regclass;

INSERT INTO section (id, name) VALUES (1, 'default_section');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'section'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'distribution'::pg_catalog.regclass;

INSERT INTO distribution (id, name, title, description, domainname, "owner", lucilleconfig, displayname, summary, members) VALUES (1, 'ubuntu', 'Ubuntu Linux', 'Ubuntu is a new
approach to Linux Distribution that includes regular releases, and a
simplified single-CD installation system.', 'ubuntulinux.org', 17, NULL, 'ubuntu', 'Ubuntu is a new
approach to Linux Distribution that includes regular releases, and a
simplified single-CD installation system.', 1);
INSERT INTO distribution (id, name, title, description, domainname, "owner", lucilleconfig, displayname, summary, members) VALUES (2, 'redhat', 'Redhat Advanced Server', 'Red Hat is a
commercial distribution of the GNU/Linux Operating System.', 'redhat.com', 1, NULL, 'redhat', 'Red Hat is a
commercial distribution of the GNU/Linux Operating System.', 1);
INSERT INTO distribution (id, name, title, description, domainname, "owner", lucilleconfig, displayname, summary, members) VALUES (3, 'debian', 'Debian GNU/Linux', 'Debian GNU/Linux is
a non commercial distribution of a GNU/Linux Operating System for many
platforms.', 'debian.org', 1, NULL, 'debian', 'Debian GNU/Linux is
a non commercial distribution of a GNU/Linux Operating System for many
platforms.', 1);
INSERT INTO distribution (id, name, title, description, domainname, "owner", lucilleconfig, displayname, summary, members) VALUES (4, 'gentoo', 'The Gentoo Linux', 'Gentoo is a very
customizeable GNU/Linux Distribution that is designed to let you build every
single package yourself, with your own preferences.', 'gentoo.org', 1, NULL, 'gentoo', 'Gentoo is a very
customizeable GNU/Linux Distribution that is designed to let you build every
single package yourself, with your own preferences.', 1);
INSERT INTO distribution (id, name, title, description, domainname, "owner", lucilleconfig, displayname, summary, members) VALUES (5, 'kubuntu', 'Kubuntu - Free KDE-based Linux', 'Kubuntu is an entirely free Linux distribution that uses the K Desktop
Environment as its default desktop after install.', 'kubuntu.org', 1, NULL, 'kubuntu', 'Kubuntu is an entirely free Linux distribution that uses the K Desktop
Environment as its default desktop after install.', 1);
INSERT INTO distribution (id, name, title, description, domainname, "owner", lucilleconfig, displayname, summary, members) VALUES (7, 'guadalinex', 'GuadaLinex: Linux for Andalucia', 'GuadaLinex is based on Ubuntu and adds full support for applications specific to the local environment in Andalucia.', 'guadalinex.es', 4, NULL, 'GuadaLinex', 'The GuadaLinex team produces a high quality linux for the Andalucian marketplace.', 32);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'distribution'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'distrorelease'::pg_catalog.regclass;

INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (1, 1, 'warty', 'The Warty Warthog
Release', 'Warty was the first stable release of Ubuntu. Key feature goals
included releasing on time, with the latest version of the Gnome Desktop
Environment, and the creation of all the infrastructure required to manage
Ubuntu itself. Warty includes excellent support for Python, with most of the
widely used Python libraries installed by default.', '4.10', 1, 1, 4, '2004-08-20 00:00:00', NULL, 17, NULL, 'Warty is the first release of Ubuntu,
with a planned release date of October 2004.', 'warty');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (2, 2, 'six', 'Six Six Six', 'some text to describe the whole 666 release of RH', '6.0.1', 1, 1, 4, '2004-03-21 00:00:00', NULL, 8, NULL, 'some text to describe the whole 666 release of RH', 'six');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (3, 1, 'hoary', 'The Hoary Hedgehog Release', 'Hoary is the second release of Ubuntu. Key feature goals include the integration of Hoary with the Launchpad for bugs and translation information, as well as Gnome 2.10 and the X.org window system.', '5.04', 1, 1, 2, '2004-08-25 00:00:00', 1, 1, NULL, 'Hoary is the second released of Ubuntu, with release planned for April 2005.', 'hoary');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (4, 2, '7.0', 'Seven', 'The release that we would not expect', '7.0.1', 1, 1, 3, '2004-04-01 00:00:00', 2, 7, NULL, 'The release that we would not expect', '7.0');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (6, 3, 'woody', 'WOODY', 'WOODY is the current stable verison of Debian GNU/Linux', '3.0', 1, 1, 4, '2003-01-01 00:00:00', NULL, 2, NULL, 'WOODY is the current stable verison of Debian GNU/Linux', 'woody');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (7, 3, 'sarge', 'Sarge', 'Sarge is the FROZEN unstable version of Debian GNU/Linux.', '3.1', 1, 1, 3, '2004-09-29 00:00:00', 6, 5, NULL, 'Sarge is the FROZEN unstable version of Debian GNU/Linux.', 'sarge');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (8, 3, 'sid', 'Sid', 'Sid is the CRAZY unstable version of Debian GNU/Linux.', '3.2', 1, 1, 1, '2004-12-29 00:00:00', 6, 6, NULL, 'Sid is the CRAZY unstable version of Debian GNU/Linux.', 'sid');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (5, 1, 'grumpy', 'The Grumpy
Groundhog Release', 'Grumpy, the third release of Ubuntu Linux, is not yet
in active development. This information is purely a placeholder.', '5.10', 1, 1, 1, '2004-08-29 00:00:00', 1, 1, NULL, 'Grumpy is the third release of
Ubuntu, planned for October 2005.', 'grumpy');
INSERT INTO distrorelease (id, distribution, name, title, description, "version", components, sections, releasestatus, datereleased, parentrelease, "owner", lucilleconfig, shortdesc, displayname) VALUES (9, 7, '2k5', 'Guada 2005', 'This release places extra emphasis on usability and installability. The installer is adapted from Ubuntu to assume your country, language, keyboard and time zone preference, thus ensuring that installs ask the minimum number of questions possible.', '2005', 1, 1, 2, NULL, 3, 4, NULL, 'Guada 2005 is a rapid-install version of
Ubuntu Hoary for the Andalucian marketplace.', 'Guada2005');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'distrorelease'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'distroarchrelease'::pg_catalog.regclass;

INSERT INTO distroarchrelease (id, distrorelease, processorfamily, architecturetag, "owner", chroot) VALUES (1, 1, 1, 'i386', 1, NULL);
INSERT INTO distroarchrelease (id, distrorelease, processorfamily, architecturetag, "owner", chroot) VALUES (6, 3, 1, 'i386', 1, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'distroarchrelease'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'libraryfilecontent'::pg_catalog.regclass;

INSERT INTO libraryfilecontent (id, datecreated, datemirrored, filesize, sha1) VALUES (1, '2005-04-07 16:46:05.265391', NULL, 178859, '378b3498ead213d35a82033a6e9196014a5ef25c');
INSERT INTO libraryfilecontent (id, datecreated, datemirrored, filesize, sha1) VALUES (2, '2005-04-07 16:46:05.266763', NULL, 9922560, 'a57faa6287aee2c58e115673a119c6083d31d1b9');
INSERT INTO libraryfilecontent (id, datecreated, datemirrored, filesize, sha1) VALUES (3, '2005-04-07 16:46:05.26727', NULL, 309386, 'b218ca7b52fa813550e3f14cdcf3ba68606e4446');
INSERT INTO libraryfilecontent (id, datecreated, datemirrored, filesize, sha1) VALUES (4, '2005-04-07 16:46:05.267803', NULL, 162927750, 'cfbd3ee1f510c66d49be465b900a3334e8488184');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'libraryfilecontent'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'libraryfilealias'::pg_catalog.regclass;

INSERT INTO libraryfilealias (id, content, filename, mimetype, expires) VALUES (1, 1, 'netapplet-1.0.0.tar.gz', 'application/x-gtar', NULL);
INSERT INTO libraryfilealias (id, content, filename, mimetype, expires) VALUES (2, 1, 'netapplet_1.0.0.orig.tar.gz', 'application/x-gtar', NULL);
INSERT INTO libraryfilealias (id, content, filename, mimetype, expires) VALUES (3, 2, 'firefox-0.9.2.tar.gz', 'application/x-gtar', NULL);
INSERT INTO libraryfilealias (id, content, filename, mimetype, expires) VALUES (4, 3, 'evolution-1.0.tar.gz', 'application/x-gtar', NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'libraryfilealias'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productreleasefile'::pg_catalog.regclass;

INSERT INTO productreleasefile (productrelease, libraryfile, filetype, id) VALUES (7, 1, 1, 1);
INSERT INTO productreleasefile (productrelease, libraryfile, filetype, id) VALUES (5, 3, 1, 2);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productreleasefile'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'sourcepackagename'::pg_catalog.regclass;

INSERT INTO sourcepackagename (id, name) VALUES (1, 'mozilla-firefox');
INSERT INTO sourcepackagename (id, name) VALUES (9, 'evolution');
INSERT INTO sourcepackagename (id, name) VALUES (10, 'netapplet');
INSERT INTO sourcepackagename (id, name) VALUES (14, 'pmount');
INSERT INTO sourcepackagename (id, name) VALUES (15, 'a52dec');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'sourcepackagename'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'packaging'::pg_catalog.regclass;

INSERT INTO packaging (packaging, id, sourcepackagename, distrorelease, productseries) VALUES (1, 1, 1, 3, 2);
INSERT INTO packaging (packaging, id, sourcepackagename, distrorelease, productseries) VALUES (1, 2, 9, 3, 3);
INSERT INTO packaging (packaging, id, sourcepackagename, distrorelease, productseries) VALUES (1, 4, 9, 1, 3);
INSERT INTO packaging (packaging, id, sourcepackagename, distrorelease, productseries) VALUES (1, 3, 10, 1, 5);
INSERT INTO packaging (packaging, id, sourcepackagename, distrorelease, productseries) VALUES (1, 6, 10, 3, 5);
INSERT INTO packaging (packaging, id, sourcepackagename, distrorelease, productseries) VALUES (1, 7, 15, 1, 6);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'packaging'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'sourcepackagerelease'::pg_catalog.regclass;

INSERT INTO sourcepackagerelease (id, creator, "version", dateuploaded, urgency, dscsigningkey, component, changelog, builddepends, builddependsindep, architecturehintlist, dsc, section, manifest, maintainer, sourcepackagename, uploaddistrorelease, format) VALUES (14, 1, '0.9', '2004-09-27 11:57:13', 1, 1, 1, 'Mozilla dummy Changelog......', 'gcc-3.4-base, libc6 (>= 2.3.2.ds1-4), gcc-3.4 (>= 3.4.1-4sarge1), gcc-3.4 (<< 3.4.2), libstdc++6-dev (>= 3.4.1-4sarge1)', 'bacula-common (= 1.34.6-2), bacula-director-common (= 1.34.6-2), postgresql-client (>= 7.4)', NULL, NULL, 1, NULL, 1, 1, 3, 1);
INSERT INTO sourcepackagerelease (id, creator, "version", dateuploaded, urgency, dscsigningkey, component, changelog, builddepends, builddependsindep, architecturehintlist, dsc, section, manifest, maintainer, sourcepackagename, uploaddistrorelease, format) VALUES (15, 1, '1.0', '2004-09-27 11:57:13', 1, NULL, 1, NULL, NULL, NULL, NULL, NULL, 1, NULL, 1, 9, 3, 1);
INSERT INTO sourcepackagerelease (id, creator, "version", dateuploaded, urgency, dscsigningkey, component, changelog, builddepends, builddependsindep, architecturehintlist, dsc, section, manifest, maintainer, sourcepackagename, uploaddistrorelease, format) VALUES (16, 1, '1.0-1', '2005-03-10 16:30:00', 1, NULL, 1, NULL, NULL, NULL, NULL, NULL, 1, NULL, 1, 10, 3, 1);
INSERT INTO sourcepackagerelease (id, creator, "version", dateuploaded, urgency, dscsigningkey, component, changelog, builddepends, builddependsindep, architecturehintlist, dsc, section, manifest, maintainer, sourcepackagename, uploaddistrorelease, format) VALUES (17, 1, '0.99.6-1', '2005-03-14 18:00:00', 1, NULL, 1, NULL, NULL, NULL, NULL, NULL, 1, NULL, 1, 10, 1, 1);
INSERT INTO sourcepackagerelease (id, creator, "version", dateuploaded, urgency, dscsigningkey, component, changelog, builddepends, builddependsindep, architecturehintlist, dsc, section, manifest, maintainer, sourcepackagename, uploaddistrorelease, format) VALUES (20, 1, '0.1-1', '2005-03-24 20:59:31.439579', 1, NULL, 1, NULL, NULL, NULL, NULL, NULL, 1, 14, 1, 14, 3, 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'sourcepackagerelease'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'sourcepackagereleasefile'::pg_catalog.regclass;

INSERT INTO sourcepackagereleasefile (sourcepackagerelease, libraryfile, filetype, id) VALUES (16, 2, 1, 1);
INSERT INTO sourcepackagereleasefile (sourcepackagerelease, libraryfile, filetype, id) VALUES (15, 4, 1, 2);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'sourcepackagereleasefile'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'build'::pg_catalog.regclass;

INSERT INTO build (id, datecreated, processor, distroarchrelease, buildstate, datebuilt, buildduration, buildlog, builder, gpgsigningkey, changes, sourcepackagerelease) VALUES (2, '2004-09-27 11:57:13', 1, 1, 1, '2004-09-27 11:57:13', NULL, NULL, NULL, NULL, 'Sample changes :)....', 14);
INSERT INTO build (id, datecreated, processor, distroarchrelease, buildstate, datebuilt, buildduration, buildlog, builder, gpgsigningkey, changes, sourcepackagerelease) VALUES (7, '2005-03-24 00:00:00', 1, 6, 1, NULL, NULL, NULL, NULL, NULL, 'changes', 20);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'build'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'binarypackagename'::pg_catalog.regclass;

INSERT INTO binarypackagename (id, name) VALUES (8, 'mozilla-firefox');
INSERT INTO binarypackagename (id, name) VALUES (13, 'pmount');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'binarypackagename'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'binarypackage'::pg_catalog.regclass;

INSERT INTO binarypackage (id, binarypackagename, "version", shortdesc, description, build, binpackageformat, component, section, priority, shlibdeps, depends, recommends, suggests, conflicts, replaces, provides, essential, installedsize, copyright, licence, architecturespecific, fti) VALUES (12, 8, '0.9', 'Mozilla Firefox Web Browser', 'Mozilla Firefox Web Browser is .....', 2, 1, 1, 1, 1, NULL, 'gcc-3.4-base, libc6 (>= 2.3.2.ds1-4), gcc-3.4 (>= 3.4.1-4sarge1), gcc-3.4 (<< 3.4.2), libstdc++6-dev (>= 3.4.1-4sarge1)', 'gcc-3.4-base, libc6 (>= 2.3.2.ds1-4), gcc-3.4 (>= 3.4.1-4sarge1), gcc-3.4 (<< 3.4.2), libstdc++6-dev (>= 3.4.1-4sarge1)', NULL, NULL, NULL, 'mozilla-firefox', NULL, NULL, NULL, NULL, true, '''web'':3,7 ''browser'':4,8 ''firefox'':2,6 ''mozilla'':1,5');
INSERT INTO binarypackage (id, binarypackagename, "version", shortdesc, description, build, binpackageformat, component, section, priority, shlibdeps, depends, recommends, suggests, conflicts, replaces, provides, essential, installedsize, copyright, licence, architecturespecific, fti) VALUES (15, 13, '0.1-1', 'pmount shortdesc', 'pmount description', 7, 1, 1, 1, 4, NULL, NULL, NULL, NULL, NULL, NULL, NULL, false, NULL, NULL, NULL, false, '''pmount'':1,3 ''descript'':4 ''shortdesc'':2');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'binarypackage'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'binarypackagefile'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'binarypackagefile'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'packagepublishing'::pg_catalog.regclass;

INSERT INTO packagepublishing (id, binarypackage, distroarchrelease, component, section, priority, scheduleddeletiondate, status, datepublished) VALUES (9, 12, 1, 1, 1, 1, NULL, 2, NULL);
INSERT INTO packagepublishing (id, binarypackage, distroarchrelease, component, section, priority, scheduleddeletiondate, status, datepublished) VALUES (11, 15, 6, 1, 1, 4, NULL, 2, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'packagepublishing'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'packageselection'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'packageselection'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'osfile'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'osfile'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'osfileinpackage'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'osfileinpackage'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'pomsgid'::pg_catalog.regclass;

INSERT INTO pomsgid (id, msgid) VALUES (1, 'evolution addressbook');
INSERT INTO pomsgid (id, msgid) VALUES (2, 'current addressbook folder');
INSERT INTO pomsgid (id, msgid) VALUES (3, 'have ');
INSERT INTO pomsgid (id, msgid) VALUES (4, 'has ');
INSERT INTO pomsgid (id, msgid) VALUES (5, ' cards');
INSERT INTO pomsgid (id, msgid) VALUES (6, ' card');
INSERT INTO pomsgid (id, msgid) VALUES (7, 'contact''s header: ');
INSERT INTO pomsgid (id, msgid) VALUES (8, 'evolution minicard');
INSERT INTO pomsgid (id, msgid) VALUES (9, 'This addressbook could not be opened.');
INSERT INTO pomsgid (id, msgid) VALUES (10, 'This addressbook server might unreachable or the server name may be misspelled or your network connection could be down.');
INSERT INTO pomsgid (id, msgid) VALUES (11, 'Failed to authenticate with LDAP server.');
INSERT INTO pomsgid (id, msgid) VALUES (12, 'Check to make sure your password is spelled correctly and that you are using a supported login method. Remember that many passwords are case sensitive; your caps lock might be on.');
INSERT INTO pomsgid (id, msgid) VALUES (13, 'Migrating `%s'':');
INSERT INTO pomsgid (id, msgid) VALUES (14, 'The location and hierarchy of the Evolution contact folders has changed since Evolution 1.x.

Please be patient while Evolution migrates your folders...');
INSERT INTO pomsgid (id, msgid) VALUES (15, '%d contact');
INSERT INTO pomsgid (id, msgid) VALUES (16, '%d contacts');
INSERT INTO pomsgid (id, msgid) VALUES (17, 'Opening %d contact will open %d new window as well.
Do you really want to display this contact?');
INSERT INTO pomsgid (id, msgid) VALUES (18, 'Opening %d contacts will open %d new windows as well.
Do you really want to display all of these contacts?');
INSERT INTO pomsgid (id, msgid) VALUES (19, '%d foo');
INSERT INTO pomsgid (id, msgid) VALUES (20, '%d bars');
INSERT INTO pomsgid (id, msgid) VALUES (21, 'EncFS Password: ');
INSERT INTO pomsgid (id, msgid) VALUES (22, 'When specifying daemon mode, you must use absolute paths (beginning with ''/'')');
INSERT INTO pomsgid (id, msgid) VALUES (23, 'Please select a key size in bits.  The cipher you have chosen
supports sizes from %i to %i bits in increments of %i bits.
For example: ');
INSERT INTO pomsgid (id, msgid) VALUES (24, 'Found %i invalid file.');
INSERT INTO pomsgid (id, msgid) VALUES (25, 'Found %i invalid files.');
INSERT INTO pomsgid (id, msgid) VALUES (26, '
      <p>Thousands of sites (particularly news sites and weblogs) publish their latest headlines and/or stories in a machine-readable format so that other sites can easily link to them. This content is usually in the form of an <a href="http://blogs.law.harvard.edu/tech/rss">RSS</a> feed (which is an XML-based syndication standard).</p>
      <p>You can read aggregated content from many sites using RSS feed readers, such as <a href="http://www.disobey.com/amphetadesk/">Amphetadesk</a>.</p>
      <p>Drupal provides the means to aggregate feeds from many sites and display these aggregated feeds to your site''s visitors. To do this, enable the aggregator module in site administration and then go to the aggregator configuration page, where you can subscribe to feeds and set up other options.</p>
      <h3>How do I find RSS feeds to aggregate?</h3>
      <p>Many web sites (especially weblogs) display small XML icons or other obvious links on their home page. You can follow these to obtain the web address for the RSS feed. Common extensions for RSS feeds are .rss, .xml and .rdf. For example: <a href="http://slashdot.org/slashdot.rdf">Slashdot RSS</a>.</p>
      <p>If you can''t find a feed for a site, or you want to find several feeds on a given topic, try an RSS syndication directory such as <a href="http://www.syndic8.com/">Syndic8</a>.</p>
      <p>To learn more about RSS, read Mark Pilgrim''s <a href="http://www.xml.com/pub/a/2002/12/18/dive-into-xml.html">What is RSS</a> and WebReference.com''s <a href="http://www.webreference.com/authoring/languages/xml/rss/1/">The Evolution of RSS</a> articles.</p>
      <p>NOTE: Enable your site''s XML syndication button by turning on the Syndicate block in block management.</p>
      <h3>How do I add a news feed?</h3>
      <p>To subscribe to an RSS feed on another site, use the <a href="% admin-news">aggregation page</a>.</p>
      <p>Once there, click the <a href="%new-feed">new feed</a> tab. Drupal will then ask for the following:</p>
      <ul>
       <li><strong>Title</strong> -- The text entered here will be used in your news aggregator, within the administration configuration section, and as a title for the news feed block. As a general rule, use the web site name from which the feed originates.</li>
       <li><strong>URL</strong> -- Here you''ll enter the fully-qualified web address for the feed you wish to subscribe to.</li>
       <li><strong>Update interval</strong> -- This is how often Drupal will scan the feed for new content. This defaults to every hour. Checking a feed more frequently that this is typically a waste of bandwidth and is considered somewhat impolite. For automatic updates to work, cron.php must be called regularly. If it is not, you''ll have to manually update the feeds one at a time within the news aggregation administration page by using <a href="%update-items">update items</a>.</li>
       <li><strong>Latest items block</strong> -- The number of items selected here will determine how many of the latest items from the feed will appear in a block which may be enabled and placed in the <a href="%block">blocks</a> administration page.</li>
       <li><strong>Automatically file items</strong> -- As items are received from a feed they will be put in any categories you have selected here.</li>
      </ul>
      <p>Once you have submitted the new feed, check to make sure it is working properly by selecting <a href="%update-items">update items</a> on the <a href="%admin-news">aggregation page</a>. If you do not see any items listed for that feed, edit the feed and make sure that the URL was entered correctly.</p>
      <h3>Adding categories</h3>
      <p>News items can be filed into categories. To create a category, start at the <a href="%admin-news">aggregation page</a>.</p>
      <p>Once there, select <a href="%new-category">new category</a> from the menu. Drupal will then ask for the following:</p>
      <ul>
       <li><strong>Title</strong> -- The title will be used in the <em>news by topics</em> listing in your news aggregator and for the block created for the bundle.</li>
       <li><strong>Description</strong> -- A short description of the category to tell users more details about what news items they might find in the category.</li>
       <li><strong>Latest items block</strong> -- The number of items selected here will determine how many of the latest items from the category will appear in a block which may be enabled and placed in the <a href="%block">blocks</a> administration page.</li>
      </ul>
      <h3>Using the news aggregator</h3>
      <p>The news aggregator has a number of ways that it displays your subscribed content:</p>
      <ul>
       <li><strong><a href="%news-aggregator">News aggregator</a></strong> (latest news) -- Displays all incoming items in the order in which they were received.</li>
       <li><strong><a href="%sources">Sources</a></strong> -- Organizes incoming content by feed, displaying feed titles (each of which links to a page with the latest items from that feed) and item titles (which link to that item''s actual story/article).</li>
       <li><strong><a href="%categories">Categories</a></strong> -- Organizes incoming content by category, displaying category titles (each of which links to a page with the latest items from that category) and item titles (which link to that item''s actual story/article).</li>
      </ul>
      <p>Pages that display items (for sources, categories, etc.) display the following for each item:
      <ul>
       <li>The title of the item (its headline).</li>
       <li>The categories that the item belongs to, each of which links to that particular category page as detailed above.</li>
       <li>A description containing the first few paragraphs or a summary of the item (if available).</li>
       <li>The name of the feed, which links to the individual feed''s page, listing information about that feed and items for that feed only. This is not shown on feed pages (they would link to the page you''re currently on).</li>
      </ul>
      <p>Additionally, users with the <em>administer news feeds permission</em> will see a link to categorize the news items. Clicking this will allow them to select which category(s) each news item is in.</p>
      <h3>Technical details</h3>
      <p>Drupal automatically generates an OPML feed file that is available by selecting the XML icon on the News Sources page.</p>
      <p>When fetching feeds Drupal supports conditional GETs, this reduces the bandwidth usage for feeds that have not been updated since the last check.</p>
      <p>If a feed is permanently moved to a new location Drupal will automatically update the feed URL to the new address.</p>');
INSERT INTO pomsgid (id, msgid) VALUES (27, '_Add Group');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'pomsgid'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'potranslation'::pg_catalog.regclass;

INSERT INTO potranslation (id, translation) VALUES (1, 'libreta de direcciones de Evolution');
INSERT INTO potranslation (id, translation) VALUES (2, 'carpeta de libretas de direcciones actual');
INSERT INTO potranslation (id, translation) VALUES (3, 'tiene');
INSERT INTO potranslation (id, translation) VALUES (4, ' tarjetas');
INSERT INTO potranslation (id, translation) VALUES (5, 'La ubicación y jerarquía de las carpetas de contactos de Evolution ha cambiado desde Evolution 1.x.

Tenga paciencia mientras Evolution migra sus carpetas...');
INSERT INTO potranslation (id, translation) VALUES (6, '%d contacto');
INSERT INTO potranslation (id, translation) VALUES (7, '%d contactos');
INSERT INTO potranslation (id, translation) VALUES (8, 'Abrir %d contacto abrirá %d ventanas nuevas también.
¿Quiere realmente mostrar este contacto?');
INSERT INTO potranslation (id, translation) VALUES (9, 'Abrir %d contactos abrirá %d ventanas nuevas también.
¿Quiere realmente mostrar todos estos contactos?');
INSERT INTO potranslation (id, translation) VALUES (10, '%d foo');
INSERT INTO potranslation (id, translation) VALUES (11, 'Contraseña de EncFS: ');
INSERT INTO potranslation (id, translation) VALUES (12, '_Añadir grupo');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'potranslation'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = '"language"'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = '"language"'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'country'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'country'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'spokenin'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'spokenin'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'license'::pg_catalog.regclass;

INSERT INTO license (id, legalese) VALUES (1, 'GPL-2');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'license'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'potemplate'::pg_catalog.regclass;

INSERT INTO potemplate (id, priority, title, description, copyright, license, datecreated, "path", iscurrent, messagecount, "owner", rawfile, rawimporter, daterawimport, rawimportstatus, sourcepackagename, distrorelease, sourcepackageversion, header, potemplatename, productrelease, binarypackagename, languagepack, filename) VALUES (2, NULL, 'pmount', NULL, NULL, NULL, '2005-03-24 19:59:31.439579', NULL, true, 0, 30, '', 1, '2005-03-24 19:59:31.439579', 1, 14, 3, NULL, NULL, 2, NULL, 13, false, NULL);
INSERT INTO potemplate (id, priority, title, description, copyright, license, datecreated, "path", iscurrent, messagecount, "owner", rawfile, rawimporter, daterawimport, rawimportstatus, sourcepackagename, distrorelease, sourcepackageversion, header, potemplatename, productrelease, binarypackagename, languagepack, filename) VALUES (1, NULL, 'Template for evolution in hoary', 'Template for evolution in hoary', NULL, NULL, '2005-03-18 18:20:12.273149', 'po', true, 22, 30, 'IyBTT01FIERFU0NSSVBUSVZFIFRJVExFLgojIENvcHlyaWdodCAoQykgWUVBUiBUSEUgUEFDS0FH
RSdTIENPUFlSSUdIVCBIT0xERVIKIyBUaGlzIGZpbGUgaXMgZGlzdHJpYnV0ZWQgdW5kZXIgdGhl
IHNhbWUgbGljZW5zZSBhcyB0aGUgUEFDS0FHRSBwYWNrYWdlLgojIEZJUlNUIEFVVEhPUiA8RU1B
SUxAQUREUkVTUz4sIFlFQVIuCiMKIywgZnV6enkKbXNnaWQgIiIKbXNnc3RyICIiCiJQcm9qZWN0
LUlkLVZlcnNpb246IFBBQ0tBR0UgVkVSU0lPTlxuIgoiUmVwb3J0LU1zZ2lkLUJ1Z3MtVG86IFxu
IgoiUE9ULUNyZWF0aW9uLURhdGU6IDIwMDUtMDQtMDcgMTQ6MTArMDIwMFxuIgoiUE8tUmV2aXNp
b24tRGF0ZTogWUVBUi1NTy1EQSBITzpNSStaT05FXG4iCiJMYXN0LVRyYW5zbGF0b3I6IEZVTEwg
TkFNRSA8RU1BSUxAQUREUkVTUz5cbiIKIkxhbmd1YWdlLVRlYW06IExBTkdVQUdFIDxMTEBsaS5v
cmc+XG4iCiJNSU1FLVZlcnNpb246IDEuMFxuIgoiQ29udGVudC1UeXBlOiB0ZXh0L3BsYWluOyBj
aGFyc2V0PUFTQ0lJXG4iCiJDb250ZW50LVRyYW5zZmVyLUVuY29kaW5nOiA4Yml0XG4iCgojOiBh
MTF5L2FkZHJlc3Nib29rL2VhLWFkZHJlc3Nib29rLXZpZXcuYzo5NAojOiBhMTF5L2FkZHJlc3Ni
b29rL2VhLWFkZHJlc3Nib29rLXZpZXcuYzoxMDMKIzogYTExeS9hZGRyZXNzYm9vay9lYS1taW5p
Y2FyZC12aWV3LmM6MTE5Cm1zZ2lkICJldm9sdXRpb24gYWRkcmVzc2Jvb2siCm1zZ3N0ciAiIgoK
IzogYTExeS9hZGRyZXNzYm9vay9lYS1taW5pY2FyZC12aWV3LmM6MTAxCm1zZ2lkICJjdXJyZW50
IGFkZHJlc3Nib29rIGZvbGRlciIKbXNnc3RyICIiCgojOiBhMTF5L2FkZHJlc3Nib29rL2VhLW1p
bmljYXJkLXZpZXcuYzoxMDIKbXNnaWQgImhhdmUgIgptc2dzdHIgIiIKCiM6IGExMXkvYWRkcmVz
c2Jvb2svZWEtbWluaWNhcmQtdmlldy5jOjEwMgptc2dpZCAiaGFzICIKbXNnc3RyICIiCgojOiBh
MTF5L2FkZHJlc3Nib29rL2VhLW1pbmljYXJkLXZpZXcuYzoxMDQKbXNnaWQgIiBjYXJkcyIKbXNn
c3RyICIiCgojOiBhMTF5L2FkZHJlc3Nib29rL2VhLW1pbmljYXJkLXZpZXcuYzoxMDQKbXNnaWQg
IiBjYXJkIgptc2dzdHIgIiIKCiM6IGExMXkvYWRkcmVzc2Jvb2svZWEtbWluaWNhcmQtdmlldy5j
OjEwNQptc2dpZCAiY29udGFjdCdzIGhlYWRlcjogIgptc2dzdHIgIiIKCiM6IGExMXkvYWRkcmVz
c2Jvb2svZWEtbWluaWNhcmQuYzoxNjYKbXNnaWQgImV2b2x1dGlvbiBtaW5pY2FyZCIKbXNnc3Ry
ICIiCgojLiBhZGRyZXNzYm9vazpsZGFwLWluaXQgcHJpbWFyeQojOiBhZGRyZXNzYm9vay9hZGRy
ZXNzYm9vay1lcnJvcnMueG1sLmg6Mgptc2dpZCAiVGhpcyBhZGRyZXNzYm9vayBjb3VsZCBub3Qg
YmUgb3BlbmVkLiIKbXNnc3RyICIiCgojLiBhZGRyZXNzYm9vazpsZGFwLWluaXQgc2Vjb25kYXJ5
CiM6IGFkZHJlc3Nib29rL2FkZHJlc3Nib29rLWVycm9ycy54bWwuaDo0Cm1zZ2lkICIiCiJUaGlz
IGFkZHJlc3Nib29rIHNlcnZlciBtaWdodCB1bnJlYWNoYWJsZSBvciB0aGUgc2VydmVyIG5hbWUg
bWF5IGJlICIKIm1pc3NwZWxsZWQgb3IgeW91ciBuZXR3b3JrIGNvbm5lY3Rpb24gY291bGQgYmUg
ZG93bi4iCm1zZ3N0ciAiIgoKIy4gYWRkcmVzc2Jvb2s6bGRhcC1hdXRoIHByaW1hcnkKIzogYWRk
cmVzc2Jvb2svYWRkcmVzc2Jvb2stZXJyb3JzLnhtbC5oOjYKbXNnaWQgIkZhaWxlZCB0byBhdXRo
ZW50aWNhdGUgd2l0aCBMREFQIHNlcnZlci4iCm1zZ3N0ciAiIgoKIy4gYWRkcmVzc2Jvb2s6bGRh
cC1hdXRoIHNlY29uZGFyeQojOiBhZGRyZXNzYm9vay9hZGRyZXNzYm9vay1lcnJvcnMueG1sLmg6
OAptc2dpZCAiIgoiQ2hlY2sgdG8gbWFrZSBzdXJlIHlvdXIgcGFzc3dvcmQgaXMgc3BlbGxlZCBj
b3JyZWN0bHkgYW5kIHRoYXQgeW91IGFyZSB1c2luZyAiCiJhIHN1cHBvcnRlZCBsb2dpbiBtZXRo
b2QuIFJlbWVtYmVyIHRoYXQgbWFueSBwYXNzd29yZHMgYXJlIGNhc2Ugc2Vuc2l0aXZlOyAiCiJ5
b3VyIGNhcHMgbG9jayBtaWdodCBiZSBvbi4iCm1zZ3N0ciAiIgoKIzogYWRkcmVzc2Jvb2svZ3Vp
L2NvbXBvbmVudC9hZGRyZXNzYm9vay1taWdyYXRlLmM6MTI0CiM6IGNhbGVuZGFyL2d1aS9taWdy
YXRpb24uYzoxODggbWFpbC9lbS1taWdyYXRlLmM6MTIwMQojLCBjLWZvcm1hdAptc2dpZCAiTWln
cmF0aW5nIGAlcyc6Igptc2dzdHIgIiIKCiM6IGFkZHJlc3Nib29rL2d1aS9jb21wb25lbnQvYWRk
cmVzc2Jvb2stbWlncmF0ZS5jOjExMjMKbXNnaWQgIiIKIlRoZSBsb2NhdGlvbiBhbmQgaGllcmFy
Y2h5IG9mIHRoZSBFdm9sdXRpb24gY29udGFjdCBmb2xkZXJzIGhhcyBjaGFuZ2VkICIKInNpbmNl
IEV2b2x1dGlvbiAxLnguXG4iCiJcbiIKIlBsZWFzZSBiZSBwYXRpZW50IHdoaWxlIEV2b2x1dGlv
biBtaWdyYXRlcyB5b3VyIGZvbGRlcnMuLi4iCm1zZ3N0ciAiIgoKIzogYWRkcmVzc2Jvb2svZ3Vp
L3dpZGdldHMvZS1hZGRyZXNzYm9vay1tb2RlbC5jOjE1MQojLCBjLWZvcm1hdAptc2dpZCAiJWQg
Y29udGFjdCIKbXNnaWRfcGx1cmFsICIlZCBjb250YWN0cyIKbXNnc3RyWzBdICIiCm1zZ3N0clsx
XSAiIgoKIzogYWRkcmVzc2Jvb2svZ3VpL3dpZGdldHMvZWFiLWd1aS11dGlsLmM6Mjc1CiMsIGMt
Zm9ybWF0Cm1zZ2lkICIiCiJPcGVuaW5nICVkIGNvbnRhY3Qgd2lsbCBvcGVuICVkIG5ldyB3aW5k
b3cgYXMgd2VsbC5cbiIKIkRvIHlvdSByZWFsbHkgd2FudCB0byBkaXNwbGF5IHRoaXMgY29udGFj
dD8iCm1zZ2lkX3BsdXJhbCAiIgoiT3BlbmluZyAlZCBjb250YWN0cyB3aWxsIG9wZW4gJWQgbmV3
IHdpbmRvd3MgYXMgd2VsbC5cbiIKIkRvIHlvdSByZWFsbHkgd2FudCB0byBkaXNwbGF5IGFsbCBv
ZiB0aGVzZSBjb250YWN0cz8iCm1zZ3N0clswXSAiIgptc2dzdHJbMV0gIiIKCiM6IGFkZHJlc3Ni
b29rL2d1aS93aWRnZXRzL2Zvby5jOjM0NQojLCBjLWZvcm1hdAptc2dpZCAiJWQgZm9vIgptc2dp
ZF9wbHVyYWwgIiVkIGJhcnMiCm1zZ3N0clswXSAiIgptc2dzdHJbMV0gIiIKCiMgc3RhcnQgcG8t
Z3JvdXA6IGNvbW1vbgojLiB4Z3JvdXAoY29tbW9uKQojOiBlbmNmcy9GaWxlVXRpbHMuY3BwOjEw
NDQKbXNnaWQgIkVuY0ZTIFBhc3N3b3JkOiAiCm1zZ3N0ciAiIgoKIy4geGdyb3VwKHVzYWdlKQoj
OiBlbmNmcy9tYWluLmNwcDozNDAKbXNnaWQgIiIKIldoZW4gc3BlY2lmeWluZyBkYWVtb24gbW9k
ZSwgeW91IG11c3QgdXNlIGFic29sdXRlIHBhdGhzIChiZWdpbm5pbmcgd2l0aCAnLycpIgptc2dz
dHIgIiIKCiMuIHhncm91cChzZXR1cCkKIzogZW5jZnMvRmlsZVV0aWxzLmNwcDo1MzUKIywgYy1m
b3JtYXQKbXNnaWQgIiIKIlBsZWFzZSBzZWxlY3QgYSBrZXkgc2l6ZSBpbiBiaXRzLiAgVGhlIGNp
cGhlciB5b3UgaGF2ZSBjaG9zZW5cbiIKInN1cHBvcnRzIHNpemVzIGZyb20gJWkgdG8gJWkgYml0
cyBpbiBpbmNyZW1lbnRzIG9mICVpIGJpdHMuXG4iCiJGb3IgZXhhbXBsZTogIgptc2dzdHIgIiIK
CiM6IGVuY2ZzL2VuY2ZzY3RsLmNwcDozNDYKIywgYy1mb3JtYXQKbXNnaWQgIkZvdW5kICVpIGlu
dmFsaWQgZmlsZS4iCm1zZ2lkX3BsdXJhbCAiRm91bmQgJWkgaW52YWxpZCBmaWxlcy4iCm1zZ3N0
clswXSAiIgptc2dzdHJbMV0gIiIKCiM6IG1vZHVsZXMvYWdncmVnYXRvci5tb2R1bGU6MTUKbXNn
aWQgIiIKIlxuIgoiICAgICAgPHA+VGhvdXNhbmRzIG9mIHNpdGVzIChwYXJ0aWN1bGFybHkgbmV3
cyBzaXRlcyBhbmQgd2VibG9ncykgcHVibGlzaCAiCiJ0aGVpciBsYXRlc3QgaGVhZGxpbmVzIGFu
ZC9vciBzdG9yaWVzIGluIGEgbWFjaGluZS1yZWFkYWJsZSBmb3JtYXQgc28gdGhhdCAiCiJvdGhl
ciBzaXRlcyBjYW4gZWFzaWx5IGxpbmsgdG8gdGhlbS4gVGhpcyBjb250ZW50IGlzIHVzdWFsbHkg
aW4gdGhlIGZvcm0gb2YgIgoiYW4gPGEgaHJlZj1cImh0dHA6Ly9ibG9ncy5sYXcuaGFydmFyZC5l
ZHUvdGVjaC9yc3NcIj5SU1M8L2E+IGZlZWQgKHdoaWNoIGlzICIKImFuIFhNTC1iYXNlZCBzeW5k
aWNhdGlvbiBzdGFuZGFyZCkuPC9wPlxuIgoiICAgICAgPHA+WW91IGNhbiByZWFkIGFnZ3JlZ2F0
ZWQgY29udGVudCBmcm9tIG1hbnkgc2l0ZXMgdXNpbmcgUlNTIGZlZWQgIgoicmVhZGVycywgc3Vj
aCBhcyA8YSAiCiJocmVmPVwiaHR0cDovL3d3dy5kaXNvYmV5LmNvbS9hbXBoZXRhZGVzay9cIj5B
bXBoZXRhZGVzazwvYT4uPC9wPlxuIgoiICAgICAgPHA+RHJ1cGFsIHByb3ZpZGVzIHRoZSBtZWFu
cyB0byBhZ2dyZWdhdGUgZmVlZHMgZnJvbSBtYW55IHNpdGVzIGFuZCAiCiJkaXNwbGF5IHRoZXNl
IGFnZ3JlZ2F0ZWQgZmVlZHMgdG8geW91ciBzaXRlJ3MgdmlzaXRvcnMuIFRvIGRvIHRoaXMsIGVu
YWJsZSAiCiJ0aGUgYWdncmVnYXRvciBtb2R1bGUgaW4gc2l0ZSBhZG1pbmlzdHJhdGlvbiBhbmQg
dGhlbiBnbyB0byB0aGUgYWdncmVnYXRvciAiCiJjb25maWd1cmF0aW9uIHBhZ2UsIHdoZXJlIHlv
dSBjYW4gc3Vic2NyaWJlIHRvIGZlZWRzIGFuZCBzZXQgdXAgb3RoZXIgIgoib3B0aW9ucy48L3A+
XG4iCiIgICAgICA8aDM+SG93IGRvIEkgZmluZCBSU1MgZmVlZHMgdG8gYWdncmVnYXRlPzwvaDM+
XG4iCiIgICAgICA8cD5NYW55IHdlYiBzaXRlcyAoZXNwZWNpYWxseSB3ZWJsb2dzKSBkaXNwbGF5
IHNtYWxsIFhNTCBpY29ucyBvciAiCiJvdGhlciBvYnZpb3VzIGxpbmtzIG9uIHRoZWlyIGhvbWUg
cGFnZS4gWW91IGNhbiBmb2xsb3cgdGhlc2UgdG8gb2J0YWluIHRoZSAiCiJ3ZWIgYWRkcmVzcyBm
b3IgdGhlIFJTUyBmZWVkLiBDb21tb24gZXh0ZW5zaW9ucyBmb3IgUlNTIGZlZWRzIGFyZSAucnNz
LCAueG1sICIKImFuZCAucmRmLiBGb3IgZXhhbXBsZTogPGEgaHJlZj1cImh0dHA6Ly9zbGFzaGRv
dC5vcmcvc2xhc2hkb3QucmRmXCI+U2xhc2hkb3QgIgoiUlNTPC9hPi48L3A+XG4iCiIgICAgICA8
cD5JZiB5b3UgY2FuJ3QgZmluZCBhIGZlZWQgZm9yIGEgc2l0ZSwgb3IgeW91IHdhbnQgdG8gZmlu
ZCBzZXZlcmFsICIKImZlZWRzIG9uIGEgZ2l2ZW4gdG9waWMsIHRyeSBhbiBSU1Mgc3luZGljYXRp
b24gZGlyZWN0b3J5IHN1Y2ggYXMgPGEgIgoiaHJlZj1cImh0dHA6Ly93d3cuc3luZGljOC5jb20v
XCI+U3luZGljODwvYT4uPC9wPlxuIgoiICAgICAgPHA+VG8gbGVhcm4gbW9yZSBhYm91dCBSU1Ms
IHJlYWQgTWFyayBQaWxncmltJ3MgPGEgIgoiaHJlZj1cImh0dHA6Ly93d3cueG1sLmNvbS9wdWIv
YS8yMDAyLzEyLzE4L2RpdmUtaW50by14bWwuaHRtbFwiPldoYXQgaXMgIgoiUlNTPC9hPiBhbmQg
V2ViUmVmZXJlbmNlLmNvbSdzIDxhICIKImhyZWY9XCJodHRwOi8vd3d3LndlYnJlZmVyZW5jZS5j
b20vYXV0aG9yaW5nL2xhbmd1YWdlcy94bWwvcnNzLzEvXCI+VGhlICIKIkV2b2x1dGlvbiBvZiBS
U1M8L2E+IGFydGljbGVzLjwvcD5cbiIKIiAgICAgIDxwPk5PVEU6IEVuYWJsZSB5b3VyIHNpdGUn
cyBYTUwgc3luZGljYXRpb24gYnV0dG9uIGJ5IHR1cm5pbmcgb24gdGhlICIKIlN5bmRpY2F0ZSBi
bG9jayBpbiBibG9jayBtYW5hZ2VtZW50LjwvcD5cbiIKIiAgICAgIDxoMz5Ib3cgZG8gSSBhZGQg
YSBuZXdzIGZlZWQ/PC9oMz5cbiIKIiAgICAgIDxwPlRvIHN1YnNjcmliZSB0byBhbiBSU1MgZmVl
ZCBvbiBhbm90aGVyIHNpdGUsIHVzZSB0aGUgPGEgaHJlZj1cIiUgIgoiYWRtaW4tbmV3c1wiPmFn
Z3JlZ2F0aW9uIHBhZ2U8L2E+LjwvcD5cbiIKIiAgICAgIDxwPk9uY2UgdGhlcmUsIGNsaWNrIHRo
ZSA8YSBocmVmPVwiJW5ldy1mZWVkXCI+bmV3IGZlZWQ8L2E+IHRhYi4gIgoiRHJ1cGFsIHdpbGwg
dGhlbiBhc2sgZm9yIHRoZSBmb2xsb3dpbmc6PC9wPlxuIgoiICAgICAgPHVsPlxuIgoiICAgICAg
IDxsaT48c3Ryb25nPlRpdGxlPC9zdHJvbmc+IC0tIFRoZSB0ZXh0IGVudGVyZWQgaGVyZSB3aWxs
IGJlIHVzZWQgaW4gIgoieW91ciBuZXdzIGFnZ3JlZ2F0b3IsIHdpdGhpbiB0aGUgYWRtaW5pc3Ry
YXRpb24gY29uZmlndXJhdGlvbiBzZWN0aW9uLCBhbmQgIgoiYXMgYSB0aXRsZSBmb3IgdGhlIG5l
d3MgZmVlZCBibG9jay4gQXMgYSBnZW5lcmFsIHJ1bGUsIHVzZSB0aGUgd2ViIHNpdGUgbmFtZSAi
CiJmcm9tIHdoaWNoIHRoZSBmZWVkIG9yaWdpbmF0ZXMuPC9saT5cbiIKIiAgICAgICA8bGk+PHN0
cm9uZz5VUkw8L3N0cm9uZz4gLS0gSGVyZSB5b3UnbGwgZW50ZXIgdGhlIGZ1bGx5LXF1YWxpZmll
ZCB3ZWIgIgoiYWRkcmVzcyBmb3IgdGhlIGZlZWQgeW91IHdpc2ggdG8gc3Vic2NyaWJlIHRvLjwv
bGk+XG4iCiIgICAgICAgPGxpPjxzdHJvbmc+VXBkYXRlIGludGVydmFsPC9zdHJvbmc+IC0tIFRo
aXMgaXMgaG93IG9mdGVuIERydXBhbCB3aWxsICIKInNjYW4gdGhlIGZlZWQgZm9yIG5ldyBjb250
ZW50LiBUaGlzIGRlZmF1bHRzIHRvIGV2ZXJ5IGhvdXIuIENoZWNraW5nIGEgZmVlZCAiCiJtb3Jl
IGZyZXF1ZW50bHkgdGhhdCB0aGlzIGlzIHR5cGljYWxseSBhIHdhc3RlIG9mIGJhbmR3aWR0aCBh
bmQgaXMgIgoiY29uc2lkZXJlZCBzb21ld2hhdCBpbXBvbGl0ZS4gRm9yIGF1dG9tYXRpYyB1cGRh
dGVzIHRvIHdvcmssIGNyb24ucGhwIG11c3QgIgoiYmUgY2FsbGVkIHJlZ3VsYXJseS4gSWYgaXQg
aXMgbm90LCB5b3UnbGwgaGF2ZSB0byBtYW51YWxseSB1cGRhdGUgdGhlIGZlZWRzICIKIm9uZSBh
dCBhIHRpbWUgd2l0aGluIHRoZSBuZXdzIGFnZ3JlZ2F0aW9uIGFkbWluaXN0cmF0aW9uIHBhZ2Ug
YnkgdXNpbmcgPGEgIgoiaHJlZj1cIiV1cGRhdGUtaXRlbXNcIj51cGRhdGUgaXRlbXM8L2E+Ljwv
bGk+XG4iCiIgICAgICAgPGxpPjxzdHJvbmc+TGF0ZXN0IGl0ZW1zIGJsb2NrPC9zdHJvbmc+IC0t
IFRoZSBudW1iZXIgb2YgaXRlbXMgIgoic2VsZWN0ZWQgaGVyZSB3aWxsIGRldGVybWluZSBob3cg
bWFueSBvZiB0aGUgbGF0ZXN0IGl0ZW1zIGZyb20gdGhlIGZlZWQgd2lsbCAiCiJhcHBlYXIgaW4g
YSBibG9jayB3aGljaCBtYXkgYmUgZW5hYmxlZCBhbmQgcGxhY2VkIGluIHRoZSA8YSAiCiJocmVm
PVwiJWJsb2NrXCI+YmxvY2tzPC9hPiBhZG1pbmlzdHJhdGlvbiBwYWdlLjwvbGk+XG4iCiIgICAg
ICAgPGxpPjxzdHJvbmc+QXV0b21hdGljYWxseSBmaWxlIGl0ZW1zPC9zdHJvbmc+IC0tIEFzIGl0
ZW1zIGFyZSAiCiJyZWNlaXZlZCBmcm9tIGEgZmVlZCB0aGV5IHdpbGwgYmUgcHV0IGluIGFueSBj
YXRlZ29yaWVzIHlvdSBoYXZlIHNlbGVjdGVkICIKImhlcmUuPC9saT5cbiIKIiAgICAgIDwvdWw+
XG4iCiIgICAgICA8cD5PbmNlIHlvdSBoYXZlIHN1Ym1pdHRlZCB0aGUgbmV3IGZlZWQsIGNoZWNr
IHRvIG1ha2Ugc3VyZSBpdCBpcyAiCiJ3b3JraW5nIHByb3Blcmx5IGJ5IHNlbGVjdGluZyA8YSBo
cmVmPVwiJXVwZGF0ZS1pdGVtc1wiPnVwZGF0ZSBpdGVtczwvYT4gb24gIgoidGhlIDxhIGhyZWY9
XCIlYWRtaW4tbmV3c1wiPmFnZ3JlZ2F0aW9uIHBhZ2U8L2E+LiBJZiB5b3UgZG8gbm90IHNlZSBh
bnkgIgoiaXRlbXMgbGlzdGVkIGZvciB0aGF0IGZlZWQsIGVkaXQgdGhlIGZlZWQgYW5kIG1ha2Ug
c3VyZSB0aGF0IHRoZSBVUkwgd2FzICIKImVudGVyZWQgY29ycmVjdGx5LjwvcD5cbiIKIiAgICAg
IDxoMz5BZGRpbmcgY2F0ZWdvcmllczwvaDM+XG4iCiIgICAgICA8cD5OZXdzIGl0ZW1zIGNhbiBi
ZSBmaWxlZCBpbnRvIGNhdGVnb3JpZXMuIFRvIGNyZWF0ZSBhIGNhdGVnb3J5LCAiCiJzdGFydCBh
dCB0aGUgPGEgaHJlZj1cIiVhZG1pbi1uZXdzXCI+YWdncmVnYXRpb24gcGFnZTwvYT4uPC9wPlxu
IgoiICAgICAgPHA+T25jZSB0aGVyZSwgc2VsZWN0IDxhIGhyZWY9XCIlbmV3LWNhdGVnb3J5XCI+
bmV3IGNhdGVnb3J5PC9hPiBmcm9tICIKInRoZSBtZW51LiBEcnVwYWwgd2lsbCB0aGVuIGFzayBm
b3IgdGhlIGZvbGxvd2luZzo8L3A+XG4iCiIgICAgICA8dWw+XG4iCiIgICAgICAgPGxpPjxzdHJv
bmc+VGl0bGU8L3N0cm9uZz4gLS0gVGhlIHRpdGxlIHdpbGwgYmUgdXNlZCBpbiB0aGUgPGVtPm5l
d3MgIgoiYnkgdG9waWNzPC9lbT4gbGlzdGluZyBpbiB5b3VyIG5ld3MgYWdncmVnYXRvciBhbmQg
Zm9yIHRoZSBibG9jayBjcmVhdGVkIGZvciAiCiJ0aGUgYnVuZGxlLjwvbGk+XG4iCiIgICAgICAg
PGxpPjxzdHJvbmc+RGVzY3JpcHRpb248L3N0cm9uZz4gLS0gQSBzaG9ydCBkZXNjcmlwdGlvbiBv
ZiB0aGUgIgoiY2F0ZWdvcnkgdG8gdGVsbCB1c2VycyBtb3JlIGRldGFpbHMgYWJvdXQgd2hhdCBu
ZXdzIGl0ZW1zIHRoZXkgbWlnaHQgZmluZCBpbiAiCiJ0aGUgY2F0ZWdvcnkuPC9saT5cbiIKIiAg
ICAgICA8bGk+PHN0cm9uZz5MYXRlc3QgaXRlbXMgYmxvY2s8L3N0cm9uZz4gLS0gVGhlIG51bWJl
ciBvZiBpdGVtcyAiCiJzZWxlY3RlZCBoZXJlIHdpbGwgZGV0ZXJtaW5lIGhvdyBtYW55IG9mIHRo
ZSBsYXRlc3QgaXRlbXMgZnJvbSB0aGUgY2F0ZWdvcnkgIgoid2lsbCBhcHBlYXIgaW4gYSBibG9j
ayB3aGljaCBtYXkgYmUgZW5hYmxlZCBhbmQgcGxhY2VkIGluIHRoZSA8YSAiCiJocmVmPVwiJWJs
b2NrXCI+YmxvY2tzPC9hPiBhZG1pbmlzdHJhdGlvbiBwYWdlLjwvbGk+XG4iCiIgICAgICA8L3Vs
PlxuIgoiICAgICAgPGgzPlVzaW5nIHRoZSBuZXdzIGFnZ3JlZ2F0b3I8L2gzPlxuIgoiICAgICAg
PHA+VGhlIG5ld3MgYWdncmVnYXRvciBoYXMgYSBudW1iZXIgb2Ygd2F5cyB0aGF0IGl0IGRpc3Bs
YXlzIHlvdXIgIgoic3Vic2NyaWJlZCBjb250ZW50OjwvcD5cbiIKIiAgICAgIDx1bD5cbiIKIiAg
ICAgICA8bGk+PHN0cm9uZz48YSBocmVmPVwiJW5ld3MtYWdncmVnYXRvclwiPk5ld3MgYWdncmVn
YXRvcjwvYT48L3N0cm9uZz4gIgoiKGxhdGVzdCBuZXdzKSAtLSBEaXNwbGF5cyBhbGwgaW5jb21p
bmcgaXRlbXMgaW4gdGhlIG9yZGVyIGluIHdoaWNoIHRoZXkgd2VyZSAiCiJyZWNlaXZlZC48L2xp
PlxuIgoiICAgICAgIDxsaT48c3Ryb25nPjxhIGhyZWY9XCIlc291cmNlc1wiPlNvdXJjZXM8L2E+
PC9zdHJvbmc+IC0tIE9yZ2FuaXplcyAiCiJpbmNvbWluZyBjb250ZW50IGJ5IGZlZWQsIGRpc3Bs
YXlpbmcgZmVlZCB0aXRsZXMgKGVhY2ggb2Ygd2hpY2ggbGlua3MgdG8gYSAiCiJwYWdlIHdpdGgg
dGhlIGxhdGVzdCBpdGVtcyBmcm9tIHRoYXQgZmVlZCkgYW5kIGl0ZW0gdGl0bGVzICh3aGljaCBs
aW5rIHRvICIKInRoYXQgaXRlbSdzIGFjdHVhbCBzdG9yeS9hcnRpY2xlKS48L2xpPlxuIgoiICAg
ICAgIDxsaT48c3Ryb25nPjxhIGhyZWY9XCIlY2F0ZWdvcmllc1wiPkNhdGVnb3JpZXM8L2E+PC9z
dHJvbmc+IC0tICIKIk9yZ2FuaXplcyBpbmNvbWluZyBjb250ZW50IGJ5IGNhdGVnb3J5LCBkaXNw
bGF5aW5nIGNhdGVnb3J5IHRpdGxlcyAoZWFjaCBvZiAiCiJ3aGljaCBsaW5rcyB0byBhIHBhZ2Ug
d2l0aCB0aGUgbGF0ZXN0IGl0ZW1zIGZyb20gdGhhdCBjYXRlZ29yeSkgYW5kIGl0ZW0gIgoidGl0
bGVzICh3aGljaCBsaW5rIHRvIHRoYXQgaXRlbSdzIGFjdHVhbCBzdG9yeS9hcnRpY2xlKS48L2xp
PlxuIgoiICAgICAgPC91bD5cbiIKIiAgICAgIDxwPlBhZ2VzIHRoYXQgZGlzcGxheSBpdGVtcyAo
Zm9yIHNvdXJjZXMsIGNhdGVnb3JpZXMsIGV0Yy4pIGRpc3BsYXkgIgoidGhlIGZvbGxvd2luZyBm
b3IgZWFjaCBpdGVtOlxuIgoiICAgICAgPHVsPlxuIgoiICAgICAgIDxsaT5UaGUgdGl0bGUgb2Yg
dGhlIGl0ZW0gKGl0cyBoZWFkbGluZSkuPC9saT5cbiIKIiAgICAgICA8bGk+VGhlIGNhdGVnb3Jp
ZXMgdGhhdCB0aGUgaXRlbSBiZWxvbmdzIHRvLCBlYWNoIG9mIHdoaWNoIGxpbmtzIHRvICIKInRo
YXQgcGFydGljdWxhciBjYXRlZ29yeSBwYWdlIGFzIGRldGFpbGVkIGFib3ZlLjwvbGk+XG4iCiIg
ICAgICAgPGxpPkEgZGVzY3JpcHRpb24gY29udGFpbmluZyB0aGUgZmlyc3QgZmV3IHBhcmFncmFw
aHMgb3IgYSBzdW1tYXJ5IG9mICIKInRoZSBpdGVtIChpZiBhdmFpbGFibGUpLjwvbGk+XG4iCiIg
ICAgICAgPGxpPlRoZSBuYW1lIG9mIHRoZSBmZWVkLCB3aGljaCBsaW5rcyB0byB0aGUgaW5kaXZp
ZHVhbCBmZWVkJ3MgcGFnZSwgIgoibGlzdGluZyBpbmZvcm1hdGlvbiBhYm91dCB0aGF0IGZlZWQg
YW5kIGl0ZW1zIGZvciB0aGF0IGZlZWQgb25seS4gVGhpcyBpcyAiCiJub3Qgc2hvd24gb24gZmVl
ZCBwYWdlcyAodGhleSB3b3VsZCBsaW5rIHRvIHRoZSBwYWdlIHlvdSdyZSBjdXJyZW50bHkgIgoi
b24pLjwvbGk+XG4iCiIgICAgICA8L3VsPlxuIgoiICAgICAgPHA+QWRkaXRpb25hbGx5LCB1c2Vy
cyB3aXRoIHRoZSA8ZW0+YWRtaW5pc3RlciBuZXdzIGZlZWRzICIKInBlcm1pc3Npb248L2VtPiB3
aWxsIHNlZSBhIGxpbmsgdG8gY2F0ZWdvcml6ZSB0aGUgbmV3cyBpdGVtcy4gQ2xpY2tpbmcgdGhp
cyAiCiJ3aWxsIGFsbG93IHRoZW0gdG8gc2VsZWN0IHdoaWNoIGNhdGVnb3J5KHMpIGVhY2ggbmV3
cyBpdGVtIGlzIGluLjwvcD5cbiIKIiAgICAgIDxoMz5UZWNobmljYWwgZGV0YWlsczwvaDM+XG4i
CiIgICAgICA8cD5EcnVwYWwgYXV0b21hdGljYWxseSBnZW5lcmF0ZXMgYW4gT1BNTCBmZWVkIGZp
bGUgdGhhdCBpcyBhdmFpbGFibGUgIgoiYnkgc2VsZWN0aW5nIHRoZSBYTUwgaWNvbiBvbiB0aGUg
TmV3cyBTb3VyY2VzIHBhZ2UuPC9wPlxuIgoiICAgICAgPHA+V2hlbiBmZXRjaGluZyBmZWVkcyBE
cnVwYWwgc3VwcG9ydHMgY29uZGl0aW9uYWwgR0VUcywgdGhpcyByZWR1Y2VzICIKInRoZSBiYW5k
d2lkdGggdXNhZ2UgZm9yIGZlZWRzIHRoYXQgaGF2ZSBub3QgYmVlbiB1cGRhdGVkIHNpbmNlIHRo
ZSBsYXN0ICIKImNoZWNrLjwvcD5cbiIKIiAgICAgIDxwPklmIGEgZmVlZCBpcyBwZXJtYW5lbnRs
eSBtb3ZlZCB0byBhIG5ldyBsb2NhdGlvbiBEcnVwYWwgd2lsbCAiCiJhdXRvbWF0aWNhbGx5IHVw
ZGF0ZSB0aGUgZmVlZCBVUkwgdG8gdGhlIG5ldyBhZGRyZXNzLjwvcD4iCm1zZ3N0ciAiIgo=
', 13, '2005-04-07 13:12:39.892924', 3, 9, 3, NULL, 'Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2005-04-07 14:10+0200
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: LANGUAGE <LL@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=ASCII
Content-Transfer-Encoding: 8bit
', 1, NULL, NULL, false, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'potemplate'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'pofile'::pg_catalog.regclass;

INSERT INTO pofile (id, potemplate, "language", title, description, topcomment, header, fuzzyheader, lasttranslator, license, currentcount, updatescount, rosettacount, lastparsed, "owner", pluralforms, variant, filename, rawfile, rawimporter, daterawimport, rawimportstatus) VALUES (1, 1, 387, 'Spanish translation for evolution in hoary', 'Spanish translation for evolution in hoary', ' traducción de es.po al Spanish
 translation of es.po to Spanish
 translation of evolution.HEAD to Spanish
 Copyright © 2000-2002 Free Software Foundation, Inc.
 This file is distributed under the same license as the evolution package.
 Carlos Perelló Marín <carlos@gnome-db.org>, 2000-2001.
 Héctor García Álvarez <hector@scouts-es.org>, 2000-2002.
 Ismael Olea <Ismael@olea.org>, 2001, (revisiones) 2003.
 Eneko Lacunza <enlar@iname.com>, 2001-2002.
 Héctor García Álvarez <hector@scouts-es.org>, 2002.
 Pablo Gonzalo del Campo <pablodc@bigfoot.com>,2003 (revisión).
 Francisco Javier F. Serrador <serrador@cvs.gnome.org>, 2003, 2004.


', 'Project-Id-Version: es
POT-Creation-Date: 2004-08-17 11:10+0200
PO-Revision-Date: 2005-04-07 13:22+0000
Last-Translator: Carlos Perelló Marín <carlos@canonical.com>
Language-Team: Spanish <traductores@es.gnome.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Report-Msgid-Bugs-To: serrador@hispalinux.es
X-Generator: Rosetta (http://launchpad.ubuntu.com/rosetta/)
Plural-Forms: nplurals=2; plural=(n != 1);
', true, NULL, NULL, 7, 0, 0, NULL, 30, 2, NULL, NULL, 'IyB0cmFkdWNjacOzbiBkZSBlcy5wbyBhbCBTcGFuaXNoCiMgdHJhbnNsYXRpb24gb2YgZXMucG8g
dG8gU3BhbmlzaAojIHRyYW5zbGF0aW9uIG9mIGV2b2x1dGlvbi5IRUFEIHRvIFNwYW5pc2gKIyBD
b3B5cmlnaHQgwqkgMjAwMC0yMDAyIEZyZWUgU29mdHdhcmUgRm91bmRhdGlvbiwgSW5jLgojIFRo
aXMgZmlsZSBpcyBkaXN0cmlidXRlZCB1bmRlciB0aGUgc2FtZSBsaWNlbnNlIGFzIHRoZSBldm9s
dXRpb24gcGFja2FnZS4KIyBDYXJsb3MgUGVyZWxsw7MgTWFyw61uIDxjYXJsb3NAZ25vbWUtZGIu
b3JnPiwgMjAwMC0yMDAxLgojIEjDqWN0b3IgR2FyY8OtYSDDgWx2YXJleiA8aGVjdG9yQHNjb3V0
cy1lcy5vcmc+LCAyMDAwLTIwMDIuCiMgSXNtYWVsIE9sZWEgPElzbWFlbEBvbGVhLm9yZz4sIDIw
MDEsIChyZXZpc2lvbmVzKSAyMDAzLgojIEVuZWtvIExhY3VuemEgPGVubGFyQGluYW1lLmNvbT4s
IDIwMDEtMjAwMi4KIyBIw6ljdG9yIEdhcmPDrWEgw4FsdmFyZXogPGhlY3RvckBzY291dHMtZXMu
b3JnPiwgMjAwMi4KIyBQYWJsbyBHb256YWxvIGRlbCBDYW1wbyA8cGFibG9kY0BiaWdmb290LmNv
bT4sMjAwMyAocmV2aXNpw7NuKS4KIyBGcmFuY2lzY28gSmF2aWVyIEYuIFNlcnJhZG9yIDxzZXJy
YWRvckBjdnMuZ25vbWUub3JnPiwgMjAwMywgMjAwNC4KIwojCm1zZ2lkICIiCm1zZ3N0ciAiIgoi
UHJvamVjdC1JZC1WZXJzaW9uOiBlc1xuIgoiUE9ULUNyZWF0aW9uLURhdGU6IDIwMDQtMDgtMTcg
MTE6MTArMDIwMFxuIgoiUE8tUmV2aXNpb24tRGF0ZTogMjAwNS0wNC0wNyAxMzoyMiswMDAwXG4i
CiJMYXN0LVRyYW5zbGF0b3I6IENhcmxvcyBQZXJlbGzDsyBNYXLDrW4gPGNhcmxvc0BjYW5vbmlj
YWwuY29tPlxuIgoiTGFuZ3VhZ2UtVGVhbTogU3BhbmlzaCA8dHJhZHVjdG9yZXNAZXMuZ25vbWUu
b3JnPlxuIgoiTUlNRS1WZXJzaW9uOiAxLjBcbiIKIkNvbnRlbnQtVHlwZTogdGV4dC9wbGFpbjsg
Y2hhcnNldD1VVEYtOFxuIgoiQ29udGVudC1UcmFuc2Zlci1FbmNvZGluZzogOGJpdFxuIgoiUmVw
b3J0LU1zZ2lkLUJ1Z3MtVG86IHNlcnJhZG9yQGhpc3BhbGludXguZXNcbiIKIlgtR2VuZXJhdG9y
OiBSb3NldHRhIChodHRwOi8vbGF1bmNocGFkLnVidW50dS5jb20vcm9zZXR0YS8pXG4iCiJQbHVy
YWwtRm9ybXM6IG5wbHVyYWxzPTI7IHBsdXJhbD0obiAhPSAxKTtcbiIKCiM6IGExMXkvYWRkcmVz
c2Jvb2svZWEtYWRkcmVzc2Jvb2stdmlldy5jOjk0CiM6IGExMXkvYWRkcmVzc2Jvb2svZWEtYWRk
cmVzc2Jvb2stdmlldy5jOjEwMwojOiBhMTF5L2FkZHJlc3Nib29rL2VhLW1pbmljYXJkLXZpZXcu
YzoxMTkKbXNnaWQgImV2b2x1dGlvbiBhZGRyZXNzYm9vayIKbXNnc3RyICJsaWJyZXRhIGRlIGRp
cmVjY2lvbmVzIGRlIEV2b2x1dGlvbiIKCiM6IGExMXkvYWRkcmVzc2Jvb2svZWEtbWluaWNhcmQt
dmlldy5jOjEwMQptc2dpZCAiY3VycmVudCBhZGRyZXNzYm9vayBmb2xkZXIiCm1zZ3N0ciAiY2Fy
cGV0YSBkZSBsaWJyZXRhcyBkZSBkaXJlY2Npb25lcyBhY3R1YWwiCgojOiBhMTF5L2FkZHJlc3Ni
b29rL2VhLW1pbmljYXJkLXZpZXcuYzoxMDIKIywgZnV6enkKbXNnaWQgImhhdmUgIgptc2dzdHIg
InRpZW5lIgoKIzogYTExeS9hZGRyZXNzYm9vay9lYS1taW5pY2FyZC12aWV3LmM6MTAyCm1zZ2lk
ICJoYXMgIgptc2dzdHIgIiIKCiM6IGExMXkvYWRkcmVzc2Jvb2svZWEtbWluaWNhcmQtdmlldy5j
OjEwNAptc2dpZCAiIGNhcmRzIgptc2dzdHIgIiB0YXJqZXRhcyIKCiM6IGExMXkvYWRkcmVzc2Jv
b2svZWEtbWluaWNhcmQtdmlldy5jOjEwNAptc2dpZCAiIGNhcmQiCm1zZ3N0ciAiIgoKIzogYTEx
eS9hZGRyZXNzYm9vay9lYS1taW5pY2FyZC12aWV3LmM6MTA1Cm1zZ2lkICJjb250YWN0J3MgaGVh
ZGVyOiAiCm1zZ3N0ciAiIgoKIzogYTExeS9hZGRyZXNzYm9vay9lYS1taW5pY2FyZC5jOjE2Ngpt
c2dpZCAiZXZvbHV0aW9uIG1pbmljYXJkIgptc2dzdHIgIiIKCiMuIGFkZHJlc3Nib29rOmxkYXAt
aW5pdCBwcmltYXJ5CiM6IGFkZHJlc3Nib29rL2FkZHJlc3Nib29rLWVycm9ycy54bWwuaDoyCm1z
Z2lkICJUaGlzIGFkZHJlc3Nib29rIGNvdWxkIG5vdCBiZSBvcGVuZWQuIgptc2dzdHIgIiIKCiMu
IGFkZHJlc3Nib29rOmxkYXAtaW5pdCBzZWNvbmRhcnkKIzogYWRkcmVzc2Jvb2svYWRkcmVzc2Jv
b2stZXJyb3JzLnhtbC5oOjQKbXNnaWQgIiIKIlRoaXMgYWRkcmVzc2Jvb2sgc2VydmVyIG1pZ2h0
IHVucmVhY2hhYmxlIG9yIHRoZSBzZXJ2ZXIgbmFtZSBtYXkgYmUgIgoibWlzc3BlbGxlZCBvciB5
b3VyIG5ldHdvcmsgY29ubmVjdGlvbiBjb3VsZCBiZSBkb3duLiIKbXNnc3RyICIiCgojLiBhZGRy
ZXNzYm9vazpsZGFwLWF1dGggcHJpbWFyeQojOiBhZGRyZXNzYm9vay9hZGRyZXNzYm9vay1lcnJv
cnMueG1sLmg6Ngptc2dpZCAiRmFpbGVkIHRvIGF1dGhlbnRpY2F0ZSB3aXRoIExEQVAgc2VydmVy
LiIKbXNnc3RyICIiCgojLiBhZGRyZXNzYm9vazpsZGFwLWF1dGggc2Vjb25kYXJ5CiM6IGFkZHJl
c3Nib29rL2FkZHJlc3Nib29rLWVycm9ycy54bWwuaDo4Cm1zZ2lkICIiCiJDaGVjayB0byBtYWtl
IHN1cmUgeW91ciBwYXNzd29yZCBpcyBzcGVsbGVkIGNvcnJlY3RseSBhbmQgdGhhdCB5b3UgYXJl
IHVzaW5nICIKImEgc3VwcG9ydGVkIGxvZ2luIG1ldGhvZC4gUmVtZW1iZXIgdGhhdCBtYW55IHBh
c3N3b3JkcyBhcmUgY2FzZSBzZW5zaXRpdmU7ICIKInlvdXIgY2FwcyBsb2NrIG1pZ2h0IGJlIG9u
LiIKbXNnc3RyICIiCgojOiBhZGRyZXNzYm9vay9ndWkvY29tcG9uZW50L2FkZHJlc3Nib29rLW1p
Z3JhdGUuYzoxMjQKIzogY2FsZW5kYXIvZ3VpL21pZ3JhdGlvbi5jOjE4OCBtYWlsL2VtLW1pZ3Jh
dGUuYzoxMjAxCiMsIGMtZm9ybWF0Cm1zZ2lkICJNaWdyYXRpbmcgYCVzJzoiCm1zZ3N0ciAiIgoK
IyBUaGlzIGlzIGFuIGV4YW1wbGUgb2YgY29tbWVudHRleHQgZm9yIGEgbXVsdGlsaW5lIG1zZ3Nl
dAojOiBhZGRyZXNzYm9vay9ndWkvY29tcG9uZW50L2FkZHJlc3Nib29rLW1pZ3JhdGUuYzoxMTIz
Cm1zZ2lkICIiCiJUaGUgbG9jYXRpb24gYW5kIGhpZXJhcmNoeSBvZiB0aGUgRXZvbHV0aW9uIGNv
bnRhY3QgZm9sZGVycyBoYXMgY2hhbmdlZCAiCiJzaW5jZSBFdm9sdXRpb24gMS54LlxuIgoiXG4i
CiJQbGVhc2UgYmUgcGF0aWVudCB3aGlsZSBFdm9sdXRpb24gbWlncmF0ZXMgeW91ciBmb2xkZXJz
Li4uIgptc2dzdHIgIiIKIkxhIHViaWNhY2nDs24geSBqZXJhcnF1w61hIGRlIGxhcyBjYXJwZXRh
cyBkZSBjb250YWN0b3MgZGUgRXZvbHV0aW9uIGhhICIKImNhbWJpYWRvIGRlc2RlIEV2b2x1dGlv
biAxLnguXG4iCiJcbiIKIlRlbmdhIHBhY2llbmNpYSBtaWVudHJhcyBFdm9sdXRpb24gbWlncmEg
c3VzIGNhcnBldGFzLi4uIgoKIzogYWRkcmVzc2Jvb2svZ3VpL3dpZGdldHMvZS1hZGRyZXNzYm9v
ay1tb2RlbC5jOjE1MQojLCBjLWZvcm1hdAptc2dpZCAiJWQgY29udGFjdCIKbXNnaWRfcGx1cmFs
ICIlZCBjb250YWN0cyIKbXNnc3RyWzBdICIlZCBjb250YWN0byIKbXNnc3RyWzFdICIlZCBjb250
YWN0b3MiCgojOiBhZGRyZXNzYm9vay9ndWkvd2lkZ2V0cy9lYWItZ3VpLXV0aWwuYzoyNzUKIywg
Yy1mb3JtYXQKbXNnaWQgIiIKIk9wZW5pbmcgJWQgY29udGFjdCB3aWxsIG9wZW4gJWQgbmV3IHdp
bmRvdyBhcyB3ZWxsLlxuIgoiRG8geW91IHJlYWxseSB3YW50IHRvIGRpc3BsYXkgdGhpcyBjb250
YWN0PyIKbXNnaWRfcGx1cmFsICIiCiJPcGVuaW5nICVkIGNvbnRhY3RzIHdpbGwgb3BlbiAlZCBu
ZXcgd2luZG93cyBhcyB3ZWxsLlxuIgoiRG8geW91IHJlYWxseSB3YW50IHRvIGRpc3BsYXkgYWxs
IG9mIHRoZXNlIGNvbnRhY3RzPyIKbXNnc3RyWzBdICIiCiJBYnJpciAlZCBjb250YWN0byBhYnJp
csOhICVkIHZlbnRhbmFzIG51ZXZhcyB0YW1iacOpbi5cbiIKIsK/UXVpZXJlIHJlYWxtZW50ZSBt
b3N0cmFyIGVzdGUgY29udGFjdG8/Igptc2dzdHJbMV0gIiIKIkFicmlyICVkIGNvbnRhY3RvcyBh
YnJpcsOhICVkIHZlbnRhbmFzIG51ZXZhcyB0YW1iacOpbi5cbiIKIsK/UXVpZXJlIHJlYWxtZW50
ZSBtb3N0cmFyIHRvZG9zIGVzdG9zIGNvbnRhY3Rvcz8iCgojOiBhZGRyZXNzYm9vay9ndWkvd2lk
Z2V0cy9mb28uYzozNDUKIywgZnV6enksIGMtZm9ybWF0Cm1zZ2lkICIlZCBmb28iCm1zZ2lkX3Bs
dXJhbCAiJWQgYmFycyIKbXNnc3RyWzBdICIlZCBmb28iCm1zZ3N0clsxXSAiIgoKIyBzdGFydCBw
by1ncm91cDogY29tbW9uCiMgc3RhcnQgcG8tZ3JvdXA6IGNvbW1vbgojLiB4Z3JvdXAoY29tbW9u
KQojOiBlbmNmcy9GaWxlVXRpbHMuY3BwOjEwNDQKbXNnaWQgIkVuY0ZTIFBhc3N3b3JkOiAiCm1z
Z3N0ciAiQ29udHJhc2XDsWEgZGUgRW5jRlM6ICIKCiMuIHhncm91cCh1c2FnZSkKIzogZW5jZnMv
bWFpbi5jcHA6MzQwCm1zZ2lkICIiCiJXaGVuIHNwZWNpZnlpbmcgZGFlbW9uIG1vZGUsIHlvdSBt
dXN0IHVzZSBhYnNvbHV0ZSBwYXRocyAoYmVnaW5uaW5nIHdpdGggJy8nKSIKbXNnc3RyICIiCgoj
LiB4Z3JvdXAoc2V0dXApCiM6IGVuY2ZzL0ZpbGVVdGlscy5jcHA6NTM1CiMsIGMtZm9ybWF0Cm1z
Z2lkICIiCiJQbGVhc2Ugc2VsZWN0IGEga2V5IHNpemUgaW4gYml0cy4gIFRoZSBjaXBoZXIgeW91
IGhhdmUgY2hvc2VuXG4iCiJzdXBwb3J0cyBzaXplcyBmcm9tICVpIHRvICVpIGJpdHMgaW4gaW5j
cmVtZW50cyBvZiAlaSBiaXRzLlxuIgoiRm9yIGV4YW1wbGU6ICIKbXNnc3RyICIiCgojOiBlbmNm
cy9lbmNmc2N0bC5jcHA6MzQ2CiMsIGMtZm9ybWF0Cm1zZ2lkICJGb3VuZCAlaSBpbnZhbGlkIGZp
bGUuIgptc2dpZF9wbHVyYWwgIkZvdW5kICVpIGludmFsaWQgZmlsZXMuIgptc2dzdHJbMF0gIiIK
bXNnc3RyWzFdICIiCgojfiBtc2dpZCAiX0FkZCBHcm91cCIKI34gbXNnc3RyICJfQcOxYWRpciBn
cnVwbyIK
', 13, '2005-04-07 13:18:57.59704', 2);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'pofile'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'pomsgset'::pg_catalog.regclass;

INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (1, 1, 1, true, false, false, '', 1);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (2, 2, 1, true, false, false, '', 2);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (3, 3, 1, true, false, true, '', 3);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (4, 4, 1, false, false, false, '', 4);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (10, 10, 1, false, false, false, '', 10);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (11, 11, 1, false, false, false, '', 11);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (5, 5, 1, true, false, false, '', 5);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (12, 12, 1, false, false, false, '', 12);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (6, 6, 1, false, false, false, '', 6);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (13, 13, 1, false, false, false, '', 13);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (7, 7, 1, false, false, false, '', 7);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (8, 8, 1, false, false, false, '', 8);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (9, 9, 1, false, false, false, '', 9);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (14, 14, 1, true, false, false, ' This is an example of commenttext for a multiline msgset', 14);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (15, 15, 1, true, false, false, '', 15);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (16, 16, 1, true, false, false, '', 16);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (17, 17, 1, false, false, true, '', 17);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (21, 21, 1, false, false, false, '', 21);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (18, 18, 1, true, false, false, ' start po-group: common
 start po-group: common', 18);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (19, 19, 1, false, false, false, '', 19);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (20, 20, 1, false, false, false, '', 20);
INSERT INTO pomsgset (id, "sequence", pofile, iscomplete, obsolete, fuzzy, commenttext, potmsgset) VALUES (22, 22, 1, true, true, false, '', 23);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'pomsgset'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'pomsgidsighting'::pg_catalog.regclass;

INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (1, 1, 1, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (2, 2, 2, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (3, 3, 3, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (4, 4, 4, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (5, 5, 5, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (6, 6, 6, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (7, 7, 7, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (8, 8, 8, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (9, 9, 9, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (10, 10, 10, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (11, 11, 11, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (12, 12, 12, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (13, 13, 13, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (14, 14, 14, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (15, 15, 15, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (17, 16, 17, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (19, 17, 19, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (21, 18, 21, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (22, 19, 22, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (23, 20, 23, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (24, 21, 24, '2005-03-18 18:31:17.54732', '2005-03-18 18:31:17.54732', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (26, 22, 26, '2005-04-07 13:16:19.484578', '2005-04-07 13:16:19.484578', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (16, 15, 16, '2005-03-18 18:31:17.54732', '2005-04-07 13:19:17.601068', true, 1);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (18, 16, 18, '2005-03-18 18:31:17.54732', '2005-04-07 13:19:17.601068', true, 1);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (20, 17, 20, '2005-03-18 18:31:17.54732', '2005-04-07 13:19:17.601068', true, 1);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (27, 23, 27, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0);
INSERT INTO pomsgidsighting (id, potmsgset, pomsgid, datefirstseen, datelastseen, inlastrevision, pluralform) VALUES (25, 21, 25, '2005-03-18 18:31:17.54732', '2005-04-07 13:19:17.601068', true, 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'pomsgidsighting'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'potranslationsighting'::pg_catalog.regclass;

INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (1, 1, 1, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (2, 2, 2, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (3, 3, 3, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (4, 5, 4, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (5, 14, 5, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (6, 15, 6, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (7, 15, 7, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 1, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (8, 16, 8, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (9, 16, 9, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 1, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (10, 17, 10, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (11, 18, 11, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);
INSERT INTO potranslationsighting (id, pomsgset, potranslation, license, datefirstseen, datelastactive, inlastrevision, pluralform, active, origin, person) VALUES (12, 22, 12, NULL, '2005-04-07 13:19:17.601068', '2005-04-07 13:19:17.601068', true, 0, true, 1, 13);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'potranslationsighting'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'pocomment'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'pocomment'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'translationeffort'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'translationeffort'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'translationeffortpotemplate'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'translationeffortpotemplate'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'posubscription'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'posubscription'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bug'::pg_catalog.regclass;

INSERT INTO bug (id, datecreated, name, title, description, "owner", duplicateof, communityscore, communitytimestamp, activityscore, activitytimestamp, hits, hitstimestamp, shortdesc, fti, private) VALUES (1, '2004-09-24 20:58:04.553583', NULL, 'Firefox does not support SVG', 'The SVG standard 1.0 is complete, and draft implementations for Firefox exist. One of these implementations needs to be integrated with the base install of Firefox. Ideally, the implementation needs to include support for the manipulation of SVG objects from JavaScript to enable interactive and dynamic SVG drawings.', 12, NULL, 0, '2004-09-24 00:00:00', 0, '2004-09-24 00:00:00', 0, '2004-09-24 00:00:00', 'Firefox needs to support embedded SVG images, now that the standard has been finalised.', '''1.0'':23 ''one'':32 ''svg'':5,11,21,57,66 ''base'':42 ''draw'':67 ''imag'':12 ''need'':7,36,49 ''draft'':27 ''dynam'':65 ''embed'':10 ''enabl'':62 ''exist'':31 ''ideal'':46 ''includ'':51 ''instal'':43 ''integr'':39 ''object'':58 ''complet'':25 ''finalis'':19 ''firefox'':1,6,30,45 ''manipul'':55 ''support'':4,9,52 ''interact'':63 ''standard'':16,22 ''implement'':28,35,48 ''javascript'':60', false);
INSERT INTO bug (id, datecreated, name, title, description, "owner", duplicateof, communityscore, communitytimestamp, activityscore, activitytimestamp, hits, hitstimestamp, shortdesc, fti, private) VALUES (2, '2004-09-24 20:58:04.572546', 'blackhole', 'Blackhole Trash folder', 'The Trash folder seems to have significant problems! At the moment, dragging an item to the trash results in immediate deletion. The item does not appear in the Trash, it is just deleted from my hard disk. There is no undo or ability to recover the deleted file. Help!', 12, NULL, 0, '2004-09-24 00:00:00', 0, '2004-09-24 00:00:00', 0, '2004-09-24 00:00:00', 'Everything put into the folder "Trash" disappears!', '''put'':6 ''abil'':54 ''disk'':48 ''drag'':23 ''file'':59 ''hard'':47 ''help'':60 ''item'':25,34 ''seem'':15 ''undo'':52 ''delet'':32,44,58 ''recov'':56 ''trash'':3,10,13,28,40 ''appear'':37 ''folder'':4,9,14 ''immedi'':31 ''moment'':22 ''result'':29 ''everyth'':5 ''problem'':19 ''blackhol'':1,2 ''signific'':18 ''disappear'':11', false);
INSERT INTO bug (id, datecreated, name, title, description, "owner", duplicateof, communityscore, communitytimestamp, activityscore, activitytimestamp, hits, hitstimestamp, shortdesc, fti, private) VALUES (3, '2004-10-05 00:00:00', NULL, 'Bug Title Test', 'y idu yifdxhfgffxShirtpkdf jlkdsj;lkd lkjd hlkjfds gkfdsg kfd glkfd gifdsytoxdiytxoiufdytoidxf yxoigfyoigfxuyfxoiug yxoiuy oiugf hyoifxugyoixgfuy xoiuyxoiyxoifuy xoShirtpkdf jlkdsj;lkd lkjd hlkjfds gkfdsg kfd glkfd gifdsytoxdiytxoiufdytoidxf yxoigfyoigfxuyfxoiug yxoiuy oiugf hyoifxugyoixgfuy xoiuyxoiyxoifuy xo
Shirtpkdf jlkdsj;lkd lkjd hlkjfds gkfdsg kfd glkfd gifdsytoxdiytxoiufdytoidxf yxoigfyoigfxuyfxoiug yxoiuy oiugf hyoifxugyoixgfuy xoiuyxoiyxoifuy xoShirtpkdf jlkdsj;lkd lkjd hlkjfds gkfdsg kfd glkfd gifdsytoxdiytxoiufdytoidxf yxoigfyoigfxuyfxoiug yxoiuy oiugf hyoifxugyoixgfuy xoiuyxoiyxoifuy xo

Shirtpkdf jlkdsj;lkd lkjd hlkjfds gkfdsg kfd glkfd gifdsytoxdiytxoiufdytoidxf yxoigfyoigfxuyfxoiug yxoiuy oiugf hyoifxugyoixgfuy xoiuyxoiyxoifuy xoShirtpkdf jlkdsj;lkd lkjd hlkjfds gkfdsg kfd glkfd gifdsytoxdiytxoiufdytoidxf yxoigfyoigfxuyfxoiug yxoiuy oiugf hyoifxugyoixgfuy xoiuyxoiyxoifuy xo', 16, NULL, 0, '2004-10-05 00:00:00', 0, '2004-10-05 00:00:00', 0, '2004-10-05 00:00:00', 'Shirtpkdf jlkdsj;lkd lkjd hlkjfds gkfdsg kfd glkfd gifdsytoxdiytxoiufdytoidxf yxoigfyoigfxuyfxoiug yxoiuy oiugf hyoifxugyoixgfuy xoiuyxoiyxoifuy xo', '''y'':19 ''xo'':18,49,78,107 ''bug'':1 ''idu'':20 ''kfd'':10,27,41,56,70,85,99 ''lkd'':6,23,37,52,66,81,95 ''lkjd'':7,24,38,53,67,82,96 ''test'':3 ''titl'':2 ''glkfd'':11,28,42,57,71,86,100 ''oiugf'':15,32,46,61,75,90,104 ''gkfdsg'':9,26,40,55,69,84,98 ''jlkdsj'':5,22,36,51,65,80,94 ''yxoiuy'':14,31,45,60,74,89,103 ''hlkjfds'':8,25,39,54,68,83,97 ''shirtpkdf'':4,50,79 ''xoshirtpkdf'':35,64,93 ''xoiuyxoiyxoifuy'':17,34,48,63,77,92,106 ''hyoifxugyoixgfuy'':16,33,47,62,76,91,105 ''yifdxhfgffxshirtpkdf'':21 ''yxoigfyoigfxuyfxoiug'':13,30,44,59,73,88,102 ''gifdsytoxdiytxoiufdytoidxf'':12,29,43,58,72,87,101', false);
INSERT INTO bug (id, datecreated, name, title, description, "owner", duplicateof, communityscore, communitytimestamp, activityscore, activitytimestamp, hits, hitstimestamp, shortdesc, fti, private) VALUES (4, '2005-01-14 00:00:00', NULL, 'Reflow problems with complex page layouts', NULL, 12, NULL, 0, '2005-01-14 17:20:12.820778', 0, '2005-01-14 17:20:12.820778', 0, '2005-01-14 17:20:12.820778', NULL, '''page'':5 ''layout'':6 ''reflow'':1 ''complex'':4 ''problem'':2', false);
INSERT INTO bug (id, datecreated, name, title, description, "owner", duplicateof, communityscore, communitytimestamp, activityscore, activitytimestamp, hits, hitstimestamp, shortdesc, fti, private) VALUES (5, '2005-01-14 00:00:00', NULL, 'Firefox install instructions should be complete', NULL, 12, NULL, 0, '2005-01-14 17:27:03.702622', 0, '2005-01-14 17:27:03.702622', 0, '2005-01-14 17:27:03.702622', NULL, '''instal'':2 ''complet'':6 ''firefox'':1 ''instruct'':3', false);
INSERT INTO bug (id, datecreated, name, title, description, "owner", duplicateof, communityscore, communitytimestamp, activityscore, activitytimestamp, hits, hitstimestamp, shortdesc, fti, private) VALUES (6, '2005-01-14 00:00:00', NULL, 'Firefox crashes when Save As dialog for a nonexistent window is closed', NULL, 12, NULL, 0, '2005-01-14 17:35:39.548665', 0, '2005-01-14 17:35:39.548665', 0, '2005-01-14 17:35:39.548665', NULL, '''save'':4 ''close'':12 ''crash'':2 ''dialog'':6 ''window'':10 ''firefox'':1 ''nonexist'':9', false);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bug'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugsubscription'::pg_catalog.regclass;

INSERT INTO bugsubscription (id, person, bug, subscription) VALUES (1, 11, 1, 2);
INSERT INTO bugsubscription (id, person, bug, subscription) VALUES (2, 2, 1, 3);
INSERT INTO bugsubscription (id, person, bug, subscription) VALUES (3, 10, 1, 3);
INSERT INTO bugsubscription (id, person, bug, subscription) VALUES (4, 12, 1, 1);
INSERT INTO bugsubscription (id, person, bug, subscription) VALUES (5, 11, 2, 2);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugsubscription'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugactivity'::pg_catalog.regclass;

INSERT INTO bugactivity (id, bug, datechanged, person, whatchanged, oldvalue, newvalue, message) VALUES (1, 1, '2004-09-24 00:00:00', 1, 'title', 'A silly problem', 'An odd problem', 'Decided problem wasn''t silly after all');
INSERT INTO bugactivity (id, bug, datechanged, person, whatchanged, oldvalue, newvalue, message) VALUES (2, 4, '2005-01-14 00:00:00', 12, 'bug', NULL, NULL, 'added bug');
INSERT INTO bugactivity (id, bug, datechanged, person, whatchanged, oldvalue, newvalue, message) VALUES (3, 5, '2005-01-14 00:00:00', 12, 'bug', NULL, NULL, 'added bug');
INSERT INTO bugactivity (id, bug, datechanged, person, whatchanged, oldvalue, newvalue, message) VALUES (4, 5, '2005-01-14 00:00:00', 12, 'firefox: assignee', NULL, 'name12', 'XXX: not yet implemented');
INSERT INTO bugactivity (id, bug, datechanged, person, whatchanged, oldvalue, newvalue, message) VALUES (5, 6, '2005-01-14 00:00:00', 12, 'bug', NULL, NULL, 'added bug');
INSERT INTO bugactivity (id, bug, datechanged, person, whatchanged, oldvalue, newvalue, message) VALUES (6, 6, '2005-01-14 00:00:00', 12, 'firefox: severity', 'Normal', 'Critical', 'XXX: not yet implemented');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugactivity'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugexternalref'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugexternalref'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugtrackertype'::pg_catalog.regclass;

INSERT INTO bugtrackertype (id, name, title, description, homepage, "owner") VALUES (1, 'bugzilla', 'BugZilla', 'Dave Miller''s Labour of Love, the Godfather of Open Source project issue tracking.', 'http://www.bugzilla.org/', 12);
INSERT INTO bugtrackertype (id, name, title, description, homepage, "owner") VALUES (2, 'debbugs', 'Debbugs System', 'Debbugs Bug Tracking System', 'http://bugs.debian.org/', 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugtrackertype'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugtracker'::pg_catalog.regclass;

INSERT INTO bugtracker (id, bugtrackertype, name, title, shortdesc, baseurl, "owner", contactdetails) VALUES (1, 1, 'mozilla.org', 'The Mozilla.org Bug Tracker', 'The Mozilla.org bug tracker is the grand-daddy of bugzillas. This is where Bugzilla was conceived, born and raised. This bugzilla instance covers all Mozilla products such as Firefox, Thunderbird and Bugzilla itself.', 'http://bugzilla.mozilla.org/', 12, 'Carrier pigeon only');
INSERT INTO bugtracker (id, bugtrackertype, name, title, shortdesc, baseurl, "owner", contactdetails) VALUES (2, 1, 'gnome-bugzilla', 'GnomeGBug GTracker', 'This is the Gnome Bugzilla bug tracking system. It covers all the applications in the Gnome Desktop and Gnome Fifth Toe.', 'http://bugzilla.gnome.org/', 16, 'Jeff Waugh, in his pants.');
INSERT INTO bugtracker (id, bugtrackertype, name, title, shortdesc, baseurl, "owner", contactdetails) VALUES (3, 2, 'debbugs', 'Debian Bug tracker', 'Bug tracker for debian project.', 'http://bugs.debian.org', 1, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugtracker'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugwatch'::pg_catalog.regclass;

INSERT INTO bugwatch (id, bug, bugtracker, remotebug, remotestatus, lastchanged, lastchecked, datecreated, "owner") VALUES (1, 2, 1, '42', 'FUBAR', '2004-09-24 20:58:04.740841', '2004-09-24 20:58:04.740841', '2004-09-24 20:58:04.740841', 12);
INSERT INTO bugwatch (id, bug, bugtracker, remotebug, remotestatus, lastchanged, lastchecked, datecreated, "owner") VALUES (2, 1, 1, '2000', '', '2004-10-04 00:00:00', '2004-10-04 00:00:00', '2004-10-04 00:00:00', 1);
INSERT INTO bugwatch (id, bug, bugtracker, remotebug, remotestatus, lastchanged, lastchecked, datecreated, "owner") VALUES (3, 1, 1, '123543', '', '2004-10-04 00:00:00', '2004-10-04 00:00:00', '2004-10-04 00:00:00', 1);
INSERT INTO bugwatch (id, bug, bugtracker, remotebug, remotestatus, lastchanged, lastchecked, datecreated, "owner") VALUES (4, 2, 2, '3224', '', '2004-10-05 00:00:00', '2004-10-05 00:00:00', '2004-10-05 00:00:00', 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugwatch'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'projectbugtracker'::pg_catalog.regclass;

INSERT INTO projectbugtracker (project, bugtracker, id) VALUES (5, 2, 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'projectbugtracker'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'buglabel'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'buglabel'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugrelationship'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugrelationship'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'message'::pg_catalog.regclass;

INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (7, '2005-01-14 17:20:12.820778', 'Reflow problems with complex page layouts', 12, NULL, NULL, '<20050114172012.6687.51124.malonedeb@localhost.localdomain>', '''page'':5 ''layout'':6 ''reflow'':1 ''complex'':4 ''problem'':2', NULL);
INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (8, '2005-01-14 17:27:03.702622', 'Firefox install instructions should be complete', 12, NULL, NULL, '<20050114172703.6687.71983.malonedeb@localhost.localdomain>', '''instal'':2 ''complet'':6 ''firefox'':1 ''instruct'':3', NULL);
INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (9, '2005-01-14 17:35:39.548665', 'Firefox crashes when Save As dialog for a nonexistent window is closed', 12, NULL, NULL, '<20050114173539.6687.81610.malonedeb@localhost.localdomain>', '''save'':4 ''close'':12 ''crash'':2 ''dialog'':6 ''window'':10 ''firefox'':1 ''nonexist'':9', NULL);
INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (1, '2004-09-24 20:58:04.684057', 'PEBCAK', NULL, NULL, NULL, 'foo@example.com-332342--1231', '''pebcak'':1', NULL);
INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (3, '2004-09-24 21:17:17.153792', 'Reproduced on AIX', 12, NULL, NULL, 'sdsdfsfd', '''aix'':3 ''reproduc'':1', NULL);
INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (4, '2004-09-24 21:24:03.922564', 'Re: Reproduced on AIX', 12, NULL, NULL, 'sdfssfdfsd', '''re'':1 ''aix'':4 ''reproduc'':2', NULL);
INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (5, '2004-09-24 21:29:27.407354', 'Fantastic idea, I''d really like to see this', 12, NULL, NULL, 'dxssdfsdgf', '''d'':4 ''see'':8 ''idea'':2 ''like'':6 ''realli'':5 ''fantast'':1', NULL);
INSERT INTO message (id, datecreated, title, "owner", parent, distribution, rfc822msgid, fti, raw) VALUES (6, '2004-09-24 21:35:20.125564', 'Strange bug with duplicate messages.', 12, NULL, NULL, 'sdfsfwew', '''bug'':2 ''duplic'':4 ''messag'':5 ''strang'':1', NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'message'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugattachment'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugattachment'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'componentselection'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'componentselection'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'sectionselection'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'sectionselection'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugproductinfestation'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugproductinfestation'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugpackageinfestation'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugpackageinfestation'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'distroreleasequeue'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'distroreleasequeue'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'distroreleasequeuesource'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'distroreleasequeuesource'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'distroreleasequeuebuild'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'distroreleasequeuebuild'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'personlanguage'::pg_catalog.regclass;

INSERT INTO personlanguage (id, person, "language") VALUES (1, 13, 387);
INSERT INTO personlanguage (id, person, "language") VALUES (4, 14, 449);
INSERT INTO personlanguage (id, person, "language") VALUES (3, 14, 196);
INSERT INTO personlanguage (id, person, "language") VALUES (2, 13, 68);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'personlanguage'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'potmsgset'::pg_catalog.regclass;

INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (22, 26, 22, 1, '', 'modules/aggregator.module:15', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (1, 1, 1, 1, '', 'a11y/addressbook/ea-addressbook-view.c:94
a11y/addressbook/ea-addressbook-view.c:103
a11y/addressbook/ea-minicard-view.c:119', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (2, 2, 2, 1, '', 'a11y/addressbook/ea-minicard-view.c:101', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (3, 3, 3, 1, '', 'a11y/addressbook/ea-minicard-view.c:102', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (4, 4, 4, 1, '', 'a11y/addressbook/ea-minicard-view.c:102', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (9, 9, 9, 1, '', 'addressbook/addressbook-errors.xml.h:2', 'addressbook:ldap-init primary', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (10, 10, 10, 1, '', 'addressbook/addressbook-errors.xml.h:4', 'addressbook:ldap-init secondary', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (11, 11, 11, 1, '', 'addressbook/addressbook-errors.xml.h:6', 'addressbook:ldap-auth primary', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (12, 12, 12, 1, '', 'addressbook/addressbook-errors.xml.h:8', 'addressbook:ldap-auth secondary', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (13, 13, 13, 1, '', 'addressbook/gui/component/addressbook-migrate.c:124
calendar/gui/migration.c:188 mail/em-migrate.c:1201', '', 'c-format');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (5, 5, 5, 1, '', 'a11y/addressbook/ea-minicard-view.c:104', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (6, 6, 6, 1, '', 'a11y/addressbook/ea-minicard-view.c:104', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (7, 7, 7, 1, '', 'a11y/addressbook/ea-minicard-view.c:105', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (8, 8, 8, 1, '', 'a11y/addressbook/ea-minicard.c:166', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (14, 14, 14, 1, '', 'addressbook/gui/component/addressbook-migrate.c:1123', '', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (15, 15, 15, 1, '', 'addressbook/gui/widgets/e-addressbook-model.c:151', '', 'c-format');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (16, 17, 16, 1, '', 'addressbook/gui/widgets/eab-gui-util.c:275', '', 'c-format');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (17, 19, 17, 1, '', 'addressbook/gui/widgets/foo.c:345', '', 'c-format');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (20, 23, 20, 1, '', 'encfs/FileUtils.cpp:535', 'xgroup(setup)', 'c-format');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (21, 24, 21, 1, '', 'encfs/encfsctl.cpp:346', '', 'c-format');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (18, 21, 18, 1, ' start po-group: common', 'encfs/FileUtils.cpp:1044', 'xgroup(common)', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (19, 22, 19, 1, '', 'encfs/main.cpp:340', 'xgroup(usage)', '');
INSERT INTO potmsgset (id, primemsgid, "sequence", potemplate, commenttext, filereferences, sourcecomment, flagscomment) VALUES (23, 27, 0, 1, NULL, '', '', '');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'potmsgset'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'launchpaddatabaserevision'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'launchpaddatabaserevision'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bounty'::pg_catalog.regclass;

INSERT INTO bounty (id, name, title, summary, description, usdvalue, difficulty, duration, reviewer, datecreated, "owner", deadline, claimant, dateclaimed) VALUES (1, 'foomatic-widgets', 'Make foomatic have better widgets.', 'Foomatic needs to have way better widgets. The current ones are SO WinXP. Eeewww. Maybe we can get some of that K-Bling that I saw in Kubuntu?', 'The widgets need to be particularly polished, since foomatic is going to be the default foomaster on the desktop for the planet.', 453.44, 65, '7 days', 16, '2005-03-11 09:17:40.585397', 16, NULL, NULL, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bounty'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugmessage'::pg_catalog.regclass;

INSERT INTO bugmessage (id, bug, message) VALUES (1, 2, 1);
INSERT INTO bugmessage (id, bug, message) VALUES (2, 1, 3);
INSERT INTO bugmessage (id, bug, message) VALUES (3, 1, 4);
INSERT INTO bugmessage (id, bug, message) VALUES (4, 2, 5);
INSERT INTO bugmessage (id, bug, message) VALUES (5, 2, 6);
INSERT INTO bugmessage (id, bug, message) VALUES (6, 4, 7);
INSERT INTO bugmessage (id, bug, message) VALUES (7, 5, 8);
INSERT INTO bugmessage (id, bug, message) VALUES (8, 6, 9);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugmessage'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'cveref'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'cveref'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'karma'::pg_catalog.regclass;

INSERT INTO karma (id, karmatype, datecreated, person, points) VALUES (1, 4, '2005-01-14 12:20:12.820778', 12, 10);
INSERT INTO karma (id, karmatype, datecreated, person, points) VALUES (2, 4, '2005-01-14 12:27:03.702622', 12, 10);
INSERT INTO karma (id, karmatype, datecreated, person, points) VALUES (3, 4, '2005-01-14 12:35:39.548665', 12, 10);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'karma'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'sshkey'::pg_catalog.regclass;

INSERT INTO sshkey (id, person, keytype, keytext, "comment") VALUES (1, 12, 2, 'AAAAB3NzaC1kc3MAAAEBAPfhCA15ZaT08brwVXwpJjcZT6QFIipzF1sGy57HY7QPi/W+uljr1VcCHzWdlSmda7YpTCTx0NFYYQIccQRGX6zYL8v1w9FSRCAnxxUJmqEhsUDFYFdVTa9uLCrs3MSbmh7wwFPdRrGrO6X5x7T4dMZQwykSZrOVdpLcCHRgrMZslLomIAjERn6OAQNiGFz7B2tEi/3Soqd52bGJwOtGymRiAXkPSLbH7KfzSCe34ytdh6BD+4SrgSoa+TL3VDV70QAdlOFXD42ZHl3Sc0Tde4LbZeYq2Uf84DOATLZBbOYpRSqTLkM9XngpnvCRVb6dxEQfgODDw783tEuPpySLj2EAAAAVANpUVgivDjt9gFibN/AXfYy1meeBAAABAB6FtnMywmWZg2lr2I3nDfE5U5QbGUQB/ZEP98ZkSkhOcF29VlnGOxyb2/VZbVTLa/btlPF82L4An/c8VKtKZnel7LnAlMoArdgzQNXGVQQVtnaWwM26ydgDzkSSIes3elNZgsfnPRBvaF0ol9Tqju0rNGKjnr3ZOX/NX+42bxpjRnxYj1h56yP2jKKeGfjorI6JK1YfqBAiTxzaDMzSpknnrbztaKJoh7IFqMMOp9ANSFh7H106pEaCv3ebCTJZprtWqNKjb2zum7OQPRz3upA0qx22ocTokjv4itXJ6yj/BvGu9qdOIQFXuB2rsFtLZtS8ATueOly0GzyeiZBx/AEAAAEBAO8jRYjL7tAYnVlO1p6UzPOicAuGCFWfNbBEDRAXoSgLNdj451jStw+eUc9ZVz7tG/XRVZsiavtFHb2cbrcfX1YOd69xi0m+IY6mo3yKt3irQRokDtt376sHoUdHgj2ozySZJgG8IJndtoS+VQQy6NdClA3fNFb96bF865eNaRYoHJO9ZI84lkWQL++MLzIuyFfCs1hSlapyyuHC8kFmF7AQdrVZvbohSbnWs+w53nIW8nAA7z21wAukvE1Pl6AQyG0e7U1sYS8Pc8dtmzJvdtVZWBl02/gqQJ7f06mFvnsN45rR1Uyxnrwl6rbFwqabZDlyD5Ac6Icbvz9SG1gBOiI=', 'andrew@trogdor');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'sshkey'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bugtask'::pg_catalog.regclass;

INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (1, 1, 1, NULL, NULL, NULL, NULL, 10, 30, 20, 5, '2004-10-11 11:07:20.330975', '2004-11-13 03:49:22.910183', 12, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (2, 1, 4, NULL, NULL, NULL, NULL, 10, 10, 20, 1, '2004-10-11 11:07:20.330975', '2004-11-13 03:49:22.910878', 12, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (3, 2, 1, NULL, NULL, NULL, NULL, 10, 20, 20, NULL, '2004-10-11 11:07:20.330975', '2004-11-13 03:49:22.908491', 12, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (4, 1, NULL, 3, NULL, 1, NULL, 20, 40, 20, NULL, '2004-10-11 11:07:20.584746', '2004-11-13 03:49:22.79024', 12, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (5, 2, NULL, 3, NULL, 1, NULL, 20, 40, 20, 12, '2004-10-11 11:07:20.584746', '2004-11-13 03:49:22.824591', 12, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (6, 3, NULL, 3, NULL, 1, NULL, 10, 20, 30, NULL, '2004-10-11 11:07:20.584746', '2004-11-13 03:49:22.825533', 16, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (13, 4, 4, NULL, NULL, NULL, NULL, 10, 30, 30, NULL, '2005-01-14 17:20:12.820778', '2005-01-14 17:20:12.820778', 12, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (14, 5, 4, NULL, NULL, NULL, NULL, 10, 30, 30, 12, '2005-01-14 17:27:03.702622', '2005-01-14 17:27:03.702622', 12, NULL);
INSERT INTO bugtask (id, bug, product, distribution, distrorelease, sourcepackagename, binarypackagename, status, priority, severity, assignee, dateassigned, datecreated, "owner", milestone) VALUES (15, 6, 4, NULL, NULL, NULL, NULL, 10, 30, 50, NULL, '2005-01-14 17:35:39.548665', '2005-01-14 17:35:39.548665', 12, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bugtask'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'logintoken'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'logintoken'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'milestone'::pg_catalog.regclass;

INSERT INTO milestone (id, product, NAME, title) VALUES (1, 4, '1.0', 'one dot zero');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'milestone'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'pushmirroraccess'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'pushmirroraccess'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'buildqueue'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'buildqueue'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'signedcodeofconduct'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'signedcodeofconduct'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'bountysubscription'::pg_catalog.regclass;

INSERT INTO bountysubscription (id, bounty, person, subscription) VALUES (1, 1, 9, 1);
INSERT INTO bountysubscription (id, bounty, person, subscription) VALUES (2, 1, 6, 3);
INSERT INTO bountysubscription (id, bounty, person, subscription) VALUES (3, 1, 1, 2);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'bountysubscription'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'productbounty'::pg_catalog.regclass;

INSERT INTO productbounty (id, bounty, product) VALUES (1, 1, 4);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'productbounty'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'distrobounty'::pg_catalog.regclass;

INSERT INTO distrobounty (id, bounty, distribution) VALUES (1, 1, 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'distrobounty'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'projectbounty'::pg_catalog.regclass;

INSERT INTO projectbounty (id, bounty, project) VALUES (1, 1, 4);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'projectbounty'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'mirror'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'mirror'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'mirrorcontent'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'mirrorcontent'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'mirrorsourcecontent'::pg_catalog.regclass;



UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'mirrorsourcecontent'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'potemplatename'::pg_catalog.regclass;

INSERT INTO potemplatename (id, name, title, description, translationdomain) VALUES (1, 'evolution-2.2', 'Main translation domain for the Evolution 2.2', 'This is a description about Evolution 2.2 POTemplateName', 'evolution-2.2');
INSERT INTO potemplatename (id, name, title, description, translationdomain) VALUES (2, 'pmount', 'pmount', NULL, 'pmount');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'potemplatename'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'maintainership'::pg_catalog.regclass;

INSERT INTO maintainership (id, distribution, sourcepackagename, maintainer) VALUES (1, 3, 1, 1);
INSERT INTO maintainership (id, distribution, sourcepackagename, maintainer) VALUES (2, 1, 9, 1);
INSERT INTO maintainership (id, distribution, sourcepackagename, maintainer) VALUES (3, 1, 14, 1);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'maintainership'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'messagechunk'::pg_catalog.regclass;

INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (3, 9, 1, 'User-Agent:       
Build Identifier: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.6) Gecko/20040207 Firefox/0.8

If a Save As dialog for a nonexistent window exists, when the dialog is closed Firefox will crash.  It''s possible to cause this to happen using the "Open With/Save As" dialog.

Reproducible: Always
Steps to Reproduce:
1. Visit http://www.mozilla.org/products/firefox/
2. Click on "Download Now!"  An "Open With/Save" dialog will appear.
4. Press OK.
5. Switch back to the "Open With/Save" dialog, and press OK again.  There are now two Save As dialogs.  This is bug 58777.
6. Close the second dialog with "Cancel"
7. Close the browser window that started all of this.
8. Close the first dialog with "Cancel".

Actual Results:  
Crash!

Expected Results:  
Not crashed.', NULL, '''1'':55 ''2'':60 ''4'':71 ''5'':74 ''6'':97 ''7'':104 ''8'':114 ''u'':8 ''en'':12 ''ok'':73,84 ''rv'':14 ''us'':13 ''1.6'':15 ''bug'':95 ''two'':89 ''use'':44 ''x11'':7 ''back'':76 ''caus'':40 ''i686'':10 ''open'':46,66,79 ''save'':20,90 ''step'':52 ''user'':2 ''58777'':96 ''agent'':3 ''alway'':51 ''build'':4 ''click'':61 ''close'':32,98,105,115 ''crash'':35,123,127 ''en-us'':11 ''exist'':27 ''first'':117 ''linux'':9 ''press'':72,83 ''start'':110 ''visit'':56 ''actual'':121 ''appear'':70 ''cancel'':103,120 ''dialog'':22,30,49,68,81,92,101,118 ''expect'':124 ''happen'':43 ''result'':122,125 ''second'':100 ''switch'':75 ''window'':26,108 ''browser'':107 ''firefox'':33 ''possibl'':38 ''user-ag'':1 ''download'':63 ''identifi'':5 ''nonexist'':25 ''reproduc'':50,54 ''with/save'':47,67,80 ''firefox/0.8'':17 ''mozilla/5.0'':6 ''gecko/20040207'':16 ''www.mozilla.org'':58 ''/products/firefox/'':59 ''www.mozilla.org/products/firefox/'':57');
INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (5, 3, 1, 'We''ve seen something very similar on AIX with Gnome 2.6 when it is compiled with XFT support. It might be that the anti-aliasing is causing loopback devices to degrade, resulting in a loss of transparency at the system cache level and decoherence in the undelete function. This is only known to be a problem when the moon is gibbous.', NULL, '''ve'':2 ''2.6'':11 ''aix'':8 ''xft'':17 ''anti'':25 ''cach'':42 ''caus'':28 ''loss'':36 ''moon'':60 ''seen'':3 ''alias'':26 ''devic'':30 ''gnome'':10 ''known'':53 ''level'':43 ''might'':20 ''compil'':15 ''degrad'':32 ''result'':33 ''someth'':4 ''system'':41 ''decoher'':45 ''gibbous'':62 ''problem'':57 ''similar'':6 ''support'':18 ''undelet'':48 ''function'':49 ''loopback'':29 ''transpar'':38 ''anti-alias'':24');
INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (1, 7, 1, 'Malone pages that use more complex layouts with portlets and fancy CSS are sometimes not getting properly reflowed after rendering.', NULL, '''css'':12 ''get'':16 ''use'':4 ''page'':2 ''fanci'':11 ''malon'':1 ''layout'':7 ''proper'':17 ''reflow'':18 ''render'':20 ''complex'':6 ''portlet'':9 ''sometim'':14');
INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (7, 5, 1, 'This would be a real killer feature. If there is already code to make it possible, why aren''t there tons of press announcements about the secuirty possibilities. Imagine - no more embarrassing emails for Mr Gates... everything they delete would actually disappear! I''m sure Redmond will switch over as soon as they hear about this. It''s not a bug, it''s a feature!', NULL, '''m'':44 ''mr'':35 ''bug'':61 ''ton'':21 ''aren'':18 ''code'':12 ''gate'':36 ''hear'':54 ''make'':14 ''real'':5 ''soon'':51 ''sure'':45 ''delet'':39 ''email'':33 ''press'':23 ''would'':2,40 ''actual'':41 ''featur'':7,65 ''imagin'':29 ''killer'':6 ''switch'':48 ''alreadi'':11 ''announc'':24 ''everyth'':37 ''possibl'':16,28 ''redmond'':46 ''secuirti'':27 ''disappear'':42 ''embarrass'':32');
INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (8, 6, 1, 'Oddly enough the bug system seems only capable of displaying the first two comments that are made against a bug. I wonder why that is? Lets have a few more decent legth comments in here so we can see what the spacing is like. Also, at some stage, we''ll need a few comments that get displayed in a fixed-width font, so we have a clue about code-in-bug-comments etc.', NULL, '''ll'':50 ''bug'':4,20,73 ''etc'':75 ''fix'':61 ''get'':56 ''let'':26 ''odd'':1 ''see'':39 ''two'':13 ''also'':45 ''clue'':68 ''code'':71 ''font'':63 ''like'':44 ''made'':17 ''need'':51 ''seem'':6 ''first'':12 ''legth'':32 ''space'':42 ''stage'':48 ''width'':62 ''capabl'':8 ''decent'':31 ''enough'':2 ''system'':5 ''wonder'':22 ''comment'':14,33,54,74 ''display'':10,57 ''fixed-width'':60 ''code-in-bug-com'':70');
INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (2, 8, 1, 'All ways of downloading firefox should provide complete install instructions. At present, they are only visible on the Release Notes page.', NULL, '''way'':2 ''note'':20 ''page'':21 ''instal'':9 ''provid'':7 ''releas'':19 ''visibl'':16 ''complet'':8 ''firefox'':5 ''present'':12 ''download'':4 ''instruct'':10');
INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (6, 4, 1, 'Sorry, it was SCO unix which appears to have the same bug. For a brief moment I was confused there, since so much code is known to have been copied from SCO into AIX.', NULL, '''aix'':34 ''bug'':12 ''sco'':4,32 ''code'':24 ''copi'':30 ''much'':23 ''sinc'':21 ''unix'':5 ''brief'':15 ''known'':26 ''sorri'':1 ''appear'':7 ''confus'':19 ''moment'':16');
INSERT INTO messagechunk (id, message, "sequence", content, blob, fti) VALUES (4, 1, 1, 'Problem exists between chair and keyboard', NULL, '''chair'':4 ''exist'':2 ''problem'':1 ''keyboard'':6');


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'messagechunk'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'sourcepackagepublishinghistory'::pg_catalog.regclass;

INSERT INTO sourcepackagepublishinghistory (id, sourcepackagerelease, distrorelease, status, component, section, datecreated, datepublished, datesuperseded, supersededby, datemadepending, scheduleddeletiondate, dateremoved) VALUES (2, 15, 3, 2, 1, 1, '2004-09-27 11:57:13', '2004-09-27 11:57:13', NULL, NULL, NULL, NULL, NULL);
INSERT INTO sourcepackagepublishinghistory (id, sourcepackagerelease, distrorelease, status, component, section, datecreated, datepublished, datesuperseded, supersededby, datemadepending, scheduleddeletiondate, dateremoved) VALUES (1, 14, 1, 2, 1, 1, '2004-09-27 11:57:13', '2004-09-27 11:57:13', NULL, NULL, NULL, NULL, NULL);
INSERT INTO sourcepackagepublishinghistory (id, sourcepackagerelease, distrorelease, status, component, section, datecreated, datepublished, datesuperseded, supersededby, datemadepending, scheduleddeletiondate, dateremoved) VALUES (5, 16, 3, 2, 1, 1, '2004-03-10 16:30:00', '2004-03-10 16:30:00', NULL, NULL, NULL, NULL, NULL);
INSERT INTO sourcepackagepublishinghistory (id, sourcepackagerelease, distrorelease, status, component, section, datecreated, datepublished, datesuperseded, supersededby, datemadepending, scheduleddeletiondate, dateremoved) VALUES (4, 17, 1, 2, 1, 1, '2004-03-14 18:00:00', '2004-03-14 18:00:00', NULL, NULL, NULL, NULL, NULL);
INSERT INTO sourcepackagepublishinghistory (id, sourcepackagerelease, distrorelease, status, component, section, datecreated, datepublished, datesuperseded, supersededby, datemadepending, scheduleddeletiondate, dateremoved) VALUES (8, 20, 3, 2, 1, 1, '2005-04-18 17:34:15.308434', '2005-04-18 17:34:15.308434', NULL, NULL, NULL, NULL, NULL);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'sourcepackagepublishinghistory'::pg_catalog.regclass;


UPDATE pg_catalog.pg_class SET reltriggers = 0 WHERE oid = 'sourcesourcebackup'::pg_catalog.regclass;

INSERT INTO sourcesourcebackup (id, name, title, description, product, cvsroot, cvsmodule, cvstarfile, cvstarfileurl, cvsbranch, svnrepository, releaseroot, releaseverstyle, releasefileglob, releaseparentbranch, branch, lastsynced, syncinterval, rcstype, hosted, upstreamname, processingapproved, syncingapproved, newarchive, newbranchcategory, newbranchbranch, newbranchversion, packagedistro, packagefiles_collapsed, "owner", currentgpgkey, fileidreference, branchpoint, autotested, datestarted, datefinished, sourcepackagename, distrorelease) VALUES (2, 'evolution-head', 'Evolution CVS HEAD', 'CVS import job for Evolution HEAD', 5, ':pserver:anonymous@anoncvs.gnome.org:/cvs/gnome', 'evolution', NULL, '', 'MAIN', '', '', NULL, '', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL, 'gnome@arch.ubuntu.com', 'evolution', 'MAIN', '0', NULL, NULL, 16, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL);
INSERT INTO sourcesourcebackup (id, name, title, description, product, cvsroot, cvsmodule, cvstarfile, cvstarfileurl, cvsbranch, svnrepository, releaseroot, releaseverstyle, releasefileglob, releaseparentbranch, branch, lastsynced, syncinterval, rcstype, hosted, upstreamname, processingapproved, syncingapproved, newarchive, newbranchcategory, newbranchbranch, newbranchversion, packagedistro, packagefiles_collapsed, "owner", currentgpgkey, fileidreference, branchpoint, autotested, datestarted, datefinished, sourcepackagename, distrorelease) VALUES (1, 'evolution', 'evolution-warty', 'Package job for Warty Evolution', 5, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 4, NULL, 'evolution', '2005-01-14 17:35:39.548665', NULL, 'evolution@arch.ubuntu.com', NULL, NULL, NULL, 'warty', NULL, 2, NULL, NULL, NULL, 0, NULL, NULL, 9, 3);


UPDATE pg_catalog.pg_class SET reltriggers = (SELECT pg_catalog.count(*) FROM pg_catalog.pg_trigger where pg_class.oid = tgrelid) WHERE oid = 'sourcesourcebackup'::pg_catalog.regclass;


SELECT pg_catalog.setval('person_id_seq', 32, true);



SELECT pg_catalog.setval('emailaddress_id_seq', 25, true);



SELECT pg_catalog.setval('gpgkey_id_seq', 11, true);



SELECT pg_catalog.setval('archuserid_id_seq', 10, true);



SELECT pg_catalog.setval('wikiname_id_seq', 10, true);



SELECT pg_catalog.setval('jabberid_id_seq', 10, true);



SELECT pg_catalog.setval('ircid_id_seq', 9, true);



SELECT pg_catalog.setval('teammembership_id_seq', 36, true);



SELECT pg_catalog.setval('teamparticipation_id_seq', 59, true);



SELECT pg_catalog.setval('schema_id_seq', 4, true);



SELECT pg_catalog.setval('label_id_seq', 1, true);



SELECT pg_catalog.setval('project_id_seq', 8, true);



SELECT pg_catalog.setval('projectrelationship_id_seq', 1, false);



SELECT pg_catalog.setval('product_id_seq', 12, true);



SELECT pg_catalog.setval('productlabel_id_seq', 1, false);



SELECT pg_catalog.setval('productseries_id_seq', 6, true);



SELECT pg_catalog.setval('productrelease_id_seq', 7, true);



SELECT pg_catalog.setval('productcvsmodule_id_seq', 1, false);



SELECT pg_catalog.setval('productbkbranch_id_seq', 1, false);



SELECT pg_catalog.setval('productsvnmodule_id_seq', 1, false);



SELECT pg_catalog.setval('archarchive_id_seq', 9, true);



SELECT pg_catalog.setval('archarchivelocation_id_seq', 1, false);



SELECT pg_catalog.setval('archnamespace_id_seq', 14, true);



SELECT pg_catalog.setval('branch_id_seq', 14, true);



SELECT pg_catalog.setval('changeset_id_seq', 3, true);



SELECT pg_catalog.setval('changesetfilename_id_seq', 1, false);



SELECT pg_catalog.setval('changesetfile_id_seq', 1, false);



SELECT pg_catalog.setval('changesetfilehash_id_seq', 1, false);



SELECT pg_catalog.setval('productbranchrelationship_id_seq', 1, false);



SELECT pg_catalog.setval('manifest_id_seq', 14, true);



SELECT pg_catalog.setval('manifestentry_id_seq', 6, true);



SELECT pg_catalog.setval('archconfig_id_seq', 1, false);



SELECT pg_catalog.setval('processorfamily_id_seq', 1, true);



SELECT pg_catalog.setval('processor_id_seq', 1, true);



SELECT pg_catalog.setval('builder_id_seq', 1, false);



SELECT pg_catalog.setval('component_id_seq', 1, true);



SELECT pg_catalog.setval('section_id_seq', 1, true);



SELECT pg_catalog.setval('distribution_id_seq', 5, true);



SELECT pg_catalog.setval('distrorelease_id_seq', 9, true);



SELECT pg_catalog.setval('distroarchrelease_id_seq', 6, true);



SELECT pg_catalog.setval('libraryfilecontent_id_seq', 4, true);



SELECT pg_catalog.setval('libraryfilealias_id_seq', 4, true);



SELECT pg_catalog.setval('sourcepackagename_id_seq', 15, true);



SELECT pg_catalog.setval('sourcepackagerelease_id_seq', 20, true);



SELECT pg_catalog.setval('build_id_seq', 7, true);



SELECT pg_catalog.setval('binarypackagename_id_seq', 13, true);



SELECT pg_catalog.setval('binarypackage_id_seq', 15, true);



SELECT pg_catalog.setval('packagepublishing_id_seq', 11, true);



SELECT pg_catalog.setval('packageselection_id_seq', 1, false);



SELECT pg_catalog.setval('osfile_id_seq', 1, false);



SELECT pg_catalog.setval('pomsgid_id_seq', 27, true);



SELECT pg_catalog.setval('potranslation_id_seq', 12, true);









SELECT pg_catalog.setval('license_id_seq', 1, true);



SELECT pg_catalog.setval('potemplate_id_seq', 2, true);



SELECT pg_catalog.setval('pofile_id_seq', 2, true);



SELECT pg_catalog.setval('pomsgset_id_seq', 22, true);



SELECT pg_catalog.setval('pomsgidsighting_id_seq', 27, true);



SELECT pg_catalog.setval('potranslationsighting_id_seq', 12, true);



SELECT pg_catalog.setval('pocomment_id_seq', 1, false);



SELECT pg_catalog.setval('translationeffort_id_seq', 1, false);



SELECT pg_catalog.setval('posubscription_id_seq', 1, false);



SELECT pg_catalog.setval('bug_id_seq', 6, true);



SELECT pg_catalog.setval('bugsubscription_id_seq', 5, true);



SELECT pg_catalog.setval('bugactivity_id_seq', 6, true);



SELECT pg_catalog.setval('bugexternalref_id_seq', 4, true);



SELECT pg_catalog.setval('bugtrackertype_id_seq', 2, true);



SELECT pg_catalog.setval('bugtracker_id_seq', 3, true);



SELECT pg_catalog.setval('bugwatch_id_seq', 4, true);



SELECT pg_catalog.setval('message_id_seq', 9, true);



SELECT pg_catalog.setval('bugattachment_id_seq', 1, false);



SELECT pg_catalog.setval('projectbugtracker_id_seq', 1, true);



SELECT pg_catalog.setval('distributionrole_id_seq', 7, true);



SELECT pg_catalog.setval('distroreleaserole_id_seq', 9, true);



SELECT pg_catalog.setval('componentselection_id_seq', 1, false);



SELECT pg_catalog.setval('sectionselection_id_seq', 1, false);



SELECT pg_catalog.setval('sourcepackagepublishing_id_seq', 8, true);



SELECT pg_catalog.setval('bugproductinfestation_id_seq', 1, false);



SELECT pg_catalog.setval('bugpackageinfestation_id_seq', 1, false);



SELECT pg_catalog.setval('distroreleasequeue_id_seq', 1, false);



SELECT pg_catalog.setval('distroreleasequeuesource_id_seq', 1, false);



SELECT pg_catalog.setval('distroreleasequeuebuild_id_seq', 1, false);



SELECT pg_catalog.setval('sourcepackagereleasefile_id_seq', 1, true);



SELECT pg_catalog.setval('binarypackagefile_id_seq', 1, false);



SELECT pg_catalog.setval('personlanguage_id_seq', 4, true);



SELECT pg_catalog.setval('potmsgset_id_seq', 23, true);



SELECT pg_catalog.setval('bounty_id_seq', 1, true);



SELECT pg_catalog.setval('bugmessage_id_seq', 8, true);



SELECT pg_catalog.setval('cveref_id_seq', 1, false);



SELECT pg_catalog.setval('karma_id_seq', 3, true);



SELECT pg_catalog.setval('spokenin_id_seq', 334, true);



SELECT pg_catalog.setval('sourcepackagerelationship_id_seq', 1, false);



SELECT pg_catalog.setval('sshkey_id_seq', 1, true);



SELECT pg_catalog.setval('bugtask_id_seq', 15, true);



SELECT pg_catalog.setval('branchlabel_id_seq', 1, false);



SELECT pg_catalog.setval('branchrelationship_id_seq', 1, false);



SELECT pg_catalog.setval('productreleasefile_id_seq', 2, true);



SELECT pg_catalog.setval('logintoken_id_seq', 1, false);



SELECT pg_catalog.setval('milestone_id_seq', 2, false);



SELECT pg_catalog.setval('pushmirroraccess_id_seq', 1, false);



SELECT pg_catalog.setval('buildqueue_id_seq', 1, false);



SELECT pg_catalog.setval('packaging_id_seq', 7, true);



SELECT pg_catalog.setval('signedcodeofconduct_id_seq', 1, false);



SELECT pg_catalog.setval('bountysubscription_id_seq', 3, true);



SELECT pg_catalog.setval('productbounty_id_seq', 1, true);



SELECT pg_catalog.setval('distrobounty_id_seq', 1, true);



SELECT pg_catalog.setval('projectbounty_id_seq', 1, true);



SELECT pg_catalog.setval('mirror_id_seq', 1, false);



SELECT pg_catalog.setval('mirrorcontent_id_seq', 1, false);



SELECT pg_catalog.setval('mirrorsourcecontent_id_seq', 1, false);



SELECT pg_catalog.setval('potemplatename_id_seq', 2, true);



SELECT pg_catalog.setval('maintainership_id_seq', 3, true);



SELECT pg_catalog.setval('messagechunk_id_seq', 8, true);



SELECT pg_catalog.setval('sourcepackagepublishinghistory_id_seq', 1, false);


