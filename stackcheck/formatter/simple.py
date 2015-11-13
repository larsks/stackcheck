from __future__ import absolute_import

import time
import textwrap
import termcolor

import stackcheck.formatter.base


class Formatter(stackcheck.formatter.base.Formatter):

    def start_run(self):
        print '=' * 60
        print 'Starting stackcheck run @ %s' % (time.ctime())
        print '=' * 60
        print

    def stop_run(self):
        print
        print '=' * 60
        print 'Finished stackcheck run @ %s' % (time.ctime())
        print '=' * 60

    def start_ruleset(self, ruleset):
        print 'Starting ruleset {name}'.format(**ruleset)

    def stop_ruleset(self, ruleset):
        print 'Finished ruleset {name}'.format(**ruleset)
        print

    def start_rule(self, rule):
        print '* {name}:'.format(**rule),

    def stop_rule(self, rule, status, message=None):
        if status == 'FAILED':
            fgcolor = 'red'
        elif status == 'OKAY':
            fgcolor = 'green'
        elif status == 'SKIPPED':
            fgcolor == 'blue'

        print termcolor.colored(status, fgcolor)

        if status == 'FAILED' and message and self.verbose:
            print
            for p in message.splitlines():
                print textwrap.fill(p,
                                    initial_indent=' '*4,
                                    subsequent_indent=' '*4,
                                    replace_whitespace=False)
                print
