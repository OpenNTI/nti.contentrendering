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
		chapterPath = args.pop()

	transform(tocFile, chapterPath)

	try:
		command = 'rm %s/*.bkp' % os.path.realpath(chapterPath)
		os.system(command)
	except:
		pass

def transform(tocFile, chapterPath=None):
	dom = parse(tocFile)
	toc = dom.getElementsByTagName("toc");
	if toc and handle_toc(toc[0], chapterPath):
		tempfile = to_xml(dom)
		os.remove(tocFile)
		os.rename(tempfile, tocFile)

def handle_toc(toc, chapterPath):
	current = 0

	ntiid_pattern = re.compile("<meta.*content=\"(.*)\".*name=\"NTIID\"")

	attributes = toc.attributes
	attributes['href'] = "index.html"
	# Either derive this information naturally or parse it from somewhere else.
	attributes['icon'] = os.environ.get( 'NTI_ICON_PATH', "icons/chapters/PreAlgebra-cov-icon.png" )
	attributes['label'] = os.environ.get( 'NTI_TITLE',  "Prealgebra" )

	if chapterPath:
		sourceFile = chapterPath + '/index.html'
		ntiid = get_ntiid(sourceFile, ntiid_pattern)
		if ntiid:
			attributes["ntiid"]= ntiid

	for node in toc.childNodes:
		if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
			current += 1
			handle_topic(node, current, chapterPath, ntiid_pattern)

	return True;

def handle_topic(topic, current, chapterPath, ntiid_pattern):

	modified = False
	attributes = topic.attributes

	if is_chapter(attributes):

		imageName = 'C' + str(current) + '.png'
		if not has_icon(attributes):
			attributes['icon'] = 'icons/chapters/' + imageName
			modified = True

		if chapterPath:

			chapterFile = get_chapter_filename(attributes)
			if chapterFile:

				sourceFile = chapterPath + '/' + chapterFile.value

				# set the body background image
				set_background_image(sourceFile, imageName)

				# set the ntiid for the chapter
				ntiid = get_ntiid(sourceFile, ntiid_pattern)
				if ntiid:
					attributes["ntiid"]= ntiid
					modified = True

			# modify the sub-topics
			modified = handle_sub_topics(topic, chapterPath, ntiid_pattern) or modified

	return modified

def handle_sub_topics(topic, chapterPath, ntiid_pattern):
	"""
	Set the NTIID for all sub topics
	"""

	modified = False

	for node in topic.childNodes:
		if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
			modified = set_ntiid(node, chapterPath, ntiid_pattern) or modified

	return modified

def set_ntiid(topic, chapterPath, ntiid_pattern):
	"""
	Set the NTIID for the specifed topic
	"""

	modified = False
	attributes = topic.attributes
	chapterFile = get_chapter_filename(attributes)
	if chapterFile:
		sourceFile = chapterPath + '/' + chapterFile.value
		ntiid = get_ntiid(sourceFile, ntiid_pattern)
		if ntiid:
			attributes["ntiid"]= ntiid
			modified = True

	return modified

def get_ntiid(sourceFile, ntiid_pattern):
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

def get_chapter_filename(attributes):
	return (attributes and attributes.get('href'))

def has_icon(attributes):
	return (attributes and attributes.get('icon'))

def is_chapter(attributes):
	if attributes:
		label = attributes.get('label',None)
		return (label and label.value !='Index')
	return False

def to_xml( document ):
	outfile = '%s/temp-toc-file.%s.xml' % (tempfile.gettempdir(), os.getpid())
	with open(outfile,"w") as f:
		document.writexml(f)
	return outfile;

def set_background_image(sourceFile, imageName):

	if not os.path.exists(sourceFile) or not os.access(sourceFile, os.O_RDWR):
		return False

	replace = r"<body \\1 style=\"background-image: url('images\/chapters\/" + imageName + r"') \">"
	command = "sed -i .bkp \"s/<body \\(.*\\)>/" + replace + "/g\" ";

	os.popen(command + sourceFile)

	return True

if __name__ == '__main__':
	args = sys.argv[1:]
	if args:
		main(args)
	else:
		print("Specify a toc file [chapter path]")


