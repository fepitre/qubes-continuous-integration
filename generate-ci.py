#!/usr/bin/env python3

import os
import sys
import json
import argparse

from ruamel.yaml import YAML

DISTS = {
    "4.0": {
        "dom0": 'fc25',
        "vms": {
            "rpm": [
                "fc30",
                "fc31"
            ],
            "deb": [
                "stretch",
                "buster"
            ]
        }
    },
    "4.1": {
        "dom0": 'fc31',
        "vms": {
            "rpm": [
                "fc30",
                "fc31",
                "fc32",
                "centos7",
                "centos8"
            ],
            "deb": [
                "stretch",
                "buster",
                "bullseye"
            ]
        }
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

VMS = {
    'import': []
}

FLAVORS = {
    'rpm': [
        "minimal",
        "xfce"
    ],
    'deb': [
        "minimal"
    ]
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

    def generate_vms(self, distro, to_string=True, only_flavors=False):
        default_env = [
            'USE_QUBES_REPO_VERSION=%s' % self.qubes_release,
            'USE_QUBES_REPO_TESTING=1'
        ]
        envs = []
        vms = DISTS[self.qubes_release]['vms']
        for vm in vms[distro]:
            if only_flavors:
                for flavor in FLAVORS[distro]:
                    env = ['DISTS_VM=%s+%s' % (vm, flavor)] + default_env
                    if to_string:
                        env = ' '.join(env)
                    envs.append(env)
            else:
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
        travis_path = 'R{release}/travis-base-r{release}.yml'.format(
            release=self.qubes_release)
        self.write_yml(base, travis_path)

    def write_dom0(self):
        envs = ENVS
        envs['env'] = self.generate_dom0()
        travis_path = 'R{release}/travis-dom0-r{release}.yml'.format(
            release=self.qubes_release)

        self.write_yml(envs, travis_path)

    def write_include_vms(self):
        vms = VMS
        for distro in ['rpm', 'deb']:
            travis_path = 'R{release}/travis-vms-{distro}-r{release}.yml'.format(
                release=self.qubes_release, distro=distro)
            vms['import'].append(
                {
                    'source': 'QubesOS/qubes-continuous-integration:%s' % travis_path
                }
            )

        travis_path_all = 'R{release}/travis-vms-r{release}.yml'.format(
            release=self.qubes_release)
        self.write_yml(vms, travis_path_all)

    def write_vms(self, only_flavors=False):
        for distro in ['rpm', 'deb']:
            envs = ENVS
            envs['env'] = self.generate_vms(distro=distro, only_flavors=only_flavors)
            if envs['env']:
                if only_flavors:
                    travis_path = 'R{release}/travis-vms-{distro}-flavors-r{release}.yml'
                else:
                    travis_path = 'R{release}/travis-vms-{distro}-r{release}.yml'

                travis_path = travis_path.format(release=self.qubes_release, distro=distro)
                self.write_yml(envs, travis_path)

    def write_all(self):
        self.write_base()
        self.write_dom0()
        self.write_vms()
        self.write_vms(only_flavors=True)
        self.write_include_vms()


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
