#!/usr/bin/env python

import sys
import os
from xml.dom.minidom import parse
from xml.dom.minidom import Node

def main(args):
	""" Main program routine """

	file = args.pop(0)
	dom = parse(file)
	toc = dom.getElementsByTagName("toc");
	if (toc and handleToc(toc[0])):
		tempfile = toXml(dom)
		os.remove(file)
		os.rename(tempfile, file)

def handleToc(toc):
	current = 0
	modified = False
	for node in toc.childNodes:
		if (node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic'):
			current += 1
			modified = handleTopic(node, current) or modified
			
	return modified;

	
def handleTopic(topic, current):
	attributes = topic.attributes
	if (isChapter(attributes)):
		if (not hasIcon(attributes)):
			s = 'C' + str(current) + '.png' 
			attributes['icon'] = 'icons/chapters/' + s
			return True
	return False
		
def hasIcon(attributes):
	return (attributes and attributes.get('icon'))

def isChapter(attributes):
	if (attributes):
		label = attributes.get('label',None)
		return (label and label.value !='Index')
	return False
		
def toXml( document ):	
	outfile = '/tmp/temp-toc-file.%s.xml' % os.getpid()
	with open(outfile,"w") as f:
		document.writexml(f)		
	return outfile;
		
if __name__ == '__main__':
	args = sys.argv[1:]
	if args:
		main(args)
	else:
		print("Specify a toc file")