#!/usr/bin/env python


import os
import re
import sys
import tempfile
from xml.dom.minidom import parse
from xml.dom.minidom import Node

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
	
	ntiid_pattern = re.compile("<meta.*content=\"(.*)\".*name=\"NTIID\"")
	
	attributes = toc.attributes
	attributes['href'] = "index.html"
	attributes['icon'] = "icons/chapters/PreAlgebra-cov-icon.png" 
	attributes['label'] = "Prealgebra" 
	
	if chapterPath:
		sourceFile = chapterPath + '/index.html'
		ntiid = getNTIID(sourceFile, ntiid_pattern)
		if ntiid:
			attributes["ntiid"]= ntiid
			
	for node in toc.childNodes:
		if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
			current += 1
			handleTopic(node, current, chapterPath, ntiid_pattern)
			
	return True;

	
def handleTopic(topic, current, chapterPath, ntiid_pattern):
	
	modified = False
	attributes = topic.attributes

	if isChapter(attributes):
		
		imageName = 'C' + str(current) + '.png' 
		if not hasIcon(attributes):
			attributes['icon'] = 'icons/chapters/' + imageName
			modified = True
			
		if chapterPath:
			
			chapterFile = getChapterFileName(attributes)
			if chapterFile:
				
				sourceFile = chapterPath + '/' + chapterFile.value
				
				# set the body background image
				setBackgroundImage(sourceFile, imageName)
				
				# set the ntiid for the chapter
				ntiid = getNTIID(sourceFile, ntiid_pattern)
				if ntiid:
					attributes["ntiid"]= ntiid
					modified = True
				
			# modify the sub-topics
			modified = handleSubTopics(topic, chapterPath, ntiid_pattern) or modified
			
	return modified
		
def handleSubTopics(topic, chapterPath, ntiid_pattern):
	"""
	Set the NTIID for all sub topics
	"""
	
	modified = False
	
	for node in topic.childNodes:
		if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
			modified = setNTIID(node, chapterPath, ntiid_pattern) or modified
			
	return modified
	
def setNTIID(topic, chapterPath, ntiid_pattern):
	"""
	Set the NTIID for the specifed topic
	"""
	
	modified = False
	attributes = topic.attributes
	chapterFile = getChapterFileName(attributes)
	if chapterFile:
		sourceFile = chapterPath + '/' + chapterFile.value
		ntiid = getNTIID(sourceFile, ntiid_pattern)
		if ntiid:
			attributes["ntiid"]= ntiid
			modified = True
										
	return modified 	

def getNTIID(sourceFile, ntiid_pattern):
	"""
	Return the NTIID from the specified file 
	"""
	
	if os.path.exists(sourceFile):
		s = ''
		with open(sourceFile, "r") as f:
			s = f.read()
		
		m = ntiid_pattern.search(s, re.M|re.I)
		if m: return m.groups()[0]
					
	return None 

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


