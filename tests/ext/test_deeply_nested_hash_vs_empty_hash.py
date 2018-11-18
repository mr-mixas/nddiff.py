"""
Do not edit manually! Generated from
https://github.com/mr-mixas/Nested-Diff/tree/master/tests/json/deeply_nested_hash_vs_empty_hash.json
"""

from __future__ import unicode_literals
import nested_diff


def test_deeply_nested_hash_vs_empty_hash():
    a = {'one': {'two': {'three': 3}}}
    b = {}
    diff = {'D': {'one': {'R': {'two': {'three': 3}}}}}
    opts = {}
    assert diff == nested_diff.diff(a, b, **opts)