#!/usr/bin/env python3

from xml.etree import ElementTree
import sys, shlex, subprocess, argparse, os
from collections import namedtuple
from urllib.parse import urlsplit, urlunsplit
from pathlib import PurePath

parser = argparse.ArgumentParser(description='Light-weight google repo alternative.')

parser.add_argument('--init', action='store_true', help='clones all git repositories according to manifest')
parser.add_argument('-u', '--url', type=str, dest='url', help='url to manifest repository.')
parser.add_argument('-b', '--branch', type=str, dest='branch', help='desired branch of the manifest repository')
parser.add_argument('--status', action='store_true', help='shows git status of all repositories')
parser.add_argument('--sync', action='store_true', help='updates all repositories that can be fast-forwarded')
parser.add_argument('--forall', nargs='+', help='executes the given command for all repositories')
parser.add_argument('--manifest', action='store_true', help='generates a manifest from the current HEADs')
parser.add_argument('-r', '--reset', action='store_true', dest='reset', help='reset branch to the one in the manifest repository, usable with sync')

args = parser.parse_args()

Remote = namedtuple('Remote', ['name', 'fetch', 'pushurl', 'revision'])
Default = namedtuple('Default', ['remote', 'revision'])
Project = namedtuple('Project', ['name', 'path', 'remote', 'revision'])

m_remote = Remote('', '', '', '')
m_default = Default('', '')
m_projects = []

manifest_root = ''

def parse_manifest():
    global manifest_root

    manifest_search_path = PurePath(os.getcwd())

    while not os.path.exists(str(manifest_search_path) + '/.manifest'):
        manifest_search_path = PurePath(manifest_search_path.parent)

    manifest_root = str(manifest_search_path)

    tree = ElementTree.parse(manifest_root + '/.manifest/default.xml')
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

def get_remote(url):
    if url:
        raw_remote = url
    ## remote.fetch = '..' denotes that the cmd args url should be used
    elif m_remote.fetch and m_remote.fetch != '..':
        raw_remote = m_remote.fetch
    else:
        if args.url:
            raw_remote = args.url
        else:
            sys.exit(1)

    remote_split = urlsplit(raw_remote)
    remote = urlunsplit((remote_split.scheme, remote_split.netloc, '', '', ''))

    return remote

def git_cmd_get(path, cmd):
    global manifest_root
    cmds = ['git', '-C', manifest_root + '/' + path]
    cmds.extend(shlex.split(cmd))
    process = subprocess.Popen(cmds, stdout=subprocess.PIPE)
    out, err = process.communicate()
    return out.decode('utf-8').rstrip()

def git_cmd(path, cmd):
    global mainfest_root
    cmds = ['git', '-C', manifest_root + '/' + path]
    cmds.extend(shlex.split(cmd))
    print(' '.join(cmds))
    subprocess.call(cmds)

def get_revision(project):
    global m_default
    revision = 'master'
    if project.revision:
        revision = project.revision
    elif m_default.revision:
        revision = m_default.revision
    return revision

# init
if args.init and args.url:
    branch = '--branch ' + args.branch + ' ' if args.branch else ''
    manifest_clone_cmd = 'git clone ' + branch + args.url + ' .manifest'

    subprocess.call(shlex.split(manifest_clone_cmd))

    parse_manifest()

    default_remote = get_remote(None)

    for project in m_projects:

        if project.remote:
            remote = get_remote(project.remote)
        else:
            remote = default_remote

        remote = remote + '/' + project.name + ' '

        path = project.path if project.path else os.path.basename(project.name)
        git_prefix = 'git -C ' + path + ' '

        # the reason for command list is to more reliably handle revisions regardless of type commit id, tag or branch
        cmd_list = ['mkdir -p ' + path]
        cmd_list.append(git_prefix + 'init')
        cmd_list.append(git_prefix + 'remote add origin ' + remote)
        cmd_list.append(git_prefix + 'fetch --all')
        cmd_list.append(git_prefix + 'checkout ' + get_revision(project))

        for cmd in cmd_list:
            subprocess.call(shlex.split(cmd))

    sys.exit(0)


# status
if args.status:
    parse_manifest()

    print('project .manifest')
    git_cmd('.manifest', 'status --short -b')
    print('')

    for project in m_projects:
        print('project ' + project.name)
        path = project.path if project.path else os.path.basename(project.name)
        git_cmd(path, ' status --short -b')
        print('')

    sys.exit(0)

# sync
if args.sync:
    parse_manifest()

    for project in m_projects:
        print('project ' + project.name)
        path = project.path if project.path else os.path.basename(project.name)
        if args.reset:
            remote = get_remote(project.remote) + '/' + project.name
            cur_remote = git_cmd_get(path, 'remote get-url origin')
            if remote != cur_remote:
                git_cmd(path, 'remote set-url origin ' + remote)
                git_cmd(path, 'fetch --all')
                git_cmd(path, 'checkout ' + get_revision(project))
        git_cmd(path, 'pull --ff-only')
        print('')

    sys.exit(0)

# forall
if args.forall:
    parse_manifest()

    for project in m_projects:
        print('project ' + project.name)
        path = project.path if project.path else os.path.basename(project.name)
        git_cmd(path, ' '.join(args.forall))
        print('')

    sys.exit(0)

# manifest
if args.manifest:
    parse_manifest()

    print("Not yet implemented.")

    sys.exit(0)
