#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import re
import socket
import shutil
import thread
import tempfile
import subprocess
from six.moves import urllib_parse

import SocketServer
import SimpleHTTPServer

from pyquery import PyQuery as pq

WGET_CMD = ['wget', '-q']

logger = __import__('logging').getLogger(__name__)


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("", 0))
        s.listen(1)
        return s.getsockname()[1]
    finally:
        s.close()


def get_cut_dirs(url):
    r = urllib_parse.urlparse(url)
    s = r.path.split('/')
    return len(s) - 1


def execute_command(args):
    cmd = ' '.join(args)
    retcode = subprocess.call(args, shell=False)
    if retcode != 0:
        raise Exception("Fail to execute '%s', return code %s"
                        % (cmd, retcode))
    return True


def remove_file(target):
    try:
        os.remove(target)
    except Exception:
        pass


def create_path(path):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def is_valid_url(url_or_path):
    try:
        pr = urllib_parse.urlparse(url_or_path)
        return pr.scheme == 'http' and pr.netloc
    except Exception:
        return False


def process_node(node, resources):
    attributes = node.attrib
    for i, name in enumerate(['href', 'qualifier', 'icon', 'thumbnail']):
        value = attributes.get(name, None)
        if value:
            if i <= 1 and not value.endswith(".html"):
                continue
            elif value not in resources:
                resources[value] = None


def get_file(url, out_dir, target, force_html=False):
    """
    Return the specified target from the specified url
    """
    args = []
    args.extend(WGET_CMD)
    args.extend(['-N', '-nH', '-P', out_dir])
    if force_html:
        args.extend(['-p', '--force-html'])

    cut_dirs = get_cut_dirs(url)
    if cut_dirs > 0:
        args.append('--cut-dirs=%s' % cut_dirs)

    url = urllib_parse.urljoin(url + '/', target)
    args.append(url)
    execute_command(args)

    target = os.path.split(target)[1]
    return os.path.exists(os.path.join(out_dir, target))


def get_toc_file(url, out_dir, toc_file='eclipse-toc.xml'):
    return get_file(url, out_dir, toc_file, True)


def process_toc_file(url, resources, toc_file='eclipse-toc.xml'):
    tmp = tempfile.mkdtemp()
    try:
        if get_toc_file(url, tmp, toc_file):
            e = pq(filename=os.path.join(tmp, toc_file))
            e('toc').map(lambda unused, e: process_node(e, resources))
            e('topic').map(lambda unused, e: process_node(e, resources))
            e('page').map(lambda unused, e: process_node(e, resources))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def launch_server(data_path, port=None):

    if not os.path.exists(data_path):
        raise Exception("'%s' does not exists" % data_path)

    os.chdir(data_path)

    def ignore(self, *args, **kwargs):
        pass

    port = port or get_open_port()
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    handler.log_error = ignore
    handler.log_message = ignore

    httpd = SocketServer.TCPServer(("", port), handler)

    def worker():
        httpd.serve_forever()

    thread.start_new_thread(worker, ())
    return httpd


def get_url_resources(url, unused_out_dir="/tmp", user_spider=False):
    tmp = None
    resources = {}

    args = []
    args.extend(WGET_CMD)
    args.extend(['-m', '-nH', '--no-parent', '-p'])
    cut_dirs = get_cut_dirs(url)
    if cut_dirs > 0:
        args.append('--cut-dirs=%s' % cut_dirs)

    if user_spider:
        args.append('--spider')
    else:
        tmp = tempfile.mkdtemp()
        args.append('-P')
        args.append(tmp)

    args.append(url)

    def valid_resource(rsr):
        rsr = rsr.rstrip() if rsr else None
        rsr = rsr[:-1] if rsr[-1] == '/' else rsr
        if rsr and '?' not in rsr and rsr != url and not rsr.endswith("robots.txt"):
            return rsr[len(url) + 1:] if rsr.startswith(url) else rsr
        else:
            return None

    try:
        logger.info('Fetching resources (%s)', args)
        result = subprocess.Popen(args,
                                  shell=False,
                                  stderr=subprocess.PIPE).communicate()
        source = result[1]  # stderr
        for line in source or ():
            m = re.search(r'(^--.*--)  (http:\/\/.*[^\/]$)', line)
            if m:
                rsr = valid_resource(m.group(2))
                if rsr and rsr not in resources:
                    resources[rsr] = None
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)

    return resources


def main(url_or_path, out_dir="/tmp/", manifest='cache-manifest', port=None):
    """
    Creates an html cache-manifest file with all resources in the specified url
    """
    httpd = None
    port = port or get_open_port()
    try:
        if not is_valid_url(url_or_path):
            httpd = launch_server(url_or_path, port)
            url = "http://localhost:%s" % port
        else:
            httpd = None
            url = url_or_path
            url = url[:-1] if url[-1] == '/' else url

        out_dir = create_path(out_dir)

        resources = get_url_resources(url, out_dir, httpd == None)
        process_toc_file(url, resources)

        path = os.path.join(out_dir, manifest)
        with open(path, "w") as target:
            target.write("CACHE MANIFEST\n")
            for value in sorted(resources.keys()):
                target.write("%s\n" % value)
        return path
    finally:
        if httpd:
            httpd.shutdown()
            httpd.server_close()
