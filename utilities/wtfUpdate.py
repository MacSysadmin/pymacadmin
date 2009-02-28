#!/usr/bin/env python
# encoding: utf-8
"""
Generate HTML documentation from an Apple .pkg update

Given a .pkg file this program will generate a list of the installed files,
installer scripts.

Contributed by Chris Barker (chrisb@sneezingdog.com):

    <http://sneezingdog.com/wtfupdate/wtfUpdate.py>
    <http://angrydome.org/?p=18>
"""

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import os
import sys
import shutil
import tempfile
import hashlib
from BeautifulSoup import BeautifulSoup, Tag, NavigableString
from os.path import basename, splitext, exists, join, isfile, isdir

# This will contain a BeautifulSoup object so we can avoid passing it around
# to every function:
SOUP = None

def expand_pkg(pkg_file):
    """ Expand the provided .pkg file and return the temp directory path """

    # n.b. This is a potential security issue but there's not really a good
    # way to avoid it because pkgutil can't handle an existing directory:
    dest = tempfile.mktemp()
    subprocess.check_call(["/usr/sbin/pkgutil", "--expand", pkg_file, dest])
    return dest


def get_description(pkg):
    """Return the HTML description """

    su_desc = pkg + '/Resources/English.lproj/SUDescription.html'

    if not exists(su_desc):
        return "<i>no description</i>"

    soup = BeautifulSoup(open(su_desc).read())
    return soup.body.contents


def load_scripts(pkg):
    """
    Given a package expand ul#scripts to include the contents of any scripts
    """

    script_ul = SOUP.find("ul", {"id": "scripts"})
    script_ul.contents = []

    for f in os.listdir(pkg):
        if splitext(f)[1] != '.pkg':
            continue

        script_dir  = join(pkg, f, 'Scripts')
        script_list = Tag(SOUP, 'ul')

        for script in os.listdir(script_dir):
            if script == "Tools":
                continue

            script_li          = Tag(SOUP, 'li')
            script_li['class'] = 'code'
            script_path        = join(script_dir, script)

            if isfile(script_path):
                script_li.append(join(f, 'Scripts', script))
                script_li.append(anchor_for_name(script_path))
                script_pre = Tag(SOUP, 'pre')
                script_pre.append(NavigableString(open(script_path).read()))
                script_li.append(script_pre)
            elif isdir(script_path):
                subscript_files = os.listdir(script_path)
                if not subscript_files:
                    continue

                script_li.append("%s Scripts" % join(f, 'Scripts', script))
                subscripts = Tag(SOUP, 'ul')

                for subscript in subscript_files:
                    subscript_path = join(script_path, subscript)
                    subscript_li = Tag(SOUP, 'li')
                    subscript_li.append(subscript)
                    subscript_li.append(anchor_for_name(subscript_path))

                    subscript_pre = Tag(SOUP, 'pre')
                    subscript_pre.append(NavigableString(open(subscript_path).read()))
                    subscript_li.append(subscript_pre)

                    subscripts.append(subscript_li)

                script_li.append(subscripts)

            script_list.append(script_li)

        if script_list.contents:
            new_scripts = Tag(SOUP, 'li')
            new_scripts.append(NavigableString("%s Scripts" % f))
            new_scripts.append(script_list)
            script_ul.append(new_scripts)

def get_file_list(pkg, sub_package):
    """
    Expand the ul#files list in the template with a listing of the files
    contained in the sub package's BOM
    """

    file_ul = SOUP.find("ul", {'id': 'files'})
    if not file_ul:
        raise RuntimeError("""Template doesn't appear to have a <ul id="files">!""")

    if not "cleaned" in file_ul.get("class", ""):
        file_ul.contents = [] # Remove any template content

    for k, v in get_bom_contents(pkg + '/' + sub_package + '/Bom').items():
        file_ul.append(get_list_for_key(k, v))

def get_list_for_key(name, children):
    """
    Takes a key and a dictionary containing its children and recursively
    generates HTML lists items. Each item will contain the name and, if it has
    children, an unordered list containing those child items.
    """

    li = Tag(SOUP, "li")
    li.append(NavigableString(name))

    if children:
        ul = Tag(SOUP, "ul")
        for k, v in children.items():
            ul.append(get_list_for_key(k, v))
        li.append(ul)

    return li


def get_bom_contents(bom_file):
    """
    Run lsbom on the provided file and return a nested dict representing
    the file structure
    """

    lsbom = subprocess.Popen(
        ["/usr/bin/lsbom", bom_file], stdout=subprocess.PIPE
    ).communicate()[0]

    file_list = filter(None,
        [ l.split("\t")[0].lstrip("./") for l in lsbom.split("\n") ]
    )
    file_list.sort(key=str.lower)

    contents = dict()

    for f in file_list:
        contents = merge_list(contents, f.split('/'))

    return contents


def merge_list(master_dict, parts):
    """Given a dict and a list of elements, recursively create sub-dicts to represent each "row" """
    if parts:
        head = parts.pop(0)
        master_dict[head] = merge_list(master_dict.setdefault(head, dict()), parts)

    return master_dict

def anchor_for_name(*args):
    file_name = join(*args)
    digest    = hashlib.md5(file_name).hexdigest()
    return Tag(SOUP, "a", [("name", digest)])

def generate_package_report(pkg):
    """Given an expanded package, create an HTML listing of the contents"""

    SOUP.find('div', {'id': 'description'}).contents = get_description(pkg)

    load_scripts(pkg)

    if exists(pkg + "/Bom"):
        get_file_list(pkg, "")

    for f in os.listdir(pkg):
        if splitext(f)[1] == '.pkg':
            get_file_list(pkg, f)


def main(pkg_file_name, html_file_name):
    global SOUP

    print "Generating %s from %s" % (html_file_name, pkg_file_name)

    pkg  = expand_pkg(pkg_file_name)
    SOUP = BeautifulSoup(open("wtfUpdate.html").read())

    SOUP.find('title').contents = [
        NavigableString("wtfUpdate: %s" % basename(pkg_file_name))
    ]

    try:
        generate_package_report(pkg)
        html_file = open(html_file_name, 'w')
        html_file.write(str(SOUP))
        html_file.close()
    except RuntimeError, exc:
        print >> sys.stderr, "ERROR: %s" % exc
        sys.exit(1)
    finally:
        shutil.rmtree(pkg)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >> sys.stderr, 'Usage: %s file.pkg [output_file.html]' % sys.argv[0]
        sys.exit(1)

    if len(sys.argv) < 3:
        sys.argv.append("%s.html" % splitext(basename(sys.argv[1]))[0])

    main(*sys.argv[1:3])
