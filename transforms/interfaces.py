#!/usr/bin/env python2.7

from zope import interface
from zope import component

class IDocumentTransformer(interface.Interface):
	"""
	Given a plasTeX DOM document, mutate the document
	in place to achieve some specified. IDocumentTransformer
	*should* perform an idempotent transformation.
	"""

	def transform( document ):
		"""
		Perform the document transformation.
		"""
