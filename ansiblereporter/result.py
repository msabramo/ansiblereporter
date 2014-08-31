"""
Ansible runner wrapper for output reporting tasks
"""

import os
import json

from datetime import datetime
from ansible.playbook import PlayBook
from ansible.runner import Runner
from seine.address import IPv4Address
from systematic.log import Logger

from ansiblereporter import SortedDict, ReportRunnerError
from ansiblereporter.reporter_callbacks import AggregateStats, PlaybookCallbacks, PlaybookRunnerCallbacks


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
    def module_name(self):
        try:
            return self['invocation']['module_name']
        except KeyError:
            return ''

    @property
    def command(self):
        try:
            return self['invocation']['module_args']
        except KeyError:
            return ''

    @property
    def returncode(self):
        return 'rc' in self and self['rc'] or 0

    @property
    def error(self):
        return 'msg' in self and self['msg'] or 'UNKNOWN ERROR'

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
    def changed(self):
        try:
            return self['changed']
        except KeyError:
            return False

    @property
    def ansible_facts(self):
        try:
            return self.resultset.ansible_facts[self.host]
        except KeyError:
            return None

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

        elif self.module_name == 'setup':
            return 'facts'

        return 'unknown'

    @property
    def ansible_status(self):
        if 'failed' in self:
            return 'FAILED'

        elif 'rc' in self:
            if self['rc'] == 0:
                return 'success'
            return 'FAILED'

        elif self.module_name == 'setup':
            return 'FACTS'

        return 'UNKNOWN'

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
        self.log = Logger().default_stream
        self.runner = runner
        self.name = name
        self.ansible_facts = {}

    def append(self, host, result):
        list.append(self, Result(self, host, result))
        if 'ansible_facts' in result:
            self.ansible_facts[host] = result['ansible_facts']

    def to_json(self, indent=2):
        return json.dumps(self, indent=indent)


class ResultList(object):
    def __init__(self, runner, show_colors=False):
        self.runner = runner
        self.show_colors = show_colors
        self.log = Logger().default_stream

        self.results = {
            'contacted': ResultSet(self, 'contacted'),
            'dark': ResultSet(self, 'dark'),
        }

    def sort(self):
        self.results['dark'].sort()
        self.results['contacted'].sort()

    def to_json(self, indent=2):
        return json.dumps({
                'contacted': self.results['contacted'],
                'dark': self.results['dark'],
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
            for result in self.results['contacted']:
                fd.write('%s\n' % formatter(result))
            for result in self.results['dark']:
                fd.write('%s\n' % formatter(result))

        fd.close()


class RunnerResults(ResultList):
    def __init__(self, runner, results, show_colors=False):
        ResultList.__init__(self, runner, show_colors)

        for k in ( 'dark', 'contacted', ):
            if k in results:
                group = self.results[k]
                for host, result in results[k].items():
                    group.append(host, result)

class PlaybookResults(ResultList, AggregateStats):
    def __init__(self, runner, show_colors=False):
        AggregateStats.__init__(self)
        ResultList.__init__(self, runner, show_colors)

    def _increment(self, what, host):
        ''' helper function to bump a statistic '''
        self.processed[host] = 1
        prev = (getattr(self, what)).get(host, 0)
        getattr(self, what)[host] = prev+1

    def compute(self, runner_results, setup=False, poll=False, ignore_errors=False):
        for (host, value) in runner_results.get('contacted', {}).iteritems():
            self.results['contacted'].append(host, value)

        for (host, value) in runner_results.get('dark', {}).iteritems():
            self.results['dark'].append(host, value)

    def summarize(self, host):
        """

        """
        return {
            'contacted': self.results['contacted'],
            'dark': self.results['dark'],
        }

    def to_json(self, indent=2):
        data = { 'contacted': [], 'dark': [] }
        res = {}
        for result in self.results['contacted']:
            if result.host not in res:
                res[result.host] = {'host': result.host, 'results': []}

            if result.module_name == 'setup' and not self.runner.show_facts:
                continue

            res[result.host]['results'].append(result.copy())

        for key in sorted(res.keys()):
            data['contacted'].append(res[key])

        return json.dumps(data, indent=indent)

    def write_to_file(self, filename, formatter=None, json=False):
        if not formatter and not json:
            raise ReportRunnerError('Either formatter callback or json flag must be set')
        fd = open(filename, 'w')
        if json:
            fd.write('%s\n' % self.to_json())
        elif formatter:
            for result in self.results['contacted']:
                if result.module_name == 'setup' and not self.runner.show_facts:
                    continue
                fd.write('%s\n' % formatter(result))
            for result in self.results['dark']:
                if result.module_name == 'setup' and not self.runner.show_facts:
                    continue
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


class PlaybookRunner(PlayBook):
    def __init__(self, *args, **kwargs):
        self.show_colors = kwargs.pop('show_colors', False)
        self.show_facts = kwargs.pop('show_facts', False)

        self.results = PlaybookResults(self, self.show_colors)
        self.callbacks = PlaybookCallbacks()
        self.runner_callbacks = PlaybookRunnerCallbacks(self.results)

        kwargs['callbacks'] =self.callbacks
        kwargs['runner_callbacks'] = self.runner_callbacks
        kwargs['stats'] = self.results
        PlayBook.__init__(self, *args, **kwargs)

    def run(self, *args, **kwargs):
        stats = PlayBook.run(self, *args, **kwargs)
        return self.process_results(self.results)

    def process_results(self, results):
        self.results.sort()
        return self.results
