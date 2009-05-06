# Copyright 2004-2007 Canonical Ltd.  All rights reserved.
# pylint: disable-msg=W0401

"""Launchpad Browser-Interface View classes.

This is the module to import for Launchpad View Classes. The classes are not
located in this specific module, but are in turn imported from each of the
files in this directory.
"""

# XXX flacoste 2009/03/18 We should use specific imports instead of
# importing from this module.
from lp.registry.browser.announcement import *
from canonical.launchpad.browser.archive import *
from canonical.launchpad.browser.authtoken import *
from lp.code.browser.bazaar import *
from canonical.launchpad.browser.binarypackagerelease import *
from canonical.launchpad.browser.bounty import *
from canonical.launchpad.browser.bountysubscription import *
from lp.code.browser.branchlisting import *
from lp.code.browser.branchmergeproposal import *
from lp.code.browser.branchref import *
from lp.code.browser.branchsubscription import *
from lp.code.browser.branchvisibilitypolicy import *
from canonical.launchpad.browser.branding import *
from canonical.launchpad.browser.bug import *
from canonical.launchpad.browser.bugalsoaffects import *
from canonical.launchpad.browser.bugattachment import *
from canonical.launchpad.browser.bugbranch import *
from canonical.launchpad.browser.bugcomment import *
from canonical.launchpad.browser.buglinktarget import *
from canonical.launchpad.browser.bugmessage import *
from canonical.launchpad.browser.bugnomination import *
from canonical.launchpad.browser.bugsubscription import *
from canonical.launchpad.browser.bugsupervisor import *
from canonical.launchpad.browser.bugtarget import *
from canonical.launchpad.browser.bugtask import *
from canonical.launchpad.browser.bugtracker import *
from canonical.launchpad.browser.bugwatch import *
from canonical.launchpad.browser.build import *
from canonical.launchpad.browser.builder import *
from lp.code.browser.codeimport import *
from lp.code.browser.codeimportmachine import *
from lp.registry.browser.codeofconduct import *
from lp.code.browser.codereviewcomment import *
from canonical.launchpad.browser.cve import *
from canonical.launchpad.browser.cvereport import *
from lp.registry.browser.distribution import *
from canonical.launchpad.browser.distributionmirror import *
from lp.registry.browser.distributionsourcepackage import *
from canonical.launchpad.browser.distributionsourcepackagerelease import *
from canonical.launchpad.browser.distribution_upstream_bug_report import *
from canonical.launchpad.browser.distroarchseries import *
from canonical.launchpad.browser.distroarchseriesbinarypackage import *
from canonical.launchpad.browser.distroarchseriesbinarypackagerelease import *
from lp.registry.browser.distroseries import *
from canonical.launchpad.browser.distroseriesbinarypackage import *
from canonical.launchpad.browser.distroserieslanguage import *
from canonical.launchpad.browser.distroseriessourcepackagerelease import *
from lp.answers.browser.faq import *
from lp.answers.browser.faqcollection import *
from lp.answers.browser.faqtarget import *
from lp.registry.browser.featuredproject import *
from canonical.launchpad.browser.feeds import *
from canonical.launchpad.browser.hastranslationimports import *
from canonical.launchpad.browser.hwdb import *
from lp.registry.browser.karma import *
from canonical.launchpad.browser.language import *
from canonical.launchpad.browser.launchpad import *
from canonical.launchpad.browser.launchpadstatistic import *
from canonical.launchpad.browser.librarian import *
from canonical.launchpad.browser.logintoken import *
from lp.registry.browser.mailinglists import *
from lp.registry.browser.mentoringoffer import *
from canonical.launchpad.browser.message import *
from lp.registry.browser.milestone import *
from canonical.launchpad.browser.oauth import *
from canonical.launchpad.browser.objectreassignment import *
from canonical.launchpad.browser.packagerelationship import *
from canonical.launchpad.browser.packaging import *
from lp.registry.browser.peoplemerge import *
from lp.registry.browser.person import *
from canonical.launchpad.browser.pofile import *
from lp.registry.browser.poll import *
from canonical.launchpad.browser.potemplate import *
from lp.registry.browser.product import *
from lp.registry.browser.productrelease import *
from lp.registry.browser.productseries import *
from lp.registry.browser.project import *
from canonical.launchpad.browser.publishedpackage import *
from canonical.launchpad.browser.publishing import *
from lp.answers.browser.question import *
from lp.answers.browser.questiontarget import *
from canonical.launchpad.browser.queue import *
from lp.registry.browser.root import *
from lp.registry.browser.sourcepackage import *
from canonical.launchpad.browser.sourcepackagerelease import *
from canonical.launchpad.browser.specification import *
from canonical.launchpad.browser.specificationbranch import *
from canonical.launchpad.browser.specificationdependency import *
from canonical.launchpad.browser.specificationfeedback import *
from canonical.launchpad.browser.specificationgoal import *
from canonical.launchpad.browser.specificationsubscription import *
from canonical.launchpad.browser.specificationtarget import *
from canonical.launchpad.browser.sprint import *
from canonical.launchpad.browser.sprintattendance import *
from canonical.launchpad.browser.sprintspecification import *
from lp.registry.browser.team import *
from lp.registry.browser.teammembership import *
from canonical.launchpad.browser.temporaryblobstorage import *
from canonical.launchpad.browser.translationgroup import *
from canonical.launchpad.browser.translationimportqueue import *
from canonical.launchpad.browser.translationmessage import *
from canonical.launchpad.browser.translations import *
from canonical.launchpad.browser.translator import *
from canonical.launchpad.browser.widgets import *
