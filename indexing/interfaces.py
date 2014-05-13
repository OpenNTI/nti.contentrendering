#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Book indexing interfaces

.. $Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

from zope import interface

from .. import interfaces as cr_interfaces

class IWhooshIndexSpec(interface.Interface):
	book = interface.Attribute("IRenderedBook object")
	indexname = interface.Attribute("Whoosh index name")
	indexdir = interface.Attribute("Output index directory")

class IWhooshContentIndexer(cr_interfaces.IContentIndexer):

	def process_book(ispec, writer, lang):
		"""
		Index the contents from the specified book 
		
		:param ispec: The :class:`IWhooshIndexSpec`.
		:param writer: Whoosh indexwriter
		:param lang: Book text language
		"""

	def index(book, indexdir=None, indexname=None):
		"""
		Index the specified book 
		
		:param book: The :class:`IRenderedBook`.
		:param indexdir: Output directory
		:param indexname: Index name
		"""

class IWhooshBookIndexer(IWhooshContentIndexer, cr_interfaces.IBookIndexer):

	def process_topic(ispec, node, writer, lang):
		"""
		Index the specified book topic
		
		:param ispec: The :class:`IWhooshIndexSpec`.
		:param node: The :class:`IEclipseMiniDomTopic`.
		:param writer: Whoosh indexwriter
		:param lang: Node text language
		"""

class IWhooshMediaTranscriptIndexer(IWhooshContentIndexer):
	pass

class IWhooshAudioTranscriptIndexer(IWhooshMediaTranscriptIndexer,
									cr_interfaces.IAudioTranscriptIndexer):
	pass

class IWhooshVideoTranscriptIndexer(IWhooshMediaTranscriptIndexer,
									cr_interfaces.IVideoTranscriptIndexer):
	pass


class IWhooshNTICardIndexer(IWhooshContentIndexer, cr_interfaces.INTICardIndexer):
	pass
