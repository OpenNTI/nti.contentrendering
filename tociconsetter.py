#!/usr/bin/env python

import sys
import os
import tempfile
from xml.dom.minidom import parse
from xml.dom.minidom import Node

buffer_size = 100

def main(args):
	""" Main program routine """

	tocFile = args.pop(0)
	chapterPath = None
	if (args):
		chapterPath = args.pop();
		
	transform(tocFile, chapterPath)

def transform(tocFile, chapterPath=None):
	dom = parse(tocFile)
	toc = dom.getElementsByTagName("toc");
	if toc and handleToc(toc[0], chapterPath):
		tempfile = toXml(dom)
		os.remove(tocFile)
		os.rename(tempfile, tocFile)
		
def handleToc(toc, chapterPath):
	current = 0
	
	attributes = toc.attributes
	attributes['href'] = "index.html"
	attributes['icon'] = "icons/chapters/PreAlgebra-cov-icon.png" 
	attributes['label'] = "Prealgebra" 
	
	for node in toc.childNodes:
		if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
			current += 1
			handleTopic(node, current, chapterPath)
			
	return True;

	
def handleTopic(topic, current, chapterPath):
	attributes = topic.attributes
	result = False
	if isChapter(attributes):
		imageName = 'C' + str(current) + '.png' 
		if not hasIcon(attributes):
			attributes['icon'] = 'icons/chapters/' + imageName
			result = True
			
		if chapterPath:
			chapterFile = getChapterFileName(attributes)
			if chapterFile:
				sourceFile = chapterPath + '/' + chapterFile.value
				setBackgroundImage(sourceFile, imageName)
				
	return result
		
def getChapterFileName(attributes):
	return (attributes and attributes.get('href'))

def hasIcon(attributes):
	return (attributes and attributes.get('icon'))

def isChapter(attributes):
	if attributes:
		label = attributes.get('label',None)
		return (label and label.value !='Index')
	return False
		
def toXml( document ):	
	outfile = '%s/temp-toc-file.%s.xml' % (tempfile.gettempdir(), os.getpid())
	with open(outfile,"w") as f:
		document.writexml(f)		
	return outfile;
		
def setBackgroundImage(sourceFile, imageName):
	
	if not os.path.exists(sourceFile) or not os.access(sourceFile, os.O_RDWR):
		return False
	
	replace = r"<body style=\"background: url('images\/chapters\/" + imageName + r"') no-repeat\">"
	command = "sed -i .bkp \"s/<body.*>/" + replace + "/g\" ";
	
	os.popen(command + sourceFile)
	os.remove(sourceFile + ".bkp")
	
	return True;

if __name__ == '__main__':	
	args = sys.argv[1:]
	if args:
		main(args)
	else:
		print("Specify a toc file [chapter path]")

