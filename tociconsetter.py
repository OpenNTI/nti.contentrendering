#!/usr/bin/env python

import os
import urllib
import sys
import tempfile

from xml.dom.minidom import parse
from xml.dom.minidom import Node

from pyquery import PyQuery

import logging
logger = logging.getLogger(__name__)

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

def transform(tocFile, contentLocation=None):
	dom = parse(tocFile)
	toc = dom.getElementsByTagName("toc")
	if toc and _handle_toc(toc[0], contentLocation):
		xml_file = to_xml(dom)
		os.remove(tocFile)
		os.rename(xml_file, tocFile)
	else:
		raise Exception( "Failed to transform %s (dom %s; toc %s)" % (tocFile, dom, toc) )

def _handle_toc(toc, contentLocation):
	current = 0

	attributes = toc.attributes
	attributes['href'] = "index.html"
	modified = True
	if contentLocation:
		index = _Topic( toc, contentLocation, os.path.join( contentLocation, 'index.html' ) )
		modified = index.set_ntiid()

		title = index.get_title( )
		if title:
			modified = index.set_label( title ) or modified
			modified = index.set_icon( "icons/chapters/" + title + "-icon.png" ) or modified

		for node in index.childNodes:
			if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
				current += 1
				_handle_topic(node, current, contentLocation)

	return modified


def _handle_topic(topic, current, contentLocation):
	modified = False

	if is_chapter(topic.attributes):
		_topic = _Topic( topic, contentLocation )
		imageName = 'C' + str(current) + '.png'
		if not _topic.has_icon():
			modified = _topic.set_icon( 'icons/chapters/' + imageName )

		if contentLocation:
			modified = _topic.set_ntiid() or modified
			modified = _topic.set_background_image( imageName ) or modified

			# modify the sub-topics
			modified = _handle_sub_topics(topic, contentLocation) or modified

	return modified

def _handle_sub_topics(topic, contentLocation):
	"""
	Set the NTIID for all sub topics
	"""

	modified = False

	for node in topic.childNodes:
		if node.nodeType == Node.ELEMENT_NODE and node.localName == 'topic':
			modified = _Topic( node, contentLocation).set_ntiid() or modified

	return modified

class _Topic(object):

	def __init__( self, topic, contentLocation, sourceFile=None ):
		self.topic = topic
		self.contentLocation = contentLocation
		self.sourceFile = sourceFile or (self.get_chapter_filename( )
										 and os.path.join( contentLocation, self.get_chapter_filename().value ) )
		self.modifiedTopic = False
		self.modifiedDom = False
		self._dom = None

	@property
	def childNodes(self):
		return self.topic.childNodes

	@property
	def dom(self):
		if not self._dom and self.sourceFile and os.path.exists( self.sourceFile ):
			dom = PyQuery( filename=self.sourceFile )
			if len(dom("body")) != 1:
				dom = PyQuery( filename=self.sourceFile, parser="html" )
			self._dom = dom
		return self._dom

	def set_ntiid( self ):
		"""
		Set the NTIID for the specifed topic
		"""

		ntiid = self.get_ntiid()
		if ntiid:
			self.topic.attributes["ntiid"] = ntiid
			self.modifiedTopic = True

		return self.modifiedTopic

	def get_ntiid(self):
		"""
		Return the NTIID from the specified file
		"""
		try:
			return self.dom("meta[name=NTIID]").attr( "content" )
		except IOError:
			logger.debug( "Unable to open file %s", self.sourceFile, exc_info=True )
			return None

	def get_title( self ):
		return self.dom("title").text()

	def get_chapter_filename( self ):
		return (self.topic.attributes and self.topic.attributes.get('href'))

	def set_background_image( self, imageName ):

		dom = self.dom
		if dom is None:
			return False

		dom("body").attr["style"] = r"background-image: url('images/chapters/" + imageName + r"')"

		with open(self.sourceFile, 'w') as f:
			f.write( dom.outerHtml().encode( "utf-8" ) )

		self.modifiedDom = True
		return self.modifiedDom

	def has_icon( self ):
		return (self.topic.attributes and self.topic.attributes.get('icon'))

	def set_icon( self, icon ):
		self.topic.attributes['icon'] = urllib.quote( icon )
		self.modifiedTopic = True
		return self.modifiedTopic

	def set_label( self, label ):
		self.topic.attributes['label'] = label
		self.modifiedTopic = True
		return self.modifiedTopic

def is_chapter(attributes):
	if attributes:
		label = attributes.get('label',None)
		return (label and label.value !='Index')
	return False

def to_xml( document ):
	outfile = '%s/temp-toc-file.%s.xml' % (tempfile.gettempdir(), os.getpid())
	with open(outfile,"w") as f:
		document.writexml(f)
	return outfile

if __name__ == '__main__':
	args = sys.argv[1:]
	if args:
		main(args)
	else:
		print("Specify a toc file [chapter path]")


