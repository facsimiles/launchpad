Update-pkgcache script
======================

Package cache system is better described in package-cache.rst.

'update-pkgcache.py' is supposed to run periodically in our
infrastructure and it is localised in the 'cronscripts' directory

    >>> import os
    >>> from lp.services.config import config
    >>> script = os.path.join(
    ...     config.root, "cronscripts", "update-pkgcache.py"
    ... )

Database sampledata has two pending modifications of package cache
contents:

    >>> from lp.registry.interfaces.distribution import IDistributionSet
    >>> ubuntu = getUtility(IDistributionSet)["ubuntu"]
    >>> warty = ubuntu["warty"]

'cdrkit' source and binary are published but it's not present in
cache:

    >>> ubuntu.searchSourcePackages("cdrkit").count()
    0
    >>> warty.searchPackages("cdrkit").count()
    0

'foobar' source and binary are removed but still present in cache:

    >>> ubuntu.searchSourcePackages("foobar").count()
    1
    >>> warty.searchPackages("foobar").count()
    1

Normal operation produces INFO level information about the
distribution and respective distroseriess considered in stderr.

    >>> import subprocess
    >>> process = subprocess.Popen(
    ...     [script],
    ...     stdout=subprocess.PIPE,
    ...     stderr=subprocess.PIPE,
    ...     universal_newlines=True,
    ... )
    >>> stdout, stderr = process.communicate()
    >>> process.returncode
    0

    >>> print(stdout)

    >>> print(stderr)
    INFO    Starting the package cache update
    INFO    Creating lockfile: /var/lock/launchpad-update-cache.lock
    INFO    Updating ubuntu package counters
    INFO    Updating ubuntu main archives
    ...
    INFO    Updating ubuntu official branch links
    INFO    Updating ubuntu PPAs
    ...
    INFO    redhat done
    INFO    Finished the package cache update

Rollback the old transaction in order to get the modifications done by
the external script:

    >>> import transaction
    >>> transaction.abort()

Now, search results are up to date:

    >>> ubuntu.searchSourcePackages("cdrkit").count()
    1
    >>> warty.searchPackages("cdrkit").count()
    1

    >>> ubuntu.searchSourcePackages("foobar").count()
    0
    >>> warty.searchPackages("foobar").count()
    0

Explicitly mark the database as dirty so that it is cleaned (see bug 994158).

    >>> from lp.testing.layers import DatabaseLayer
    >>> DatabaseLayer.force_dirty_database()
