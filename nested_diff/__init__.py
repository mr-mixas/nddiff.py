# -*- coding: utf-8 -*-
#
# Copyright 2018 Michael Samoglyadov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
Recursive diff for nested structures, implementation of
https://github.com/mr-mixas/Nested-Diff

"""

from __future__ import unicode_literals

from difflib import SequenceMatcher
from pickle import dumps


__all__ = ['Differ', 'diff', 'patch']

__version__ = '0.3'
__author__ = 'Michael Samoglyadov'
__license__ = 'Apache License, Version 2.0'
__website__ = 'https://github.com/mr-mixas/Nested-Diff.py'


class Differ(object):
    """
    Compute recursive diff for two passed objects.

    Resulting diff is a dict and may contain following keys:
    `A` stands for 'added', it's value - added item.
    `D` means 'different' and contains subdiff.
    `I` index for list item, used only when prior item was omitted.
    `N` is a new value for changed item.
    `O` is a changed item's old value.
    `R` key used for removed item.
    `U` represent unchanged item.

    Diff metadata alternates with actual data; simple types specified as is,
    lists and dicts contain subdiffs for their items with native for such types
    addressing: indexes for lists and keys for dictionaries. Each status type,
    except `D` and `I`, may be (optionally) omitted during diff computation.

    Example:

    a:  {"one": [5,7]}
    b:  {"one": [5], "two": 2}
    opts: U=False  # omit unchanged items

    diff:
    {"D": {"one": {"D": [{"I": 1, "R": 7}]}, "two": {"A": 2}}}
    | |   |  |    | |   || |   |   |   |       |    | |   |
    | |   |  |    | |   || |   |   |   |       |    | |   +- with value 2
    | |   |  |    | |   || |   |   |   |       |    | +- key 'two' was added
    | |   |  |    | |   || |   |   |   |       |    +- subdiff for it
    | |   |  |    | |   || |   |   |   |       +- another key from top-level
    | |   |  |    | |   || |   |   |   +- what it was (item's value: 7)
    | |   |  |    | |   || |   |   +- what happened to item (removed)
    | |   |  |    | |   || |   +- list item's actual index
    | |   |  |    | |   || +- prior item was omitted
    | |   |  |    | |   |+- subdiff for list item
    | |   |  |    | |   +- it's value - list
    | |   |  |    | +- it is deeply changed
    | |   |  |    +- subdiff for key 'one'
    | |   |  +- it has key 'one'
    | |   +- top-level thing is a dict
    | +- changes somewhere deeply inside
    +- diff is always a dict

    Dicts and lists traversed recursively, all other types compared by values.

    """
    def __init__(self, A=True, N=True, O=True, R=True, U=True, trimR=False):
        """
        Construct Differ.

        Optional arguments:
        `A`, `N`, `O`, `R`, `U` are toggles for according diff ops and all set
        to True by default.

        `trimR` when True drops (replaces by `None`) removed data from diff,
        default is False.

        """
        self.lcs = SequenceMatcher(isjunk=None, autojunk=False)

        self.op_a = A
        self.op_n = N
        self.op_o = O
        self.op_r = R
        self.op_u = U
        self.op_trim_r = trimR

    def diff(self, a, b):
        """
        Compute diff for two arbitrary objects.

        This method is a dispatcher and calls `diff_dicts` for dicts,
        `diff_lists` for lists and so forth.

        :param a: First object to diff.
        :param b: Second object to diff.

        """
        if a == b:
            return {'U': a} if self.op_u else {}

        if isinstance(a, dict) and isinstance(a, type(b)):
            return self.diff_dicts(a, b)

        if isinstance(a, list) and isinstance(a, type(b)):
            return self.diff_lists(a, b)

        return self.get_default_diff(a, b)

    def diff_dicts(self, a, b):
        """
        Compute diff for two dicts.

        :param a: First dict to diff.
        :param b: Second dict to diff.

        >>> a = {'one': 1, 'two': 2, 'three': 3}
        >>> b = {'one': 1, 'two': 42}
        >>>
        >>> Differ(O=False, U=False).diff_dicts(a, b)
        {'D': {'two': {'N': 42}, 'three': {'R': 3}}}
        >>>

        """
        ret = {'D': {}}

        for key in set(list(a) + list(b)):
            if key in a and key in b:
                if a[key] == b[key]:
                    if self.op_u:
                        ret['D'][key] = {'U': a[key]}
                else:
                    subdiff = self.diff(a[key], b[key])
                    if subdiff:
                        ret['D'][key] = subdiff

            elif key in a:  # removed
                if self.op_r:
                    ret['D'][key] = {'R': None if self.op_trim_r else a[key]}

            elif key in b:  # added
                if self.op_a:
                    ret['D'][key] = {'A': b[key]}

        if not ret['D']:
            del ret['D']

        return ret

    def diff_lists(self, a, b):
        """
        Compute diff for two lists.

        :param a: First list to diff.
        :param b: Second list to diff.

        >>> a = [0,1,2,3]
        >>> b = [  1,2,4,5]
        >>>
        >>> Differ(O=False, U=False).diff_lists(a, b)
        {'D': [{'R': 0}, {'N': 4, 'I': 3}, {'A': 5}]}
        >>>

        """
        self.lcs.set_seq1([dumps(i, -1) for i in a])
        self.lcs.set_seq2([dumps(i, -1) for i in b])

        ret = {'D': []}
        i = j = 0
        force_index = False

        for ai, bj, _ in self.lcs.get_matching_blocks():
            while i < ai and j < bj:
                subdiff = self.diff(a[i], b[j])
                if subdiff:
                    ret['D'].append(subdiff)
                    if force_index:
                        ret['D'][-1]['I'] = i
                        force_index = False
                else:
                    force_index = True

                i += 1
                j += 1

            while i < ai:  # removed
                if self.op_r:
                    ret['D'].append({'R': None if self.op_trim_r else a[i]})
                    if force_index:
                        ret['D'][-1]['I'] = i
                        force_index = False
                else:
                    force_index = True

                i += 1

            while j < bj:  # added
                if self.op_a:
                    ret['D'].append({'A': b[j]})
                    if force_index:
                        ret['D'][-1]['I'] = i
                        force_index = False
                else:
                    force_index = True

                j += 1

        if not ret['D']:
            del ret['D']

        return ret

    def get_default_diff(self, a, b):
        """
        Return default diff.

        """
        ret = {}

        if self.op_n:
            ret['N'] = b
        if self.op_o:
            ret['O'] = a

        return ret


def patch(target, diff):
    """
    Return patched object.

    :param target: Object to patch.
    :param diff: Nested diff.

    """

    if 'D' in diff:
        if isinstance(diff['D'], dict):
            for key, subdiff in diff['D'].items():
                if 'D' in subdiff or 'N' in subdiff:
                    target[key] = patch(target[key], subdiff)
                elif 'A' in subdiff:
                    target[key] = subdiff['A']
                elif 'R' in subdiff:
                    del target[key]

        elif isinstance(diff['D'], list):
            i, j = 0, 0  # index, scatter

            for subdiff in diff['D']:
                if 'I' in subdiff:
                    i = subdiff['I'] + j

                if 'D' in subdiff or 'N' in subdiff:
                    target[i] = patch(target[i], subdiff)
                elif 'A' in subdiff:
                    target.insert(i, subdiff['A'])
                    j += 1
                elif 'R' in subdiff:
                    del target[i]
                    j -= 1
                    continue

                i += 1
        else:
            raise NotImplementedError("unsupported type for patch")
    elif 'N' in diff:
        target = diff['N']

    return target


def diff(a, b, **kwargs):
    """
    Compute recursive diff for two passed objects.

    Just a wrapper around Differ.diff() for backward compatibility.

    :param a: First object to diff.
    :param b: Second object to diff.

    See Differ class for keywords options.

    """
    return Differ(**kwargs).diff(a, b)
