import re
import os
import sys
import shutil
import tempfile
import subprocess

from urlparse import urljoin
from urlparse import urlparse

from xml.dom.minidom import parse
from xml.dom.minidom import Node

WGET_CMD = 'wget'

def main(url, manifest='cache-manifest', out_dir="/tmp/"):
	""" 
	Creates an html cache-manifest file with all resources in the specified url
	"""
	
	url = url[:-1] if url[-1] =='/' else url
	
	out_dir = os.path.expanduser(out_dir)
	if not os.path.exists(out_dir):
		os.makedirs(out_dir)

	resources = _get_url_resources(url, out_dir) 
	_process_toc_file(url, resources)
		
	print "%s Resources found" % len(resources)
	
	path = os.path.join(out_dir, manifest)
	with open(path,"w") as target:
		target.write("CACHE MANIFEST\n")
		for value in sorted(resources.keys()):
			target.write("%s\n" % value)
	
def _process_toc_file(url, resources, toc_file='eclipse-toc.xml'):
	
	print "Processing TOC file"
	
	tmp = tempfile.mkdtemp()
	try:
		if _get_toc_file(url, tmp):			
			dom = parse(os.path.join(tmp, toc_file))
			toc = dom.getElementsByTagName("toc")
			if toc:
				_process_node(toc[0], resources)
	finally:
		shutil.rmtree(tmp, ignore_errors=True)
	
def _process_node(node, resources):
	
	attributes = node.attributes if node.attributes else {}
	for i, name  in enumerate ( ['href', 'qualifier', 'icon', 'thumbnail']):
		av =  attributes.get(name, None)
		if av and av.value:
			if i<=1 and not av.value.endswith(".html"):
				continue
			elif av.value not in resources:
				resources[av.value] = None
		
	for child in node.childNodes:
		if child.nodeType == Node.ELEMENT_NODE:
			_process_node(child,  resources)
	
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
	
def _get_url_resources(url, out_dir="/tmp"):	
	
	print "Getting URL resources"
	
	resources = {}
	
	args = [WGET_CMD, '-r', '-np', '-p', '-nH'] 
	cut_dirs = _get_cut_dirs(url)
	if cut_dirs > 0:
		args.append('--cut-dirs=%s' % cut_dirs)
	args.append('--spider')
	args.append(url)
	
	def valid_resource(rsr):
		rsr = rsr.rstrip() if rsr else None
		rsr = rsr[:-1] if rsr[-1] =='/' else rsr
		if rsr and '?' not in rsr and rsr != url and not rsr.endswith("robots.txt"):
			return rsr[len(url) + 1:] if rsr.startswith(url) else rsr
		else:
			return None
		
	with subprocess.Popen(args, shell=False, stderr=subprocess.PIPE).stderr as source:
		for line in source:
			m = re.search('(^--.*--)  (http:\/\/.*[^\/]$)', line)
			if m:
				rsr = valid_resource(m.group(2))
				if rsr and rsr not in resources:
					resources[rsr] = None
					
	return resources

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
		out_dir = args.pop(0) if args else "/tmp/"
		main(url, out_dir)
	else:
		print("Syntax URL [output directory]")
		print("python mirror.py http://localhost/prealgebra /tmp/")
