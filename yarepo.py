#!/usr/bin/env python3
# Usage: ./yarepo.py <manifest repo> <manifest branch>
# i.e.: ./yarepo.py https://android.googlesource.com/platform/manifest master

from xml.etree import ElementTree
import sys, shlex, subprocess

# git manifest stuffs
manifest_clone = 'git clone --branch ' + sys.argv[2] + ' ' + sys.argv[1] + ' manifest'

subprocess.call(shlex.split(manifest_clone), stdout=subprocess.PIPE)

tree = ElementTree.parse('manifest/default.xml')
root = tree.getroot()

for child in root:
    if child.tag == 'remote':
        git_base = child.get('fetch')
    if child.tag == 'project':
        revision = child.get('revision')

        if revision is None:
            revision = root.find('default').get('revision')

        subprocess.call(shlex.split('git clone --branch ' + revision + ' ' + git_base + '/' + child.get('name')), stdout=subprocess.PIPE)
