#!/usr/bin/env python

import argparse
import lbdist

parser = argparse.ArgumentParser(description='a uname like program to query distribution information')
parser.add_argument('--os-release', dest='osrelease',
                    help='Path to the os-release file', default='/etc/os-release')
parser.add_argument('--linbit-reponame', '-l', action='store_true', dest='lbrepo',
                    help='Query the LINBIT internal distribution name/repo name')
parser.add_argument('--name', '-n', action='store_true', dest='name',
                    help='Query the distribution name')
parser.add_argument('--dist-version', action='store_true', dest='distversion',
                    help='Query the distribution version')
parser.add_argument('--family', '-f', action='store_true', dest='family',
                    help='Query the distribution family')
parser.add_argument('--all', '-a', action='store_true', dest='all',
                    help='Query all information')
parser.add_argument('--format', choices=('csv', 'space'), default='csv',
                    help='Output format')

args = parser.parse_args()

if args.lbrepo:
    print(lbdist.LinbitDistribution(args.osrelease).repo_name)
elif args.name:
    print(lbdist.LinbitDistribution(args.osrelease).name)
elif args.distversion:
    print(lbdist.LinbitDistribution(args.osrelease).version)
elif args.family:
    print(lbdist.LinbitDistribution(args.osrelease).family)
elif args.all:
    d = lbdist.LinbitDistribution(args.osrelease)
    v = [d.repo_name, d.name, d.version, d.family]
    out = ''
    if args.format == 'csv':
        out = ','.join(v)
    elif args.format == 'space':
        out = ' '.join(v)
    print(out)
