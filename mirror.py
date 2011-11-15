import os
import sys
import glob
import shutil
import thread
import zipfile 
import tempfile
import html5lib
import subprocess

from urlparse import urljoin
from urlparse import urlparse

from pyquery import PyQuery as pq

# -------------------------------

WGET_CMD = '/opt/local/bin/wget'

# -------------------------------

def main(url_or_path, out_dir="/tmp/mirror", zip_archive=True, process_links=True, archive_index=False, port=7777):
	
	global WGET_CMD
	
	httpd = None
	try:
		result = False
		
		if not _is_valid_url(url_or_path):
			httpd = _launch_server(url_or_path, port)
			url = "http://localhost:%s" % port
		else:
			httpd = None
			url = url_or_path
			url = url[:-1] if url[-1] =='/' else url
	
		out_dir = _create_path(out_dir)
		
		if zip_archive:
			log_file = tempfile.mktemp()
			archive_dir = tmp_dir = _create_path(tempfile.mkdtemp())
		else:
			tmp_dir = None
			archive_dir = out_dir
			log_file = '%s/_out.log' % archive_dir
		
		_remove_file(log_file)
		WGET_CMD = "%s -a %s" % (WGET_CMD, log_file)
	
		result = _get_url_content(url, archive_dir) and _get_toc_file(url, archive_dir)	
		if result:
			toc_file = os.path.join(archive_dir, 'eclipse-toc.xml')
			_process_toc_file(url, archive_dir, process_links, toc_file)
			if archive_index:
				_get_index_dir(url, archive_dir)
			
		if zip_archive:
			zip_name = zip_archive if isinstance(zip_archive, basestring) else 'archive.zip'
			_zip_archive(archive_dir, out_dir, zip_name)
		
		return result
	finally:
		if httpd:
			httpd.shutdown()
			httpd.server_close()
			
		if result:
			if tmp_dir:
				shutil.rmtree(tmp_dir, ignore_errors=True)
			
			if zip_archive:
				lpath = os.path.join(out_dir, '_out.log')
				_remove_file(lpath)
				os.rename(log_file, lpath)
				

# -------------------------------

def _zip_archive(source_path, out_dir, zip_name="archive.zip"):

	out_file = os.path.join(out_dir, zip_name)
	
	print "Archiving '%s' to '%s'" % (source_path, zip_name)
	
	zip_file = zipfile.ZipFile(out_file, "w")
	try:
		_add_to_zip(zip_file, source_path, source_path)
	finally:
		zip_file.close()

def _add_to_zip(zip_file, path, source_path):
	if os.path.isfile(path):
		path = path[len(source_path) + 1:]
		zip_file.write(path, path, zipfile.ZIP_DEFLATED)
	elif os.path.isdir(path):
		for name in glob.glob("%s/*" % path):
			_add_to_zip(zip_file, name, source_path)
			
# -------------------------------

def _process_toc_file(url, out_dir, process_links, toc_file='eclipse-toc.xml'):
	
	print "Processing TOC content"
	
	e = pq(filename = toc_file)
	e('toc').map(lambda i,e: _process_node(e, url, out_dir, process_links))
	e('topic').map(lambda i,e: _process_node(e, url, out_dir, process_links))
	e('page').map(lambda i,e: _process_node(e, url, out_dir, process_links))
	
	return True
				
def _process_node(node, url, out_dir, process_links):
	result = True
	attributes = node.attrib
	for i, name  in enumerate (['href', 'qualifier', 'icon', 'thumbnail']):
		
		if i<=1 and not process_links:
			continue
		
		value =  attributes.get(name, None)
		if value:
			force_html = i <= 1 
			if i == 1 and attributes.get('type', None) != 'link':
				continue
			result = _handle_attribute(value, url, out_dir, force_html) and result
			
	return result

def _handle_attribute(target, url, out_dir, force_html=False):
	head, _ = os.path.split(target)
	out_dir = _create_path(os.path.join(out_dir, head))
	return _get_file(url, out_dir, target, force_html)
	
def _get_toc_file(url, out_dir, toc_file='eclipse-toc.xml'):
	print "Getting TOC file"
	return _get_file(url, out_dir, toc_file, True)

# -------------------------------
	
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
	finally:
		_remove_file(tmp)

# -------------------------------

def _launch_server(data_path, port = 7777):

	import SimpleHTTPServer
	import SocketServer

	if not os.path.exists(data_path):
		raise Exception("'%s' does not exists" % data_path)
	
	os.chdir(data_path)

	def ignore(self, *args, **kwargs):
		pass
		
	handler = SimpleHTTPServer.SimpleHTTPRequestHandler
	handler.log_error = ignore
	handler.log_message = ignore
	
	httpd = SocketServer.TCPServer(("", port), handler) 	
	def worker():
		httpd.serve_forever()
		
	thread.start_new_thread(worker, ())
	return httpd
	
# -------------------------------

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

def _get_cut_dirs(url):
	r = urlparse(url)
	s = r.path.split('/')
	return len(s) - 1

def _execute_cmd(args):
	cmd = ' '.join(args)
	retcode = subprocess.call(cmd, shell=True)
	if retcode != 0:
		raise Exception("Fail to execute '%s'" % cmd)
	
	return True

# -------------------------------

def _remove_file(target):
	try:
		os.remove(target)
	except:
		pass
	
def _create_path(path):
	path = os.path.expanduser(path)
	if not os.path.exists(path):
		os.makedirs(path)
	return path
			
def _is_valid_url(url_or_path):
	try:
		pr = urlparse(url_or_path)
		return pr.scheme == 'http' and pr.netloc
	except:
		return False

# -------------------------------

if __name__ == '__main__':
	args = sys.argv[1:]
	if args:
		url_or_path = args.pop(0)
		out_dir = args.pop(0) if args else "/tmp/mirror"
		zip_archive = args.pop(0) if args else False
		main(url_or_path, out_dir, zip_archive)
	else:
		print("Syntax URL_OR_PATH [output directory] [--disable-zip-archive]")
		print("python mirror.py http://localhost/prealgebra /tmp/prealgebra")
