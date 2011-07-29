#!/usr/bin/env python


import os
import re
import sys
from xml.dom.minidom import parse
from xml.dom.minidom import Node
import subprocess
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

tocFileName='eclipse-toc.xml'

javascript = os.path.join('%s'%(os.path.dirname(__file__)),'getContentSize.js')

contentSizeName = 'NTIRelativeScrollHeight'

def main(args):
	""" Main program routine """

	if not len(args)>0:
		print "Usage: contentsizesetter.py path/to/content"
		sys.exit()

	transform(args.pop(0))

def transform(contentLocation):
	"""
	Use the toc file to find all the pages in the contentLocation.
	Use phantomjs and js to render the page and extract the content size.
	Stuff the contentsize in the page as a meta tag and add it to toc
	"""
	tocFile = os.path.join(contentLocation, tocFileName)

	print 'Using %s' % tocFile

	tocDOM = parse(tocFile)

	#Build a list of files we need to do
	rootTOC = tocDOM.getElementsByTagName('toc')[0]

	htmlFiles = []
	findHTMLInTOC(rootTOC, htmlFiles);

	htmlFiles = [os.path.join(contentLocation, f) for f in htmlFiles]

	print 'Finding content size for %s' % htmlFiles

	contentSizes = {}

	#Generate sizes for all our pages
	with ProcessPoolExecutor() as executor:
			for the_tuple in executor.map( getContentSize, htmlFiles):
				contentSizes[the_tuple[0]]=(the_tuple[1], the_tuple[2])

	print 'Storing generated content sizes'
	storeContentSizes(contentSizes, rootTOC, contentLocation)


	f = open(tocFile, 'w')
	rootTOC.writexml(f)
	f.close()

	return contentSizes

def storeContentSizes(contentSizes, node, contentLocation):

	htmlFile = os.path.join(contentLocation, node.getAttribute('href'))
	contentWidth = contentSizes[htmlFile][0]

	writeContentSizeToMeta(htmlFile, contentWidth)
	node.attributes[contentSizeName]=str(contentWidth)

	for child in node.childNodes:
		if getattr(child, 'hasAttributes', None) and child.hasAttribute('href'):
			storeContentSizes(contentSizes,child, contentLocation);





def writeContentSizeToMeta(htmlFile, contentWidth):
	if htmlFile.startswith('./'):
		htmlFile = htmlFile[2:]

	command = 'sed -i .bkp \
					  \"s/\\(<meta name=\\"NTIRelativeScrollHeight\\" content=\\"\\).*\\(\\" \\/>\\)/\\1%s\\2/\" %s' % (contentWidth,htmlFile)

	#print command

	subprocess.Popen(command, shell=True)

	backupFile = htmlFile+'.bkp'

	if os.path.exists(backupFile):
		os.remove(htmlFile+'.bkp')

def getContentSize(htmlFile):
	height, width = subprocess.Popen( "phantomjs %s %s 2>/dev/null" % (javascript, htmlFile), shell=True, stdout=subprocess.PIPE).communicate()[0].strip().split()
	return (htmlFile, int(height), int(width))

def findHTMLInTOC(toc, files):
	if toc.hasAttribute('href'):
		files.append(toc.getAttribute('href'))

	for node in toc.getElementsByTagName('topic'):
		findHTMLInTOC(node, files);

if __name__ == '__main__':
	main(sys.argv[1:])
