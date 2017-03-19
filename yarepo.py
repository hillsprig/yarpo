#!/usr/bin/env python3

from xml.etree import ElementTree
import sys, shlex, subprocess, argparse
from collections import namedtuple

parser = argparse.ArgumentParser(description='Light-weight google repo alternative.')

parser.add_argument('--init', action='store_true', help='clones all git repositories according to manifest')
parser.add_argument('-u', '--url', type=str, dest='url', help='url to manifest repository.')
parser.add_argument('-b', '--branch', type=str, dest='branch', help='desired branch of the manifest repository')
parser.add_argument('--status', action='store_true', help='shows git status of all repositories')
parser.add_argument('--sync', action='store_true', help='updates all repositories that can be fast-forwarded')
parser.add_argument('--forall', nargs='+', help='executes the given command for all repositories')
parser.add_argument('--manifest', action='store_true', help='generates a manifest from the current HEADs')

args = parser.parse_args()

Remote = namedtuple('Remote', ['name', 'fetch', 'pushurl', 'revision'])
Default = namedtuple('Default', ['remote', 'revision'])
Project = namedtuple('Project', ['name', 'path', 'remote', 'revision'])

m_remote = Remote('', '', '', '')
m_default = Default('', '')
m_projects = []

def parse_manifest():
    tree = ElementTree.parse('.manifest/default.xml')
    root = tree.getroot()

    global m_remote
    global m_default
    global m_projects

    for child in root:
        if child.tag == 'remote':
            m_remote = Remote(name=child.get('name'), fetch=child.get('fetch'), pushurl=child.get('pushurl'), revision=child.get('revision'))
        if child.tag == 'default':
            m_default = Default(remote=child.get('remote'), revision=child.get('revision'))
        if child.tag == 'project':
            m_projects.append(Project(name=child.get('name'), path=child.get('path'), remote=child.get('remote'), revision=child.get('revision')))

if args.init and args.url:
    branch = '--branch ' + args.branch + ' ' if args.branch else ''
    manifest_clone_cmd = 'git clone ' + branch + args.url + ' .manifest'

    subprocess.call(shlex.split(manifest_clone_cmd), stdout=subprocess.PIPE)

    parse_manifest()

    for project in m_projects:
        branch = '--branch ' + (project.revision if project.revision else m_default.revision) + ' ' if project.revision or m_default.revision else ''

        # Replace with more readable regex
        remote = args.url[:[index for index, char in enumerate(args.url) if char == '/'][2]] + '/' + project.name

        path = project.path if project.path else ''
        clone_cmd = 'git clone ' + branch + remote + ' ' + path 
        subprocess.call(shlex.split(clone_cmd), stdout=subprocess.PIPE)

    sys.exit(0)

if args.status:
    pass

if args.sync:
    pass

if args.forall:
    pass

if args.manifest:
    pass

