#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A resource converter the copies a resource into the resource system with no coversion.

..note:: This module is currently not tested.

$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import tempfile
import shutil

import nti.contentrendering.resources as resources
from nti.contentrendering.jsonpbuilder import _JSONPWrapper

from ._util import copy
from . import converters

_RESOURCE_TYPE = 'jsonp'

# XXX: TODO: Very similar to converter_html_wrapped

class JSONPBatchConverterDriver(object):

	fileExtension = '.jsonp'
	resourceType = _RESOURCE_TYPE

	def __init__(self):
		self._jsonp_tempdir = tempfile.mkdtemp()

	def _convert_unit(self, unit):
		unit_path = unit.attributes['src']
		ext = os.path.splitext(unit_path)[1]
		resource_path = tempfile.mkstemp(suffix=ext,dir=self._jsonp_tempdir)[1]

		plain = resources.Resource()
		plain.path = resource_path
		plain.resourceType = 'raw'
		plain.qualifiers = ('raw',)
		plain.source = unit.source
		copy(unit_path, plain.path)

		jsonp = resources.Resource()
		jsonp.path = resource_path + self.fileExtension
		jsonp.resourceType = 'jsonp'
		jsonp.qualifiers = ('wrapped',)
		jsonp.source = unit.source
		ntiid = unit.ntiid if hasattr(unit,'ntiid') else unit.id
		_JSONPWrapper(ntiid, resource_path, 'jsonpData').writeJSONPToFile()

		return [plain, jsonp]

	def convert_batch(self, content_units):
		# Here we need to convert the incoming blog to jsonp and write both versions to
		# the resource folder.
		return [self._convert_unit(unit) for unit in content_units]

	def close(self):
		shutil.rmtree(self._jsonp_tempdir, True)
		self._jsonp_tempdir = None


class JSONPBatchConverter(converters.AbstractContentUnitRepresentationBatchConverter):
	"""
	Converts by compiling latex using the TTM command.
	"""

	resourceType = _RESOURCE_TYPE

	def _new_batch_converter_driver(self, *args, **kwargs):
		return JSONPBatchConverterDriver()

ResourceGenerator = JSONPBatchConverter
ResourceSetGenerator = JSONPBatchConverterDriver

from zope.deprecation import deprecated
deprecated(['ResourceGenerator', 'ResourceSetGenerator'], 'Prefer the new names in this module')
