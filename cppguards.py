#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

ROOT_NAMES = 'src', 'source'
SKIPPED_NAMES = 'test', 'tests', 'impl'
SUFFIX = 'H_INCLUDED'

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

def get_guard(fname):
    fname = os.path.abspath(fname)
    root, path = _find_root(fname)
    path = [p for p in path if p not in SKIPPED_NAMES]
    path[-1], extension = os.path.splitext(path[-1])
    assert extension == '.h'

    path.append(SUFFIX)
    return '_'.join(p.upper() for p in path)

def add_guards(fname):
    guard = get_guard(fname)
    guard_lines = ['#ifndef %s\n' % guard, '#define %s\n' % guard, '\n']
    contents = open(fname, 'r').readlines()

    for i, line in enumerate(contents):
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

    open(fname, 'w').writelines(contents)

if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        raise Exception('Usage: cppguards <file> [<file> ...]')
    for f in args:
        add_guards(f)
