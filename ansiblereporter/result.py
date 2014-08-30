"""
Ansible runner wrapper for output reporting tasks
"""

import os
import json

from datetime import datetime
from ansible.runner import Runner
from seine.address import IPv4Address

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
        return ' '.join([self.host, self.status, self.end])

    @property
    def show_colors(self):
        return self.resultset.runner.show_colors

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
    def chaned(self):
        try:
            return self['changed']
        except KeyError:
            return False

    @property
    def start(self):
        try:
            return datetime.strptime(self['start'], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
        except KeyError:
            return ''

    @property
    def end(self):
        try:
            return datetime.strptime(self['end'], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
        except KeyError:
            return ''

    @property
    def delta(self):
        try:
            return datetime.strptime(self['delta'], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
        except KeyError:
            return ''

    @property
    def status(self):
        if 'failed' in self:
            return 'failed'

        elif 'rc' in self:
            if self['rc'] == 0:
                return 'ok'
            return 'error'

        return 'unknown'

    def write_to_directory(self, directory, callback, extension):
        filename = os.path.join(directory, '%s.%s' % (self.host, extension))
        self.log.debug('writing to %s' % filename)

        open(filename, 'w').write('%s\n' % callback(self))

    def format(self, callback):
        return callback(self)

    def to_json(self, indent=2):
        return json.dumps(self, indent=indent)


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

    def to_json(self, indent=2):
        return json.dumps(self, indent=indent)

class RunnerResults(list):
    def __init__(self, runner, results, show_colors=False):
        self.runner = runner
        self.show_colors = show_colors

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

    def to_json(self, indent=2):
        return json.dumps({
                'contacted': self.contacted,
                'dark': self.dark,
            },
            indent=indent
        )

    def write_to_file(self, filename, formatter=None, json=False):
        if not formatter and not json:
            raise ReportRunnerError('Either formatter callback or json flag must be set')
        fd = open(filename, 'w')
        if json:
            fd.write('%s\n' % self.to_json())
        elif formatter:
            for result in self.contacted:
                fd.write('%s\n' % formatter(result))

        fd.close()


class ReportRunner(Runner):
    def __init__(self, *args, **kwargs):
        self.show_colors = kwargs.pop('show_colors', False)
        Runner.__init__(self, *args, **kwargs)

    def run(self, *args, **kwargs):
        results = Runner.run(self, *args, **kwargs)
        return self.process_results(results, show_colors=self.show_colors)

    def process_results(self, results, show_colors=False):
        return RunnerResults(self, results, show_colors)


