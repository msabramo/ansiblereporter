"""
Extended ansible.inventory.Inventory to support editing and saving to file.
"""

import os
import re
import configobj

from systematic.log import Logger

from ansible.errors import AnsibleError
from ansible.inventory import Inventory as AnsibleInventory
from ansible.inventory.group import Group
from ansible.inventory.host import Host

HEADER = """# Automatically generated with ansible-inventory tool."""


HOST_VARIABLES_SAVE_IGNORE = (
    'group_names',
    'inventory_hostname_short',
    'inventory_hostname',
)


class InventoryError(Exception):
    pass


class Inventory(AnsibleInventory):
    def __init__(self, *args, **kwargs):
        self.log = Logger().default_stream
        try:
            AnsibleInventory.__init__(self, *args, **kwargs)
        except AnsibleError, emsg:
            raise InventoryError(emsg)

    def add_group(self, group):
        if isinstance(group, basestring):
            group = Group(group)
        try:
            self.log.debug('add inventory group: %s' % group.name)
            AnsibleInventory.add_group(self, group)
        except AnsibleError, emsg:
            raise InventoryError(emsg)
        return group

    def add_host(self, group, host):
        if isinstance(group, basestring):
            g = self.get_group(group)
            group = g is None and self.add_group(group) or g

        if host in [h.name for h in group.get_hosts()]:
            raise InventoryError('Host already in group %s: %s' % (group.name, host))

        if isinstance(host, basestring):
            host = Host(host)

        self.log.debug('group %s: add host: %s' % (group.name, host.name))
        group.add_host(host)
        return group

    def save(self, path, minimize=True):
        def parse_hosts(hosts, minimize):
            if not minimize:
                return hosts

            prefixed = {}
            grouped = []

            return hosts

        def format_host(host):
            line = host.name
            for k, v in host.get_variables().items():
                if k not in HOST_VARIABLES_SAVE_IGNORE:
                    line += ' %s=%s' % (k,v)
            return line

        path = os.path.expanduser(os.path.expandvars(path))
        self.log.debug('Saving inventory to %s' % path)

        try:

            fd = open(path, 'wb')

            fd.write(HEADER)

            ungrouped = parse_hosts(self.get_group('ungrouped').hosts, minimize)
            if ungrouped:
                fd.write('\n')
                for host in ungrouped:
                    fd.write('%s\n' % format_host(host))

            for group in sorted(self.get_groups(), lambda a, b: cmp(a.name, b.name)):
                if group.name in ('all', 'ungrouped'):
                    continue

                if group.child_groups:
                    fd.write('\n[%s:children]\n' % (group.name))
                    for child in [child for child in group.child_groups if child.name != group.name]:
                        fd.write('%s\n' % child.name)

                else:
                    fd.write('\n[%s]\n' % (group.name))
                    for host in parse_hosts(group.hosts, minimize):
                        fd.write('%s\n' % format_host(host))

            fd.write('\n')
            fd.close()

        except IOError:
            raise InventoryError('Error opening %s for writing: %s' % (path, emsg))

        except OSError, (ecode, emsg):
            raise InventoryError('Error opening %s for writing: %s' % (path, emsg))

