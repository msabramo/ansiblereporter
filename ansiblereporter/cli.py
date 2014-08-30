"""
Wrap systematic's Script to run ansible commands
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
from ansiblereporter.result import ReportRunner, ReportRunnerError

DEFAULT_INVENTORY_PATHS = (
    os.path.expanduser('~/.ansible.hosts'),
    DEFAULT_HOST_LIST,
)


logger = Logger().default_stream


def find_inventory():
    for hostlist in DEFAULT_INVENTORY_PATHS:
        if os.path.isfile(hostlist):
            return hostlist

    return None


def create_directory(directory):
    if os.path.isdir(directory):
        logger.debug('directory already exists: %s' % directory)
        return

    try:
        os.makedirs(directory)
    except IOError, (ecode, emsg):
        raise ReportRunnerError('Error creating directory %s: %s' % (directory, emsg))
    except OSError, (ecode, emsg):
        raise ReportRunnerError('Error creating directory %s: %s' % (directory, emsg))


class ReportScript(Script):
    def __init__(self, *args, **kwargs):
        Script.__init__(self, *args, **kwargs)
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

        self.runner = None

    def SIGINT(self, signum, frame):
        """
        Parse SIGINT signal by quitting the program cleanly with exit code 1
        """
        if self.runner is not None:
            raise KeyboardInterrupt()
        else:
            self.exit(1)

    def run(self):
        args = self.parse_args()

        if args.inventory is None:
            self.exit(1, 'Could not detect default inventory path')

        if not Inventory(args.inventory).list_hosts(args.pattern):
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
            mode = 'sudo %s ' % args.sudo_user
        elif args.su:
            mode = 'su %s ' % args.su_user
        else:
            mode = ''
        self.log.debug('run with %s%s args %s' % (mode, args.module, args.args))

        self.runner = ReportRunner(
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
            raise ReportRunnerError(emsg)
