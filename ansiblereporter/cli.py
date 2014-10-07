"""
Script wrappers for ansible commands and PlaybookScript

Wrap calling of ansible commands and playbooks to a script, extending
systematic.shell.Script classes.
"""

import os
import threading
import getpass

from systematic.shell import Script
from systematic.log import Logger

from ansible.constants import DEFAULT_MODULE_NAME, DEFAULT_MODULE_PATH, DEFAULT_MODULE_ARGS, \
                              DEFAULT_TIMEOUT, DEFAULT_HOST_LIST, DEFAULT_PRIVATE_KEY_FILE, \
                              DEFAULT_FORKS, DEFAULT_REMOTE_PORT, DEFAULT_PATTERN, \
                              DEFAULT_SUDO_USER, active_user

from ansible.errors import AnsibleError
from ansible.inventory import Inventory

from ansiblereporter import RunnerError
from ansiblereporter.result import PlaybookRunner, AnsibleRunner


DEFAULT_INVENTORY_PATHS = (
    os.environ.get('ANSIBLE_HOSTS', None),
    os.path.expanduser('~/.ansible.hosts'),
    DEFAULT_HOST_LIST,
)


logger = Logger().default_stream


def find_inventory():
    """Locate ansible inventory

    Return first ansible inventory file matching paths in
    DEFAULT_INVENTORY_PATHS.
    """
    for hostlist in DEFAULT_INVENTORY_PATHS:
        if hostlist is None:
            continue

        if os.path.isfile(hostlist):
            return hostlist

    return None


def create_directory(directory):
    """Create directory

    Wrapper to attempt creating directory unless it exists.

    Raises RunnerError if any errors happen.
    """
    if os.path.isdir(directory):
        logger.debug('directory already exists: %s' % directory)
        return

    try:
        os.makedirs(directory)
    except IOError, (ecode, emsg):
        raise RunnerError('Error creating directory %s: %s' % (directory, emsg))
    except OSError, (ecode, emsg):
        raise RunnerError('Error creating directory %s: %s' % (directory, emsg))


class GenericAnsibleScript(Script):
    """Ansible script wrapper base class

    Extend systematic.shell.Script (which wraps argparse.ArgumentParser) to run ansible
    and playbook commands. This is just the base class for variants.
    """

    def __init__(self, *args, **kwargs):
        Script.__init__(self, *args, **kwargs)
        self.runner = None
        self.mode = ''

    def SIGINT(self, signum, frame):
        """
        Parse SIGINT signal by quitting the program cleanly with exit code 1
        """
        if self.runner is not None:
            raise KeyboardInterrupt()
        else:
            self.exit(1)

    def parse_args(self, *args, **kwargs):
        args = Script.parse_args(self, *args, **kwargs)

        if args.inventory is None:
            self.exit(1, 'Could not detect default inventory path')

        if 'pattern' in args and not Inventory(args.inventory).list_hosts(args.pattern):
            self.exit(1, 'No hosts matched')

        if args.ask_pass:
            args.remote_pass = getpass('Enter remote user password: ')
        else:
            args.remote_pass = None

        if args.ask_sudo_pass:
            args.sudo_pass = getpass('Enter sudo password: ')
        else:
            args.sudo_pass = None

        if args.sudo:
            self.mode = 'sudo %s ' % args.sudo_user
        elif args.su:
            self.mode = 'su %s ' % args.su_user

        return args


class AnsibleScript(GenericAnsibleScript):
    """Ansible script wrapper

    Extend systematic.shell.Script (which wraps argparse.ArgumentParser) to run ansible
    commands with reports.
    """
    runner_class = AnsibleRunner

    def __init__(self, *args, **kwargs):
        GenericAnsibleScript.__init__(self, *args, **kwargs)

        self.add_argument('-i', '--inventory', default=find_inventory(), help='Inventory path')
        self.add_argument('-m', '--module', default=DEFAULT_MODULE_NAME, help='Ansible module name')
        self.add_argument('-M', '--module-path', default=DEFAULT_MODULE_PATH, help='Ansible module path')
        self.add_argument('-T', '--timeout', type=int, default=DEFAULT_TIMEOUT, help='Response timeout')
        self.add_argument('-u', '--user', default=active_user, help='Remote user')
        self.add_argument('-U', '--sudo-user', default=DEFAULT_SUDO_USER, help='Sudo user')
        self.add_argument('--private-key', default=DEFAULT_PRIVATE_KEY_FILE, help='Private key file')
        self.add_argument('--forks', type=int, default=DEFAULT_FORKS, help='Ansible concurrency')
        self.add_argument('--port', type=int, default=DEFAULT_REMOTE_PORT, help='Remote port')
        self.add_argument('-S','--su', action='store_true', help='run operations with su')
        self.add_argument('-s','--sudo', action='store_true', help='run operations with sudo (nopasswd)')
        self.add_argument('-k', '--ask-pass', action='store_true', help='Ask for SSH password')
        self.add_argument('-K', '--ask-sudo-pass', action='store_true', help='Ask for sudo password')
        self.add_argument('-a', '--args', default=DEFAULT_MODULE_ARGS, help='Module arguments')
        self.add_argument('-c', '--colors', action='store_true', help='Show output with colors')
        self.add_argument('pattern', default=DEFAULT_PATTERN, help='Ansible host pattern')

    def run(self):
        """Parse arguments and run ansible command

        Parse provided arguments and run the ansible command with ansiblereporter.result.AnsibleRunner.run()
        """
        args = self.parse_args()

        self.log.debug('runner with %s%s args %s' % (self.mode, args.module, args.args))
        self.runner = self.runner_class(
            host_list=os.path.realpath(args.inventory),
            module_path=args.module_path,
            module_name=args.module,
            module_args=args.args,
            forks='%d' % args.forks,
            timeout=args.timeout,
            pattern=args.pattern,
            remote_user=args.user,
            remote_pass=args.remote_pass,
            remote_port=args.port,
            private_key_file=args.private_key,
            su=args.su,
            sudo=args.sudo,
            sudo_user=args.sudo_user,
            sudo_pass=args.sudo_pass,
            show_colors=args.colors,
        )

        try:
            return args, self.runner.run()
        except AnsibleError, emsg:
            raise RunnerError(emsg)


class PlaybookScript(GenericAnsibleScript):
    """Playbook runner wrapper

    Extend systematic.shell.Script (which wraps argparse.ArgumentParser) to run ansible
    playbooks with reports.
    """
    runner_class = PlaybookRunner

    def __init__(self, *args, **kwargs):
        GenericAnsibleScript.__init__(self, *args, **kwargs)

        self.add_argument('-i', '--inventory', default=find_inventory(), help='Inventory path')
        self.add_argument('-M', '--module-path', default=DEFAULT_MODULE_PATH, help='Ansible module path')
        self.add_argument('-T', '--timeout', type=int, default=DEFAULT_TIMEOUT, help='Response timeout')
        self.add_argument('-u', '--user', default=active_user, help='Remote user')
        self.add_argument('-U', '--sudo-user', default=DEFAULT_SUDO_USER, help='Sudo user')
        self.add_argument('--private-key', default=DEFAULT_PRIVATE_KEY_FILE, help='Private key file')
        self.add_argument('--forks', type=int, default=DEFAULT_FORKS, help='Ansible concurrency')
        self.add_argument('--port', type=int, default=DEFAULT_REMOTE_PORT, help='Remote port')
        self.add_argument('-S','--su', action='store_true', help='run operations with su')
        self.add_argument('-s','--sudo', action='store_true', help='run operations with sudo (nopasswd)')
        self.add_argument('-k', '--ask-pass', action='store_true', help='Ask for SSH password')
        self.add_argument('-K', '--ask-sudo-pass', action='store_true', help='Ask for sudo password')
        self.add_argument('-a', '--args', default=DEFAULT_MODULE_ARGS, help='Module arguments')
        self.add_argument('-c', '--colors', action='store_true', help='Show output with colors')
        self.add_argument('--show-facts', action='store_true', help='Show ansible facts in results')
        self.add_argument('playbook', help='Ansible playbook path')

    def run(self):
        """Parse arguments and run playbook

        Parse provided arguments and run the playbook with ansiblereporter.result.PlaybookRunner.run()
        """
        args = self.parse_args()

        self.runner = self.runner_class(
            playbook=args.playbook,
            host_list=os.path.realpath(args.inventory),
            module_path=args.module_path,
            forks='%d' % args.forks,
            timeout=args.timeout,
            remote_user=args.user,
            remote_pass=args.remote_pass,
            sudo_pass=args.sudo_pass,
            remote_port=args.port,
            transport='smart',
            private_key_file=args.private_key,
            sudo=args.sudo,
            sudo_user=args.sudo_user,
            extra_vars=None,
            only_tags=None,
            skip_tags=None,
            subset=None,
            inventory=None,
            check=False,
            diff=False,
            any_errors_fatal=False,
            vault_password=False,
            force_handlers=False,
            show_colors=args.colors,
            show_facts=args.show_facts,
        )

        try:
            return args, self.runner.run()
        except AnsibleError, emsg:
            raise RunnerError(emsg)
