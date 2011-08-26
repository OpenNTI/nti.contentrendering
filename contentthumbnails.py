#!/usr/bin/env python


import os
import re
import sys, shutil,pdb
from xml.dom.minidom import parse
from xml.dom.minidom import Node
import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from RenderedBook import RenderedBook
import tempfile
javascript = os.path.join(os.path.dirname(__file__),'../js/rasterize.js')
thumbnailsLocationName = 'thumbnails'

def replaceExtension(fname, newext):
	return '%s.%s' % (os.path.splitext(fname)[0], newext);

def _generatedImage(contentdir, page, output):
	#print 'Fetching page info for %s' % htmlFile
	process = "phantomjs %s %s %s 2>/dev/null" % (javascript, os.path.join(contentdir, page.location), output)
	#print process
	jsonStr = subprocess.Popen(process, shell=True, stdout=subprocess.PIPE).communicate()[0].strip()

	#shrink it down to size
	process = "convert %s -resize %d%% PNG32:%s" % (output, 25, output)
	#print process
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

	eclipseTOC = book.getEclipseTOC()

	htmlFiles = [x.filename for x in book.pages.values()]

	pageAndOutput = [(page, replaceExtension(page.filename, 'png')) for page in book.pages.values()]

	#generate a place to put the thumbnails
	thumbnails = os.path.join(book.contentLocation, thumbnailsLocationName);

	if not os.path.isdir(thumbnails):
		os.mkdir(thumbnails)

	cwd = os.getcwd()

	tempdir = tempfile.mkdtemp()

	results = None

	os.chdir(tempdir)

	with ProcessPoolExecutor() as executor:
		for ntiid, output in executor.map( _generatedImage,[cwd for x in pageAndOutput], [x[0] for x in pageAndOutput], [x[1] for x in pageAndOutput]):
			thumbnail = os.path.join(thumbnails, output)
			copy(os.path.join(tempdir, output), os.path.join(cwd, thumbnail))
			eclipseTOC.getPageNodeWithNTIID(ntiid).attributes['thumbnail']=thumbnail

	os.chdir(cwd)


	eclipseTOC.save()
	shutil.rmtree(tempdir)


