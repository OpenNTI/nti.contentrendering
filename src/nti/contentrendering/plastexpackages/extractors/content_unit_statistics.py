#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract content unit statistics

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import re
import simplejson as json

from zope import component
from zope import interface

from nti.contentrendering.interfaces import IRenderedBook
from nti.contentrendering.interfaces import IContentUnitStatistics

from nti.contentrendering.plastexpackages.extractors._utils import _render_children


	
@interface.implementer(IContentUnitStatistics)
@component.adapter(IRenderedBook)
class _ContentUnitStatistics(object):

	def __init__(self, book=None):
		pass

	def transform(self, book, outpath=None):
		outpath = outpath or book.contentLocation
		outpath = os.path.expanduser(outpath)
		dom = book.toc.dom
		root = dom.documentElement
		index = {'Items' : {}}
		self._process_topic(root, index['Items'])
		return index

	def _process_topic(self, node, index):
		if node.hasAttribute('ntiid'):
			ntiid = node.getAttributeNode('ntiid').value
			element_index = index[ntiid] = {}
			element_index['NTIID'] = ntiid
		
		if node.hasChildNodes():	
			for child in node.childNodes:
				if child.nodeName == 'topic':
					containing_index = element_index.setdefault('Items', {})
					self._process_topic(child, containing_index)