#!/usr/bin/env python2.7

import logging
logger = logging.getLogger(__name__)

from lxml import etree

from zope import interface
from .. import interfaces
interface.moduleProvides(interfaces.IRenderedBookValidator)

def check(book):

	def _check( page ):
		errors = page.dom( "span[class=merror]" )
		all_errors = len(errors)
		if len(errors):
			errors = [etree.tostring(error) for error in errors]
			logger.warn( "Mathjax errors for page %s: %s", page.filename, errors )
		for child in page.childTopics:
			all_errors += _check( child )

		return all_errors


	all_errors = _check( book.toc.root_topic )

	if not all_errors:
		logger.info( "No MathJax errors" )

	return all_errors
