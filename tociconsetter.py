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
		os.remove(file)
		os.rename(tempfile, tocFile)
		
def handleToc(toc, chapterPath):
	current = 0
	modified = False
	for node in toc.childNodes:
		if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
			current += 1
			modified = handleTopic(node, current, chapterPath) or modified
			
	return modified;

	
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
				setBackgroundImage(sourceFile, imageName, current)
				
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
		
def setBackgroundImage(sourceFile, imageName, current):
	
	if not os.path.exists(sourceFile) or not os.access(sourceFile, os.O_RDWR):
		return False
	
	outfile = '%s/temp-ch-file.%s.%s.html' % (tempfile.gettempdir(),  os.getpid(), current)
	
	modified = False
	with open(outfile,"w") as out:
		with open(sourceFile, 'r') as source:
			buffer = ''
			bodyFound = False
			while True:
				s = source.read(buffer_size)
				if (not s): break;
				
				if not bodyFound:
					buffer += s;
					idx = buffer.find("<body");
					bodyFound = (idx != -1)
					if bodyFound:
						
						# search closing tag
						while buffer.find(">", idx) == -1:
							s = source.read(1)
							if (not s): raise IOError("Unexpected EOF")
							buffer += s;
					
						
						#check for style
						
						eidx = buffer.find(">", idx);	
						s = buffer[idx:eidx+1]
						
						if s.find("style") == -1:
							s = (
									buffer[:(idx+5)] +
									" style=\"background: url(\'images/chapters/" + imageName + "')\" " +
									buffer[(idx+5):] 
								)
							out.write(s);
							modified = True
				# body found		
				else: 
					out.write(s);
					
	if modified:
		os.remove(sourceFile)
		os.rename(outfile, sourceFile)
	else:
		os.remove(outfile)

	return modified;

if __name__ == '__main__':	
	args = sys.argv[1:]
	if args:
		main(args)
	else:
		print("Specify a toc file [chapter path]")
