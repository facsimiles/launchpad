import readline
import rlcompleter
import sys

import bzrlib.errors

from devscripts.ec2test.command import CommandController
from devscripts.ec2test.builtins import cmd_demo, cmd_test, cmd_update_image

# Shut up pyflakes.
rlcompleter

readline.parse_and_bind('tab: complete')

def main():
    controller = CommandController()
    controller.install_bzrlib_hooks()
    controller.register_command('test', cmd_test)
    controller.register_command('demo', cmd_demo)
    controller.register_command('update-image', cmd_update_image)

    if len(sys.argv) < 2:
        command_names = controller._commands.iterkeys()
        sys.exit(
            "You must supply a command, one of: %s."
            % ', '.join(sorted(command_names)))
    try:
        controller.run(sys.argv[1:])
    except bzrlib.errors.BzrCommandError, e:
        sys.exit('ec2: ERROR: ' + str(e))
