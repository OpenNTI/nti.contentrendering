#!/usr/bin/env python2.7

from zope import interface
from zope import component
from zope import schema

class IRenderedBook(interface.Interface):

	contentLocation = schema.TextLine(
		title=u"The location of the directory on disk containing the content")

class IDocumentTransformer(interface.Interface):
	"""
	Given a plasTeX DOM document, mutate the document
	in place to achieve some specified end. IDocumentTransformer
	*should* perform an idempotent transformation.
	"""

	def transform( document ):
		"""
		Perform the document transformation.
		"""

class IRenderedBookTransformer(interface.Interface):
	"""
	Given a rendered book, mutate its on-disk state
	to achieve some specified end. This *should* be idempotent.
	"""

	def transform( book ):
		"""
		Perform the book transformation.
		"""

class IStaticRelatedItemsAdder(IRenderedBookTransformer):
	"""
	Transforms the book's TOC by adding related items mined from
	the book.
	"""
