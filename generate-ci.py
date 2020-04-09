#!/usr/bin/env python3

import os
import sys
import json
import argparse

from ruamel.yaml import YAML

DISTS = {
    "4.0": {
        "dom0": 'fc25',
        "vm": [
            "fc30",
            "fc31",
            "centos7",
            "stretch",
            "buster"
        ]
    },
    "4.1": {
        "dom0": 'fc32',
        "vm": [
            "fc30",
            "fc31",
            "fc32",
            "centos7",
            "centos8",
            "stretch",
            "buster",
            "bullseye"
        ]
    }
}

COMMON = {
    "os": "linux",
    "dist": "bionic",
    "language": "generic",
    "install": "git clone https://github.com/QubesOS/qubes-builder ~/qubes-builder",
    "script": "~/qubes-builder/scripts/travis-build"
}

# don't build tags which are meant for code signing only
BRANCHES = {
    "branches": {
        "except": [
            "/.*_.*/",
            "build"
        ]
    }
}

ENVS = {
    'env': []
}


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release",
        default="4.1"
    )
    parser.add_argument(
        "--all",
        required=False,
        action="store_true"
    )
    parser.add_argument(
        "--dom0",
        required=False,
        action="store_true"
    )
    parser.add_argument(
        "--vms",
        required=False,
        action="store_true"
    )

    return parser.parse_args()


class QubesCI:
    def __init__(self, qubes_release):
        self.qubes_release = qubes_release

    def generate_dom0(self, to_string=True):
        default_env = [
            'USE_QUBES_REPO_VERSION=%s' % self.qubes_release,
            'USE_QUBES_REPO_TESTING=1'
        ]
        env = ['DIST_DOM0=%s' % DISTS[self.qubes_release]['dom0']] + default_env
        if to_string:
            env = ' '.join(env)
        return [env]

    def generate_vms(self, to_string=True):
        default_env = [
            'USE_QUBES_REPO_VERSION=%s' % self.qubes_release,
            'USE_QUBES_REPO_TESTING=1'
        ]
        envs = []
        vms = DISTS[self.qubes_release]['vm']
        for vm in vms:
            env = ['DISTS_VM=%s' % vm] + default_env
            if to_string:
                env = ' '.join(env)
            envs.append(env)

        return envs

    @staticmethod
    def write_yml(content, path):
        try:
            travis_yml = YAML()
            travis_yml.indent(sequence=4, offset=2)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as yml_fd:
                travis_yml.dump(content, yml_fd)
        except FileNotFoundError as e:
            print("Cannot write %s: %s" % (path, str(e)))

    def write_base(self):

        base = {
            **COMMON,
            **BRANCHES
        }
        travis_path = 'R%s/travis-base-r%s.yml' % (self.qubes_release,
                                                   self.qubes_release)
        self.write_yml(base, travis_path)

    def write_dom0(self):
        envs = ENVS
        envs['env'] = self.generate_dom0()
        travis_path = 'R%s/travis-dom0-r%s.yml' % (self.qubes_release,
                                                   self.qubes_release)

        self.write_yml(envs, travis_path)

    def write_vms(self):
        envs = ENVS
        envs['env'] = self.generate_vms()
        travis_path = 'R%s/travis-vms-r%s.yml' % (self.qubes_release,
                                                  self.qubes_release)

        self.write_yml(envs, travis_path)

    def write_all(self):
        self.write_base()
        self.write_dom0()
        self.write_vms()


def main():
    args = get_args()
    qubesci = QubesCI(args.release)

    if args.all:
        qubesci.write_all()
    else:
        if args.dom0:
            qubesci.write_dom0()
        if args.vms:
            qubesci.write_vms()


if __name__ == '__main__':
    sys.exit(main())
