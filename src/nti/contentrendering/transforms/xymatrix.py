#!/usr/bin/env python
# -*- coding: utf-8 -*
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

import plasTeX
from plasTeX import Base, Node
from plasTeX.Base.LaTeX import Math

from nti.contentrendering import domutils
from nti.contentrendering.resources import interfaces as res_interfaces

from nti.contentrendering.interfaces import IDocumentTransformer

interface.moduleProvides(IDocumentTransformer)

class ntixymatrix(Base.Command):
	@property
	def source(self):
		return self._source

@interface.implementer(res_interfaces.IRepresentationPreferences)
class ntixydisplaymath(Math.displaymath):
	resourceTypes = ['png', 'svg']

@interface.implementer(res_interfaces.IRepresentationPreferences)
class ntixymath(Math.math):
	resourceTypes = ['png', 'svg']

def transform(document):
	document.context['ntixymatrix'] = ntixymatrix
	document.context['ntixymath'] = ntixymath
	document.context['ntixydisplaymath'] = ntixydisplaymath

	xys = domutils.findNodesStartsWith(document, 'xymatrix')

	logger.info( 'Will transform on %s', xys )

	for xy in xys:
		fixxy(document, xy)

plasTeX_DOM = getattr(plasTeX, 'DOM')

def fixxy(document, xy):
	#figure out if the xy would be the only child
	parent = xy.parentNode

	xynodes = []
	# source = xy.source.strip()

	nextSibling = xy

	while (nextSibling.nodeName != 'bgroup'):
		xynodes.append(nextSibling)
		nextSibling = nextSibling.nextSibling

	xynodes.append(nextSibling)

	source = ''.join([node.source.strip() for node in xynodes])

	newxy = document.createElement('ntixymatrix')
	newxy._source = source
	parent.replaceChild(newxy, xynodes[0])

	for oldNode in xynodes[1:]:
		parent.removeChild(oldNode)

	if getattr(parent, 'mathMode', False):
		onlyxy = True

		for child in parent.childNodes:

			if child == newxy:
				continue

			if child.nodeType == Node.TEXT_NODE:
				if child.textContent.strip():
					onlyxy = False
					break

			if child.nodeType == Node.ELEMENT_NODE:
				onlyxy = False
				break

		if onlyxy:
			newparent = None
			if parent.nodeName == 'math':
				newparent = document.createElement('ntixymath')
			else:
				newparent = document.createElement('ntixydisplaymath')

			if newparent != None:
				try:
					parent.parentNode.replaceChild(newparent, parent)
				except plasTeX_DOM.NotFoundErr:
					#Since its not where its suppossed to be, hopefully its in an attribute
					vals = parent.parentNode.attributes.values()

					for val in vals:
						if getattr(val, 'childNodes', None):
							for child in val.childNodes:
								if child == parent:
									val.replaceChild(newparent, parent)

				newparent.appendChild(newxy)
