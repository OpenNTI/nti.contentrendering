import os
import sys
import glob
import subprocess

from urlparse import urljoin
from urlparse import urlparse

from xml.dom.minidom import parse
from xml.dom.minidom import Node

WGET_CMD = '/opt/local/bin/wget'

def main(url, out_dir="/tmp"):
	""" 
	Main program routine 
	"""
	
	url = url[:-1] if url[-1] =='/' else url
	
	out_dir = os.path.expanduser(out_dir)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
		
	if _get_all_content(url, out_dir) and _get_toc_file(url, out_dir):
		pass
	
def _process_toc_file(url, out_dir, toc_file='eclipse-toc.xml'):
	dom = parse(toc_file)
	toc = dom.getElementsByTagName("toc");
	if toc and _process_node(toc[0], url, out_dir):
		pass
	
def _process_node(node, url, out_dir):
	return True
	
def _get_cut_dirs(url):
	r = urlparse(url)
	s = r.path.split('/')
	return len(s) - 1
	
def _get_file(url, out_dir, target):
	"""
	return the specified target from the specified url
	"""
	url = urljoin(url + '/', target)
	args = [WGET_CMD, '--force-html', '-nH', '-p', '-P %s' % out_dir]
	cut_dirs = _get_cut_dirs(url)
	if cut_dirs > 0:
		args.append('--cut-dirs=%s' % cut_dirs)
	args.append(url)
	
	cmd = ' '.join(args)
	retcode = subprocess.call(cmd, shell=True)
	if retcode != 0:
		raise Exception("Fail to execute '%s'" % cmd)
	
	return os.path.exists(os.path.join(out_dir, target))

def _get_toc_file(url, out_dir, toc_file='eclipse-toc.xml'):
	return _get_file(url, out_dir, toc_file)
	
def _get_all_content(url, out_dir="/tmp"):	
	"""
	Get as much as possible content from the
	specified URL
	"""
	
	# -m   --mirror
	# -nH  no-host-directories
	# --no-parent do not ever ascend to the parent directory when retrieving recursively
	# --cut-dirs=number Ignore number directory components
	# -P output directory
	
	args = [WGET_CMD, '-m', '-nH', '--no-parent', '-p']
	
	cut_dirs = _get_cut_dirs(url)
	if cut_dirs > 0:
		args.append('--cut-dirs=%s' % cut_dirs)
	args.append('-P %s' % out_dir)
	args.append(url)
	
	cmd = ' '.join(args)
	retcode = subprocess.call(cmd, shell=True)
	if retcode != 0:
		raise Exception("Fail to execute '%s'" % cmd)
	
	return glob.glob(out_dir + "*.html") > 0

if __name__ == '__main__':
	args = sys.argv[1:]
	if args:
		url = args.pop(0)
		out_dir = args.pop(0) if args else "/tmp"
		main(url, out_dir)
	else:
		print("syntax URL [output directory]")
