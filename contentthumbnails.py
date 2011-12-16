#!/usr/bin/env python2.7

import os
import shutil

import subprocess
# This process is all about external processes so threads
# are fine to extract max concurrency
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import tempfile
import warnings

javascript = os.path.join(os.path.dirname(__file__), 'js', 'rasterize.js')
if not os.path.exists(javascript): raise Exception( "Unable to load %s" % javascript )
thumbnailsLocationName = 'thumbnails'


warnings.warn( "Using phantomjs and convert from the PATH" )
def _generateImage(contentdir, page, output):
	#print 'Fetching page info for %s' % htmlFile
	process = "phantomjs %s %s %s 2>/dev/null" % (javascript, os.path.join(contentdir, page.location), output)
	#print process
	subprocess.Popen(process, shell=True, stdout=subprocess.PIPE).communicate()[0].strip()

	#shrink it down to size
	process = "convert %s -resize %d%% PNG32:%s" % (output, 25, output)
	subprocess.Popen(process, shell=True, stdout=subprocess.PIPE).communicate()[0].strip()

	return (page.ntiid, output)

def copy(source, dest, debug=True):
	if not os.path.exists(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest))
	try:
		shutil.copy2(source, dest)
	except OSError:
		shutil.copy(source, dest)

def transform(book):
	"""
	Generate thumbnails for all pages and stuff them in the toc
	"""

	eclipseTOC = book.toc

	def replaceExtension(fname, newext):
		return '%s.%s' % (os.path.splitext(fname)[0], newext)
	pageAndOutput = [(page, replaceExtension(page.filename, 'png')) for page in book.pages.values()]

	#generate a place to put the thumbnails
	thumbnails = os.path.join(book.contentLocation, thumbnailsLocationName)

	if not os.path.isdir(thumbnails):
		os.mkdir(thumbnails)

	cwd = os.getcwd()

	tempdir = tempfile.mkdtemp()

	os.chdir(tempdir)

	with ThreadPoolExecutor(multiprocessing.cpu_count()) as executor:
		for ntiid, output in executor.map( _generateImage,
										   [cwd for x in pageAndOutput],
										   [x[0] for x in pageAndOutput],
										   [x[1] for x in pageAndOutput]):
			thumbnail = os.path.join(thumbnails, output)
			copy(os.path.join(tempdir, output), os.path.join(cwd, thumbnail))
			eclipseTOC.getPageNodeWithNTIID(ntiid).attributes['thumbnail'] = os.path.relpath(thumbnail, start=book.contentLocation)

	os.chdir(cwd)


	eclipseTOC.save()
	shutil.rmtree(tempdir)


