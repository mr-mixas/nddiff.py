# -*- coding: utf-8 -*-
#
# Copyright 2019,2020 Michael Samoglyadov
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
Patch tool for nested diff.

"""
import argparse
import nested_diff.cli


class App(nested_diff.cli.App):
    """
    Patch tool for nested data structures

    """
    def dump(self, file_, data, fmt):
        if fmt == 'auto':
            fmt = self.guess_fmt(file_, 'json')

        super().dump(file_, data, fmt)

    def get_positional_args_parser(self):
        parser = super().get_positional_args_parser()

        parser.add_argument('target_file')
        parser.add_argument('patch_file', type=argparse.FileType())

        return parser

    @staticmethod
    def patch(target, diff):
        """
        Return patched object

        :param target: object to patch.
        :param diff: nested diff.

        """
        return nested_diff.patch(target, diff)

    def run(self):
        patched = self.patch(
            self.load(argparse.FileType()(self.args.target_file)),
            self.load(self.args.patch_file),
        )

        self.dump(
            argparse.FileType('w')(self.args.target_file),
            patched,
            self.args.ofmt,
        )

        return 0


def cli():
    return App().run()
