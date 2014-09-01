"""
Custom callbacks

These callbacks override the chatty behaviour of default ansible playbook
callbacks, allowing us to collect the info and only log the progress to
debug logging.
"""


from ansible import utils
from ansible import callbacks

from ansiblereporter import SortedDict, ReportRunnerError
from systematic.log import Logger

AggregateStats = callbacks.AggregateStats


class PlaybookRunnerCallbacks(callbacks.PlaybookRunnerCallbacks):
    """Playbook runner callbacks

    Override version of ansible.callbacks.PlaybookRunnerCallbacks that
    only logs to default logger with debug messages, not actually doing
    anything else.
    """
    def __init__(self, stats, verbose=None):
        callbacks.PlaybookRunnerCallbacks.__init__(self, stats, verbose)
        self.log = Logger().default_stream

    def on_unreachable(self, host, results):
        self.log.debug('host unreachable %s %s' % (host, results))

    def on_failed(self, host, results, ignore_errors=False):
        self.log.debug('host failed %s %s' % (host, results))

    def on_ok(self, host, host_result):
        self.log.debug('host ok %s %s' % (host, host_result))

    def on_skipped(self, host, item=None):
        self.log.debug('skip %s item %s' % (host, item))

    def on_no_hosts(self):
        self.log.debug('no hosts')

    def on_async_poll(self, host, res, jid, clock):
        self.log.debug('async poll %s' % host)

    def on_async_ok(self, host, res, jid):
        self.log.debug('async ok %s' % host)

    def on_async_failed(self, host, res, jid):
        self.log.debug('async failed %s' % host)

    def on_file_diff(self, host, diff):
        self.log.debug('file diff %s' % host)


class PlaybookCallbacks(callbacks.PlaybookCallbacks):
    """Playbook callbacks

    Override version of ansible.callbacks.PlaybookCallbacks that only logs
    to default logger with debug messages, not actually doing anything else.

    Please note that callback on_vars_prompt is NOT overridden, so if your
    code asks for variables we will use the standard chatty query version!
    """

    def __init__(self, verbose=False):
        callbacks.PlaybookCallbacks.__init__(self, verbose)
        self.log = Logger().default_stream

    def on_start(self):
        self.log.debug('starting playbook')

    def on_notify(self, host, handler):
        self.log.debug('playbook notification')

    def on_no_hosts_remaining(self):
        self.log.debug('playbook no hosts remaining')

    def on_task_start(self, name, is_conditional):
        self.log.debug('playbook starting task "%s"' % name)

    def on_setup(self):
        self.log.debug('playbook setup')

    def on_import_for_host(self, host, imported_file):
        self.log.debug('playbook importing for host %s' % host)

    def on_not_import_for_host(self, host, missing_file):
        self.log.debug('playbook not importing for host %s' % host)

    def on_play_start(self, name):
        self.log.debug('playbook start play %s' % name)

    def on_no_hosts_matched(self):
        raise ReportRunnerError('No hosts matched')

    def on_stats(self, stats):
        self.log.debug('playbook statistics %s' % stats)


