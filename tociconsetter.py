#!/usr/bin/env python

import os
import urllib
import sys

from pyquery import PyQuery
from . import RenderedBook

import logging
logger = logging.getLogger(__name__)

from zope import interface
from zope import component
from zope.deprecation import deprecate
from . import interfaces

interface.moduleProvides( interfaces.IRenderedBookTransformer )

def main(args):
	""" Main program routine """

	contentLocation = args[0]
	book = RenderedBook.RenderedBook( None, contentLocation )

	transform( book )

def transform( book, save_toc=True ):
	"""
	Modifies the TOC dom by: reading NTIIDs out of HTML content and adding them
	to the TOC, setting icon attributes in the TOC. Also modifies HTML content
	to include background images when appropriate.
	"""
	dom = book.toc.dom
	toc = dom.getElementsByTagName("toc")
	if toc:
		modified, child_nodes = _handle_toc(toc[0], book, save_toc)
		if save_toc:
			if modified:
				book.toc.save()
			return modified
		# Testing mode: return a tuple
		return modified, child_nodes

	raise Exception( "Failed to transform %s" % (book) )

def _handle_toc(toc, book, save_dom):
	contentLocation = book.contentLocation
	attributes = toc.attributes
	attributes['href'] = "index.html"
	modified = True
	# For testing, we return the child nodes we modify
	# (otherwise don't waste the memory)
	child_nodes = []
	if contentLocation:
		index = _Topic( toc, contentLocation, os.path.join( contentLocation, 'index.html' ) )
		modified = index.set_ntiid()

		title = index.get_title( )
		if title:
			modified = index.set_label( title ) or modified
			modified = index.set_icon( "icons/chapters/" + title + "-icon.png" ) or modified

		for node in index.childTopics:
			node.save_dom = save_dom
			_handle_topic( book, node )
			if not save_dom: child_nodes.append( node )

	return modified, child_nodes

def _query_finder( book, topic, iface ):
	result = component.queryMultiAdapter( (book,topic), iface, name=book.jobname )
	if not result and book.jobname != '':
		# If nothing for the job, query the global default
		result = component.queryMultiAdapter( (book,topic), iface )
	return result

def _handle_topic( book, _topic ):
	modified = False

	if _topic.is_chapter():
		if not _topic.has_icon():
			icon_finder = _query_finder( book, _topic, interfaces.IIconFinder )
			icon_path = icon_finder.find_icon() if icon_finder else None
			modified = _topic.set_icon( icon_path ) if icon_path else modified

		modified = _topic.set_ntiid() or modified
		bg_finder = _query_finder( book, _topic, interfaces.IBackgroundImageFinder )
		bg_path = bg_finder.find_background_image() if bg_finder else None
		modified |= _topic.set_background_image( bg_path ) if bg_path else modified

		# modify the sub-topics
		modified = _handle_sub_topics(_topic) or modified

	return modified

def _handle_sub_topics(topic):
	"""
	Set the NTIID for all sub topics
	"""

	modified = False

	for node in topic.childTopics:
		modified = node.set_ntiid() or modified

	return modified

class _PrealgebraIconFinder(object):
	path_type = 'icons'

	def __init__( self, book, topic ):
		self._book = book
		self._topic = topic

	def find_icon( self ):
		# Note that the return is in URL-space using /, but the check
		# for existence uses local path conventions
		imagename = 'C' + str(self._topic.ordinal) + '.png'
		path = os.path.join( self._book.contentLocation,
							 self.path_type,
							 'chapters',
							 imagename )
		if os.path.exists( path ):
			return self.path_type + '/chapters/' + imagename

class _PrealgebraBackgroundImageFinder(_PrealgebraIconFinder):
	path_type = 'images'
	find_background_image = _PrealgebraIconFinder.find_icon

class _Topic(object):
	"""
	Attributes:
	`ordinal` A number starting at one representing which (nth) child
		I am of the parent.
	"""
	# TODO: Merge this class with RenderedBook.ContentPage
	interface.implements( interfaces.IEclipseMiniDomTopic )

	save_dom = True

	def __init__( self, topic, contentLocation, sourceFile=None ):
		self.topic = topic
		self.contentLocation = contentLocation
		self.sourceFile = sourceFile or (self.get_chapter_filename( )
										 and os.path.join( contentLocation, self.get_chapter_filename().value ) )
		self.modifiedTopic = False
		self.modifiedDom = False
		self._dom = None
		self.ordinal = 1

	@property
	@deprecate("Prefer `childTopics`; this returns arbitrary Nodes")
	def childNodes(self):
		"""
		:return: An iterable of :class:`_Topic` objects representing the children
			of this object.
		"""
		childCount = 1
		for x in self.topic.childNodes:
			result = self.__class__( x, self.contentLocation )
			result.ordinal = childCount
			childCount += 1
			yield result

	@property
	def childTopics(self):
		"""
		:return: An iterable of :class:`_Topic` objects representing the topic element children
			of this object.
		"""
		childCount = 1
		for x in self.topic.childNodes:
			if x.nodeType == x.ELEMENT_NODE and x.localName == 'topic':
				result = self.__class__( x, self.contentLocation )
				result.ordinal = childCount
				childCount += 1
				yield result

	@property
	def nodeType(self): return self.topic.nodeType

	@property
	def localName(self): return self.topic.localName

	@property
	def dom(self):
		if not self._dom and self.sourceFile and os.path.exists( self.sourceFile ):
			# we've seen this throw ValueError: I/O operation on closed file
			# we've also seen AttributeError: 'NoneType' object has no attribute 'xpath'
			# on dom("body")
			body_len = 0
			dom = None
			try:
				dom = PyQuery( filename=self.sourceFile )
				body_len = len(dom("body"))
			except (ValueError,AttributeError):
				logger.warn( "Failed to parse %s as XML. Will try HTML.", self.sourceFile, exc_info=False )

			if body_len != 1:
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

	def set_background_image( self, image_path ):

		dom = self.dom
		if dom is None:
			return False

		dom("body").attr["style"] = r"background-image: url('" + image_path + r"')"
		if self.save_dom:
			with open(self.sourceFile, 'w') as f:
				f.write( dom.outerHtml().encode( "utf-8" ) )

		self.modifiedDom = True
		return self.modifiedDom

	def get_background_image( self ):
		dom = self.dom
		if dom is None:
			return None
		return dom('body').attr('style')

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

	def is_chapter(self):
		attributes = self.topic.attributes
		if attributes:
			label = attributes.get('label',None)
			return (label and label.value !='Index')
		return False

if __name__ == '__main__':
	main( sys.argv[1:] )
