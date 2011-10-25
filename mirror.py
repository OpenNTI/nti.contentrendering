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
		toc_file = os.path.join(out_dir, 'eclipse-toc.xml')
		_process_toc_file(url, out_dir, toc_file)
	
def _process_toc_file(url, out_dir, toc_file='eclipse-toc.xml'):
	result = True
	dom = parse(toc_file)
	toc = dom.getElementsByTagName("toc");
	if toc and _process_node(toc[0], url, out_dir):
		for node in toc[0].childNodes:
			if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
				result = _process_topic(node,  url, out_dir) and result
	else:
		result = False
		
	return result

def _process_topic(topic, url, out_dir):
	result = _process_node(topic, url, out_dir)
	if result:
		for node in topic.childNodes:
			if node.nodeType == Node.ELEMENT_NODE:
				if node.localName == 'topic':
					result = _process_topic(node,  url, out_dir) and result
				elif node.localName == 'Related':
					for c in node.childNodes:
						if c.nodeType == Node.ELEMENT_NODE and c.localName == 'page':
							result = _process_node(c,  url, out_dir) and result
	return result
				
def _process_node(node, url, out_dir):
	result = True
	attributes = node.attributes
	for i, name  in enumerate (['href', 'qualifier', 'icon', 'thumbnail']):
		av =  attributes.get(name, None)
		if av and av.value:
			if i <= 1 and not av.value.endswith(".html"):
				continue
			result = _handle_attribute(av.value, url, out_dir, i<=1) and result
	return result

def _handle_attribute(attr, url, out_dir, force_html=False):
	
	target = os.path.join(out_dir, attr)
	if os.path.exists(target):
		return True

	head, _ = os.path.split(attr)
	out_dir = os.path.join(out_dir, head)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	
	args = [WGET_CMD, '-N', '-nH', '-P %s' % out_dir]
	if force_html:
		args.extend(['-p', '--force-html'])
		
	cut_dirs = _get_cut_dirs(url)
	if cut_dirs > 0:
		args.append('--cut-dirs=%s' % cut_dirs)
		
	url = urljoin(url + '/', attr)
	args.append(url)
	_execute_cmd(args)
	
	return os.path.exists(target)
	
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
	
	_execute_cmd(args)
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
	
	_execute_cmd(args)
	return glob.glob(out_dir + "*.html") > 0

def _execute_cmd(args):
	cmd = ' '.join(args)
	retcode = subprocess.call(cmd, shell=True)
	if retcode != 0:
		raise Exception("Fail to execute '%s'" % cmd)
	
	return True
if __name__ == '__main__':
	args = sys.argv[1:]
	if args:
		url = args.pop(0)
		out_dir = args.pop(0) if args else "/tmp"
		main(url, out_dir)
	else:
		print("syntax URL [output directory]")
