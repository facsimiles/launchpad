#!/usr/bin/env python
# Copyright 2012 Canonical Ltd.  This software is licensed under the
# GNU Affero General Public License version 3 (see the file LICENSE).

"""Create an LXC test environment for Launchpad testing."""

__metaclass__ = type
__all__ = [
    'ArgumentParser',
    'cd',
    'create_lxc',
    'file_append',
    'file_prepend',
    'get_container_path',
    'get_user_ids',
    'initialize_host',
    'initialize_lxc',
    'Configuration',
    'SetupLXCError',
    'ssh',
    'SSHError',
    'stop_lxc',
    'su',
    'user_exists',
    ]

# To run doctests: python -m doctest -v setuplxc.py

from collections import namedtuple, OrderedDict
from contextlib import contextmanager
import argparse
import os
import pwd
import shutil
import subprocess
import sys
import time


DEPENDENCIES_DIR = '~/dependencies'
DHCP_FILE = '/etc/dhcp/dhclient.conf'
HOST_PACKAGES = ['ssh', 'lxc', 'libvirt-bin', 'bzr', 'language-pack-en']
HOSTS_FILE = '/etc/hosts'
LP_APACHE_MODULES = 'proxy proxy_http rewrite ssl deflate headers'
LP_APACHE_ROOTS = (
    '/var/tmp/bazaar.launchpad.dev/static',
    '/var/tmp/archive',
    '/var/tmp/ppa',
    )
LP_CHECKOUT = 'devel'
LP_REPOSITORY = 'lp:launchpad'
LP_SOURCE_DEPS = (
    'http://bazaar.launchpad.net/~launchpad/lp-source-dependencies/trunk')
LXC_CONFIG_TEMPLATE = '/etc/lxc/local.conf'
LXC_GATEWAY = '10.0.3.1'
LXC_GUEST_OS = 'lucid'
LXC_HOSTS_CONTENT = (
    ('127.0.0.88',
        'launchpad.dev answers.launchpad.dev archive.launchpad.dev '
        'api.launchpad.dev bazaar-internal.launchpad.dev beta.launchpad.dev '
        'blueprints.launchpad.dev bugs.launchpad.dev code.launchpad.dev '
        'feeds.launchpad.dev id.launchpad.dev keyserver.launchpad.dev '
        'lists.launchpad.dev openid.launchpad.dev '
        'ubuntu-openid.launchpad.dev ppa.launchpad.dev '
        'private-ppa.launchpad.dev testopenid.dev translations.launchpad.dev '
        'xmlrpc-private.launchpad.dev xmlrpc.launchpad.dev'),
    ('127.0.0.99', 'bazaar.launchpad.dev'),
    )
LXC_NAME = 'lptests'
LXC_OPTIONS = (
    ('lxc.network.type', 'veth'),
    ('lxc.network.link', 'lxcbr0'),
    ('lxc.network.flags', 'up'),
    )
LXC_PATH = '/var/lib/lxc/'
LXC_REPOS = (
    'deb http://archive.ubuntu.com/ubuntu '
    'lucid main universe multiverse',
    'deb http://archive.ubuntu.com/ubuntu '
    'lucid-updates main universe multiverse',
    'deb http://archive.ubuntu.com/ubuntu '
    'lucid-security main universe multiverse',
    'deb http://ppa.launchpad.net/launchpad/ppa/ubuntu lucid main',
    'deb http://ppa.launchpad.net/bzr/ppa/ubuntu lucid main',
    )
RESOLV_FILE = '/etc/resolv.conf'


Env = namedtuple('Env', 'uid gid home')


class SetupLXCError(Exception):
    """Base exception for setuplxc."""


class SSHError(SetupLXCError):
    """Errors occurred during SSH connection."""


@contextmanager
def ssh(location, user=None):
    """Return a callable that can be used to run ssh shell commands.

    The ssh `location` and, optionally, `user` must be given.
    If the user is None then the current user is used for the connection.
    """
    if user is not None:
        location = '{}@{}'.format(user, location)

    def _sshcall(cmd):
        sshcmd = (
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            location,
            '--', cmd,
            )
        if subprocess.call(sshcmd):
            raise SSHError(
                'Error running command: {}'.format(' '.join(sshcmd)))

    yield _sshcall


def get_user_ids(user):
    """Return the uid and gid of given `user`, e.g.::

        >>> get_user_ids('root')
        (0, 0)
    """
    userdata = pwd.getpwnam(user)
    return userdata.pw_uid, userdata.pw_gid


@contextmanager
def su(user):
    """A context manager to temporary run the script as a different user."""
    uid, gid = get_user_ids(user)
    os.setegid(gid)
    os.seteuid(uid)
    current_home = os.getenv('HOME')
    home = os.path.join(os.path.sep, 'home', user)
    os.environ['HOME'] = home
    yield Env(uid, gid, home)
    os.setegid(os.getgid())
    os.seteuid(os.getuid())
    os.environ['HOME'] = current_home


@contextmanager
def cd(directory):
    """A context manager to temporary change current working dir, e.g.::

        >>> import os
        >>> os.chdir('/tmp')
        >>> with cd('/bin'): print os.getcwd()
        /bin
        >>> os.getcwd()
        '/tmp'
    """
    cwd = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(cwd)


def get_container_path(lxcname, path='', base_path=LXC_PATH):
    """Return the path of LXC container called `lxcname`.

    If a `path` is given, return that path inside the container, e.g.::

        >>> get_container_path('mycontainer')
        '/var/lib/lxc/mycontainer/rootfs/'
        >>> get_container_path('mycontainer', '/etc/apt/')
        '/var/lib/lxc/mycontainer/rootfs/etc/apt/'
        >>> get_container_path('mycontainer', 'home')
        '/var/lib/lxc/mycontainer/rootfs/home'
    """
    return os.path.join(base_path, lxcname, 'rootfs', path.lstrip('/'))


def file_prepend(filename, line):
    """Insert given `line`, if not present, at the beginning of `filename`.

    Usage example::

        >>> import tempfile
        >>> f = tempfile.NamedTemporaryFile('w', delete=False)
        >>> f.write('line1\\n')
        >>> f.close()
        >>> file_prepend(f.name, 'line0\\n')
        >>> open(f.name).read()
        'line0\\nline1\\n'

    If the file starts with the given `line`, nothing happens::

        >>> file_prepend(f.name, 'line0\\n')
        >>> open(f.name).read()
        'line0\\nline1\\n'

    If the file contains the given `line`, but not at the beginning,
    the line is moved on top::

        >>> file_prepend(f.name, 'line1\\n')
        >>> open(f.name).read()
        'line1\\nline0\\n'
    """
    with open(filename, 'r+') as f:
        lines = f.readlines()
        if lines[0] != line:
            if line in lines:
                lines.remove(line)
            lines.insert(0, line)
            f.seek(0)
            f.writelines(lines)


def file_append(filename, line):
    """Append given `line`, if not present, at the end of `filename`.

    Usage example::

        >>> import tempfile
        >>> f = tempfile.NamedTemporaryFile('w', delete=False)
        >>> f.write('line1\\n')
        >>> f.close()
        >>> file_append(f.name, 'new line\\n')
        >>> open(f.name).read()
        'line1\\nnew line\\n'

    Nothing happens if the file already contains the given `line`::

        >>> file_append(f.name, 'new line\\n')
        >>> open(f.name).read()
        'line1\\nnew line\\n'

    A new line is automatically added before the given `line` if it is not
    present at the end of current file content::

        >>> import tempfile
        >>> f = tempfile.NamedTemporaryFile('w', delete=False)
        >>> f.write('line1')
        >>> f.close()
        >>> file_append(f.name, 'new line\\n')
        >>> open(f.name).read()
        'line1\\nnew line\\n'
    """
    with open(filename, 'a+') as f:
        content = f.read()
        if line not in content:
            f.write(line if content.endswith('\n') else '\n{}'.format(line))


def user_exists(username):
    """Return True if given `username` exists, e.g.::

        >>> user_exists('root')
        True
        >>> user_exists('_this_user_does_not_exist_')
        False
    """
    try:
        pwd.getpwnam(username)
    except KeyError:
        return False
    return True


class Configuration(argparse.Namespace):
    """A namespace for argparse.

    Add methods for further arguments validation.
    This class implements ssh key validation, e.g.::

        >>> args = parser.parse_args('-u example_user -e example@example.com '
        ...                          '-f exampleuser -v PRIVATE -b PUBLIC '
        ...                          '/home/example_user/launchpad/'.split(),
        ...                          namespace=Configuration())
        >>> args.are_valid()
        True
        >>> args = parser.parse_args('-u example_user -e example@example.com '
        ...                          '-f exampleuser -b PUBLIC '
        ...                          '/home/example_user/launchpad/'.split(),
        ...                          namespace=Configuration())
        >>> args.are_valid()
        False
        >>> args.error_message # doctest: +ELLIPSIS
        'argument private_key ...'

    and directory validation::

        >>> args = parser.parse_args('-u example_user -e example@example.com '
        ...                          '-f exampleuser -v PRIVATE -b PUBLIC '
        ...                          '/home/'.split(),
        ...                          namespace=Configuration())
        >>> args.are_valid()
        False
        >>> args.error_message # doctest: +ELLIPSIS
        'argument directory ...'
    """
    _errors = None

    @property
    def error_message(self):
        return '\n'.join(self._errors)

    def _get_ssh_key(self, attr, filename):
        value = getattr(self, attr)
        if value:
            return value.decode('string-escape')
        try:
            return open(filename).read()
        except IOError:
            self._errors.append(
                'argument {} is required if the system user '
                'does not exists with SSH key pair set up.'.format(attr))

    def _get_directory(self, attr, home_dir):
        directory = getattr(self, attr).replace('~', home_dir)
        if not directory.startswith(home_dir + os.path.sep):
            self._errors.append('argument {} does not reside under the home '
                                'directory of the system user.'.format(attr))
        return directory

    def are_valid(self):
        self._errors = []
        self.run_as_root = not os.geteuid()
        home_dir = os.path.join(os.path.sep, 'home', self.user)
        if self.lpuser is None:
            self.lpuser = self.user
        self.private_key = self._get_ssh_key(
            'private_key', os.path.join(home_dir, '.ssh', 'id_rsa'))
        self.public_key = self._get_ssh_key(
            'public_key', os.path.join(home_dir, '.ssh', 'id_rsa.pub'))
        self.directory = self._get_directory('directory', home_dir)
        self.dependencies_dir = self._get_directory(
            'dependencies_dir', home_dir)
        return not self._errors


class ArgumentParser(argparse.ArgumentParser):
    """A customized parser for argparse."""

    def get_args_from_namespace(self, namespace):
        """Return a list of arguments taking values from `namespace`.

        Having a parser defined as usual::

            >>> parser = ArgumentParser()
            >>> _ = parser.add_argument('--foo')
            >>> _ = parser.add_argument('bar')
            >>> namespace = parser.parse_args('--foo eggs spam'.split())

        It is possible to recreate the argument list taking values from
        a different namespace::

            >>> namespace.foo = 'changed'
            >>> parser.get_args_from_namespace(namespace)
            ['--foo', 'changed', 'spam']
        """
        args = []
        for action in self._actions:
            dest = action.dest
            option_strings = action.option_strings
            value = getattr(namespace, dest, None)
            if value:
                if option_strings:
                    args.append(option_strings[0])
                args.append(value)
        return args


parser = ArgumentParser(description=__doc__)
parser.add_argument(
    '-u', '--user', required=True,
    help='The name of the system user to be created or updated.')
parser.add_argument(
    '-e', '--email', required=True,
    help='The email of the user, used for bzr whoami.')
parser.add_argument(
    '-f', '--full-name', required=True,
    help='The full name of the user, used for bzr whoami.')
parser.add_argument(
    '-l', '--lpuser',
    help='The name of the Launchpad user that will be used to check out '
         'dependencies.  If not provided, the system user name is used.')
parser.add_argument(
    '-v', '--private-key',
    help='The SSH private key for the Launchpad user (without passphrase). '
         'If the system user already exists with SSH key pair set up, '
         'this argument can be omitted.')
parser.add_argument(
    '-b', '--public-key',
    help='The SSH public key for the Launchpad user. '
         'If the system user already exists with SSH key pair set up, '
         'this argument can be omitted.')
parser.add_argument(
    '-a', '--actions', nargs='+',
    choices=('initialize_host', 'create_lxc', 'initialize_lxc', 'stop_lxc'),
    help='Only for debugging. Call one or more internal functions.')
parser.add_argument(
    '-n', '--lxc-name', default=LXC_NAME,
    metavar='LXC_NAME (default={})'.format(LXC_NAME),
    help='The LXC container name.')
parser.add_argument(
    '-d', '--dependencies-dir', default=DEPENDENCIES_DIR,
    metavar='DEPENDENCIES_DIR (default={})'.format(DEPENDENCIES_DIR),
    help='The directory of the Launchpad dependencies to be created. '
         'The directory must reside under the home directory of the '
         'given user (see -u argument).')
parser.add_argument(
    'directory',
    help='The directory of the Launchpad repository to be created. '
         'The directory must reside under the home directory of the '
         'given user (see -u argument).')


def initialize_host(
    user, fullname, email, lpuser, private_key, public_key,
    dependencies_dir, directory):
    """Initialize host machine."""
    # Install necessary deb packages.  This requires Oneiric or later.
    subprocess.call(['apt-get', 'update'])
    subprocess.call(['apt-get', '-y', 'install'] + HOST_PACKAGES)
    # Create the user (if he does not exist).
    if not user_exists(user):
        subprocess.call(['useradd', '-m', '-s', '/bin/bash', '-U', user])
    # Generate root ssh keys if they do not exist.
    if not os.path.exists('/root/.ssh/id_rsa.pub'):
        subprocess.call([
            'ssh-keygen', '-q', '-t', 'rsa', '-N', '',
            '-f', '/root/.ssh/id_rsa'])
    with su(user) as env:
        # Set up the user's ssh directory.  The ssh key must be associated
        # with the lpuser's Launchpad account.
        ssh_dir = os.path.join(env.home, '.ssh')
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir)
        priv_file = os.path.join(ssh_dir, 'id_rsa')
        pub_file = os.path.join(ssh_dir, 'id_rsa.pub')
        auth_file = os.path.join(ssh_dir, 'authorized_keys')
        known_hosts = os.path.join(ssh_dir, 'known_hosts')
        known_host_content = subprocess.check_output([
            'ssh-keyscan', '-t', 'rsa', 'bazaar.launchpad.net'])
        for filename, contents, mode in [
            (priv_file, private_key, 'w'),
            (pub_file, public_key, 'w'),
            (auth_file, public_key, 'a'),
            (known_hosts, known_host_content, 'a'),
            ]:
            with open(filename, mode) as f:
                f.write('{}\n'.format(contents))
            os.chmod(filename, 0644)
        os.chmod(priv_file, 0600)
        # Set up bzr and Launchpad authentication.
        subprocess.call([
            'bzr', 'whoami', '"{} <{}>"'.format(fullname, email)])
        subprocess.call(['bzr', 'lp-login', lpuser])
        # Set up the repository.
        if not os.path.exists(directory):
            os.makedirs(directory)
        subprocess.call(['bzr', 'init-repo', directory])
        checkout_dir = os.path.join(directory, LP_CHECKOUT)
    # bzr branch does not work well with seteuid.
    os.system(
        "su - {} -c 'bzr branch {} {}'".format(
        user, LP_REPOSITORY, checkout_dir))
    with su(user) as env:
        # Set up source dependencies.
        for subdir in ('eggs', 'yui', 'sourcecode'):
            os.makedirs(os.path.join(dependencies_dir, subdir))
        with cd(dependencies_dir):
            subprocess.call([
                'bzr', 'co', '--lightweight',
                LP_SOURCE_DEPS, 'download-cache'])
    # Update resolv file in order to get the ability to ssh into the LXC
    # container using its name.
    file_prepend(RESOLV_FILE, 'nameserver {}\n'.format(LXC_GATEWAY))
    file_append(
        DHCP_FILE, 'prepend domain-name-servers {};\n'.format(LXC_GATEWAY))


def create_lxc(user, lxcname):
    """Create the LXC container that will be used for ephemeral instances."""
    # Container configuration template.
    content = ''.join('{}={}\n'.format(*i) for i in LXC_OPTIONS)
    with open(LXC_CONFIG_TEMPLATE, 'w') as f:
        f.write(content)
    # Creating container.
    exit_code = subprocess.call([
        'lxc-create',
        '-t', 'ubuntu',
        '-n', lxcname,
        '-f', LXC_CONFIG_TEMPLATE,
        '--',
        '-r {} -a i386 -b {}'.format(LXC_GUEST_OS, user),
        ])
    if exit_code:
        raise SetupLXCError('Unable to create the LXC container.')
    subprocess.call(['lxc-start', '-n', lxcname, '-d'])
    # Set up root ssh key.
    user_authorized_keys = os.path.join(
        os.path.sep, 'home', user, '.ssh/authorized_keys')
    with open(user_authorized_keys, 'a') as f:
        f.write(open('/root/.ssh/id_rsa.pub').read())
    dst = get_container_path(lxcname, '/root/.ssh/')
    if not os.path.exists(dst):
        os.makedirs(dst)
    shutil.copy(user_authorized_keys, dst)
    # SSH into the container.
    with ssh(lxcname, user) as sshcall:
        trials = 60
        while True:
            trials -= 1
            try:
                sshcall('true')
            except SSHError:
                if not trials:
                    raise
                time.sleep(1)
            else:
                break


def initialize_lxc(user, dependencies_dir, directory, lxcname):
    """Set up the Launchpad development environment inside the LXC container.
    """
    with ssh(lxcname) as sshcall:
        # APT repository update.
        sources = get_container_path(lxcname, '/etc/apt/sources.list')
        with open(sources, 'w') as f:
            f.write('\n'.join(LXC_REPOS))
        # XXX frankban 2012-01-13 - Bug 892892: upgrading mountall in LXC
        # containers currently does not work.
        sshcall("echo 'mountall hold' | dpkg --set-selections")
        # Upgrading packages.
        sshcall(
            'apt-get update && '
            'DEBIAN_FRONTEND=noninteractive '
            'apt-get -y --allow-unauthenticated install language-pack-en')
        sshcall(
            'DEBIAN_FRONTEND=noninteractive '
            'apt-get -y --allow-unauthenticated install '
            'bzr launchpad-developer-dependencies apache2 apache2-mpm-worker')
        # User configuration.
        sshcall('adduser {} sudo'.format(user))
        pygetgid = 'import pwd; print pwd.getpwnam("{}").pw_gid'.format(user)
        gid = "`python -c '{}'`".format(pygetgid)
        sshcall('addgroup --gid {} {}'.format(gid, user))
    with ssh(lxcname, user) as sshcall:
        # Set up Launchpad dependencies.
        checkout_dir = os.path.join(directory, LP_CHECKOUT)
        sshcall(
            'cd {} && utilities/update-sourcecode {}/sourcecode'.format(
            checkout_dir, dependencies_dir))
        sshcall(
            'cd {} && utilities/link-external-sourcecode {}'.format(
            checkout_dir, dependencies_dir))
        # Create Apache document roots, to avoid warnings.
        sshcall(' && '.join('mkdir -p {}'.format(i) for i in LP_APACHE_ROOTS))
    with ssh(lxcname) as sshcall:
        # Set up Apache modules.
        for module in LP_APACHE_MODULES.split():
            sshcall('a2enmod {}'.format(module))
        # Launchpad database setup.
        sshcall(
            'cd {} && utilities/launchpad-database-setup {}'.format(
            checkout_dir, user))
    with ssh(lxcname, user) as sshcall:
        sshcall('cd {} && make'.format(checkout_dir))
    # Set up container hosts file.
    lines = ['{}\t{}'.format(ip, names) for ip, names in LXC_HOSTS_CONTENT]
    lxc_hosts_file = get_container_path(lxcname, HOSTS_FILE)
    file_append(lxc_hosts_file, '\n'.join(lines))
    # Make and install launchpad.
    with ssh(lxcname) as sshcall:
        sshcall('cd {} && make install'.format(checkout_dir))


def stop_lxc(lxcname):
    """Stop the lxc instance named `lxcname`."""
    with ssh(lxcname) as sshcall:
        sshcall('poweroff')
    time.sleep(5)
    subprocess.call(['lxc-stop', '-n', lxcname])


def main(
    user, fullname, email, lpuser, private_key, public_key, actions,
    lxc_name, dependencies_dir, directory):
    function_args_map = OrderedDict((
        ('initialize_host', (user, fullname, email, lpuser, private_key,
                             public_key, dependencies_dir, directory)),
        ('create_lxc', (user, lxc_name)),
        ('initialize_lxc', (user, dependencies_dir, directory, lxc_name)),
        ('stop_lxc', (lxc_name,)),
        ))
    if actions is None:
        actions = function_args_map.keys()
    scope = globals()
    for action in actions:
        try:
            scope[action](*function_args_map[action])
        except SetupLXCError as err:
            return err


if __name__ == '__main__':
    args = parser.parse_args(namespace=Configuration())
    if args.are_valid():
        if args.run_as_root:
            exit_code = main(
                args.user,
                args.full_name,
                args.email,
                args.lpuser,
                args.private_key,
                args.public_key,
                args.actions,
                args.lxc_name,
                args.dependencies_dir,
                args.directory,
                )
        else:
            exit_code = subprocess.call(
                ['sudo', sys.argv[0]] + parser.get_args_from_namespace(args))
        sys.exit(exit_code)
    else:
        parser.error(args.error_message)
