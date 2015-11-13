#!/usr/bin/python

from __future__ import absolute_import

import os
import sys
import argparse
import logging
import yaml
import jinja2
import subprocess
import fnmatch
import augeas

import stackcheck.formatter.simple

LOG = logging.getLogger(__name__)


class Constant (object):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return '<Constant: %s>' % self.value

Undefined = Constant('Undefined')


def filter_bool(v):
    if v.lower() in ['true', 'yes', 'y', '1']:
        return True
    elif v.lower() in ['false', 'no', 'n', '0']:
        return False
    else:
        raise ValueError(v)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--verbose', '-v',
                   action='store_const',
                   const='INFO',
                   dest='loglevel')
    p.add_argument('--debug', '-d',
                   action='store_const',
                   const='DEBUG',
                   dest='loglevel')
    p.add_argument('--facts', '-f')
    p.add_argument('--facter', '-F',
                   action='store_true')
    p.add_argument('--ruleset', '-r',
                   action='append',
                   default=[])
    p.add_argument('--option', '-o',
                   action='append',
                   default=[])
    p.add_argument('--root')
    p.add_argument('--loadpath', '-I')
    p.add_argument('--pdb', action='store_true')

    p.add_argument('rules')

    p.set_defaults(loglevel='WARN')
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=args.loglevel)

    formatter = stackcheck.formatter.simple.Formatter(
        verbose=(args.loglevel == 'INFO'))

    with open(args.rules) as fd:
        rules = yaml.load(fd)

    env = jinja2.Environment()
    env.filters['bool'] = filter_bool

    if args.facts:
        with open(args.facts) as fd:
            facts = yaml.load(fd)
    elif args.facter:
        facts = yaml.load(subprocess.check_output(['facter', '--yaml']))
    else:
        facts = {}

    parser = augeas.Augeas(root=args.root,
                           loadpath=args.loadpath)
    for spec in rules['load']:
        paths = (spec['path'] if isinstance(spec['path'], list)
                 else spec['path'])
        for path in paths:
            parser.add_transform(spec['lens'], path)

    parser.load()

    if args.pdb:
        import pdb; pdb.set_trace()

    formatter.start_run()

    for ruleset in rules['rulesets']:
        if args.ruleset:
            for pat in args.ruleset:
                if fnmatch.fnmatch(ruleset['name'], pat):
                    break
            else:
                continue

        formatter.start_ruleset(ruleset)

        for rule in ruleset['rules']:
            context = {
                'rule': rule,
                'ruleset': ruleset,
                'facts': facts,
            }

            for varname, varpat in rule['vars'].items():
                # Iterate over the listed augeas path expressions
                # and take the first one that returns a non-None
                # result.
                for pat in (varpat if isinstance(varpat, list) else [varpat]):
                    value = parser.get('/files' + pat)
                    if value is not None:
                        break

                if value is not None:
                    context[varname] = value

            formatter.start_rule(rule)

            if 'assert' in rule:
                expr = env.compile_expression(rule['assert'])
                res = expr(**context)

                if res:
                    status = 'OKAY'
                else:
                    status = 'FAILED'
            else:
                status = 'SKIPPED'

            if 'message' in rule:
                message_tmpl = env.from_string(rule['message'])
                message = message_tmpl.render(**context)
            else:
                message = None

            formatter.stop_rule(rule, status, message)
        formatter.stop_ruleset(ruleset)
    formatter.stop_run()


if __name__ == '__main__':
    p = main()
