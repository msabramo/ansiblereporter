"""
Ansible runner wrapper for output reporting tasks
"""

import os
import json

from seine.address import IPv4Address
from ansible.runner import Runner

from ansiblereporter import SortedDict


class ReportRunnerError(Exception): pass


class Result(SortedDict):
    compare_fields = ( 'resultset', 'address', 'host', )
    def __init__(self, resultset, host, data):
        SortedDict.__init__(self)
        self.resultset = resultset
        self.host = host

        try:
            self.address = IPv4Address(host)
        except ValueError:
            self.address = None

        self.update(**data)

    def __repr__(self):
        return '%s %s' % (self.host, self.state)

    @property
    def stdout(self):
        return 'stdout' in self and self['stdout'] or ''

    @property
    def stderr(self):
        return 'stderr' in self and self['stderr'] or ''

    @property
    def state(self):
        return self.resultset.name

    @property
    def status(self):
        if 'failed' in self:
            return 'failed'

        elif 'rc' in self:
            if self['rc'] == 0:
                return 'ok'
            return 'error'

        return 'unknown'

    def write_to_directory(self, directory, to_json=False):
        extension = to_json and 'json' or 'txt'
        filename = os.path.join(directory, '%s.%s' % (self.host, extension))
        self.log.debug('writing to %s' % filename)

        if to_json:
            open(filename, 'w').write('%s\n' % json.dumps({
                'stdout': self.stdout,
                'stderr': self.stderr
                },
                indent=2
            ))
        else:
            open(filename, 'w').write('\n'.join([self.stdout, self.stderr]))

class ResultSet(list):
    def __init__(self, runner, name):
        self.runner = runner
        self.name = name

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __repr__(self):
        return 'result group %s' % self.name

    def append(self, host, result):
        list.append(self, Result(self, host, result))


class RunnerResults(list):
    def __init__(self, runner, results):
        self.runner = runner
        for k in ( 'dark', 'contacted', ):
            if k in results:
                group = ResultSet(self, k)
                setattr(self, k, group)

                for host, result in results[k].items():
                    group.append(host, result)

            else:
                setattr(self, k, [])

    @property
    def summary(self):
        summary = {
            'dark': len(self.dark),
            'contacted': len(self.contacted),
            'ok': 0,
            'error': 0,
            'failed': 0,
            'unknown': 0,
        }
        for c in self.contacted:
            try:
                summary[c.status] += 1
            except KeyError:
                summary['unknown'] += 1
        return summary

    def sort(self):
        self.dark.sort()
        self.contacted.sort()


class ReportRunner(Runner):
    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)

    def run(self, *args, **kwargs):
        results = Runner.run(self, *args, **kwargs)
        return self.process_results(results)

    def process_results(self, results):
        return RunnerResults(self, results)


