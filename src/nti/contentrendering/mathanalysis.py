#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import sys
from collections import defaultdict

from xml.dom import minidom, Node

def main():
	mathxml = minidom.parse(sys.stdin)
	maths = mathxml.getElementsByTagName("math")

	simpleElementDict = defaultdict(list)

	emptyCount = 0
	simpleCount = 0
	complexCount = 0

	for math in maths:
		mathId = math.getAttribute('id')
		if isEmptyMath(math):
			emptyCount = emptyCount + 1
			print('Found empty math element with id %(id)s' % {'id': mathId})
		elif isSimpleMath(math):
			simpleCount = simpleCount + 1
			content = ' '.join(math.firstChild.nodeValue.split())

			simpleElementDict[content].append(id)

			print('Found simple element with id %(id)s and contents %(value)s' % \
				  {'id': mathId, 'value': math.firstChild.nodeValue})

	for content in simpleElementDict:
		print('%(c)d items have content %(value)s' % {'c': len(simpleElementDict[content]), 'value': content})

	print('Found %(e)d empty maths, %(s)d simple maths, %(u)d unique simple maths, and %(c)d complex maths' % \
		  {'e': emptyCount, 's': simpleCount, 'c': complexCount, 'u': len(simpleElementDict)})

def isEmptyMath(math):
	return not math.hasChildNodes()

def isSimpleMath(math):
	return 		math.hasChildNodes() \
			and 1 == len(math.childNodes) \
			and math.firstChild.nodeType == Node.TEXT_NODE

def analyzeMath(math):
	pass

if __name__ == '__main__':
	main()
