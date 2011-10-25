import os
import sys
import glob
import tempfile
import html5lib
import subprocess

from urlparse import urljoin
from urlparse import urlparse

from xml.dom.minidom import parse
from xml.dom.minidom import Node

WGET_CMD = 'wget'

def main(url, out_dir="/tmp/mirror"):
	""" 
	Main program routine 
	"""
	global WGET_CMD
	
	url = url[:-1] if url[-1] =='/' else url
	
	out_dir = os.path.expanduser(out_dir)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	
	log_file = '%s/_out.log' % out_dir
	_remove_file(log_file)
	
	WGET_CMD = "%s -a %s" % (WGET_CMD, log_file)

	result = _get_url_content(url, out_dir) and _get_toc_file(url, out_dir)	
	if result:
		toc_file = os.path.join(out_dir, 'eclipse-toc.xml')
		result = _process_toc_file(url, out_dir, toc_file)
		if result:
			_get_index_dir(url, out_dir)
		
	return result

def _remove_file(target):
	try:
		os.remove(target)
	except:
		pass
	
def _get_index_dir(url, out_dir):
	
	print "Getting [book]/index content"
	
	tmp = tempfile.mktemp(".html", "index", out_dir)
	try:
		url2 = urljoin(url + '/', 'indexdir')
		args = [WGET_CMD, '-O %s' % tmp, url2]
		_execute_cmd(args)	
	
		with open(tmp, "r") as source:
			doc = html5lib.parse(source, encoding="utf-8")
			for node in doc:
				if node.type == 5 and node.name == 'a':
					attributes = node.attributes
					href = attributes.get('href', None)
					if href and (href.startswith('_') or href.endswith('_WRITELOCK')):
						target = "indexdir/" + href
						_get_file(url, os.path.join(out_dir,"indexdir"), target, False)
		
	except Exception, e:
		print e
	finally:
		_remove_file(tmp)

def _process_toc_file(url, out_dir, toc_file='eclipse-toc.xml'):
	
	print "Processing TOC content"
	
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

def _handle_attribute(target, url, out_dir, force_html=False):
	
	head, _ = os.path.split(target)
	out_dir = os.path.join(out_dir, head)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)
	
	return _get_file(url, out_dir, target, force_html)
	
def _get_cut_dirs(url):
	r = urlparse(url)
	s = r.path.split('/')
	return len(s) - 1
	
def _get_file(url, out_dir, target, force_html=False):
	"""
	Return the specified target from the specified url
	"""
	args = [WGET_CMD, '-N', '-nH', '-P %s' % out_dir]
	if force_html:
		args.extend(['-p', '--force-html'])
		
	cut_dirs = _get_cut_dirs(url)
	if cut_dirs > 0:
		args.append('--cut-dirs=%s' % cut_dirs)
		
	url = urljoin(url + '/', target)
	args.append(url)
	_execute_cmd(args)
	
	target = os.path.split(target)[1]
	return os.path.exists(os.path.join(out_dir, target))

def _get_toc_file(url, out_dir, toc_file='eclipse-toc.xml'):
	print "Getting TOC file"
	return _get_file(url, out_dir, toc_file, True)
	
def _get_url_content(url, out_dir="/tmp"):	
	"""
	Get as much as possible content from the
	specified URL
	"""
	
	print "Getting URL content"
	
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
		out_dir = args.pop(0) if args else "/tmp/mirror"
		main(url, out_dir)
	else:
		print("Syntax URL [output directory]")
		print("python mirror.py http://localhost/prealgebra /tmp/prealgebra")
