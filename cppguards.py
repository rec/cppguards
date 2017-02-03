#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

# Don't include unicode_literals to improve legacy code.

import argparse
import os
import sys

NAME = 'cppguards'
VERSION = '1.0'

PARSER = argparse.ArgumentParser(
    prog='cppguards',
    description='Add #ifdef guards to C/C++ header files.',
    )

# Positional arguments.
PARSER.add_argument(
    'files',
    nargs='+',
    help='Files to clean.'
)

# Flag arguments

PARSER.add_argument(
    '--continue',
    action='store_true',
    help="Keep going even if there's an error in one file.",
)

PARSER.add_argument(
    '--repeats',
    action='store_true',
    help='Keep repeated directories in the guard.',
)

PARSER.add_argument(
    '--noexecution', '-n',
    action='store_true',
    help='If set, print the guards without editing the files.',
)

PARSER.add_argument(
    '--roots',
    default='src:source',
    help='Names of directories that might be the root of the source tree.',
)

PARSER.add_argument(
    '--skip',
    default='test:tests:impl',
    help='Names of directories that should be skipped in forming a guard.',
)

PARSER.add_argument(
    '--suffix',
    default='H_INCLUDED',
    help='Suffix added to the end of the guard.',
)

ARGS = PARSER.parse_args()

ROOT_NAMES = ARGS.roots.split(':')
SKIPPED_NAMES = ARGS.skip.split(':')

def _find_root(fname):
    path = []
    while True:
        head, tail = os.path.split(fname)
        if not head:
            raise ValueError(
                "Couldn't find root directory: looking in %s" %
                ':'.join(ROOT_NAMES))
        if tail in ROOT_NAMES:
            return fname, path
        fname = head
        path.insert(0, tail)

def _remove_extensions(fname):
    extensions = []
    while True:
        fname, ext = os.path.splitext(fname)
        if ext:
            extensions.insert(0, ext)
        else:
            return fname, extensions

def get_guard(fname):
    fname = os.path.abspath(fname)
    root, path = _find_root(fname)
    path = [p for p in path if p not in SKIPPED_NAMES]

    if not ARGS.repeats:
        path = [p for (i, p) in enumerate(path)
                if not (i and path[i] == path[i - 1])]

    path[-1], extensions = _remove_extensions(path[-1])
    assert extensions, ', '.join((fname, root, str(path)))
    assert extensions[-1] == '.h'

    path.append(ARGS.suffix)
    return '_'.join(p.upper() for p in path).replace('-', '_')


def add_guards(fname):
    guard = get_guard(fname)
    guard_lines = ['#ifndef %s\n' % guard, '#define %s\n' % guard, '\n']
    contents = open(fname, 'r').readlines()

    for i, line in enumerate(contents):
        try:
            if line.startswith('#ifndef'):
                count = 2 if contents[i + 1].startswith('#define') else 1
                if contents[i + count].isspace():
                    count += 1
                contents[i:i + count] = guard_lines
                break
            if line.startswith('#'):
                contents[i:i] = guard_lines
                contents.append('#endif\n')
                break
        except UnicodeDecodeError as e:
            e.reason += ' on line %d' % (1 + i)
            raise e

    open(fname, 'w').writelines(contents)


if __name__ == '__main__':
    for f in ARGS.files:
        if ARGS.noexecution:
            print('%s: %s' % (f, get_guard(f)))
        else:
            try:
                add_guards(f)
            except Exception as e:
                e.reason += ' in file "%s".' % f
                if getattr(ARGS, 'continue'):
                    print('ERROR:', e.reason)
                else:
                    raise
