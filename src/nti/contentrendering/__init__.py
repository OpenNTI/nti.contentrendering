#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

## re-export
from .phantom import _closing
from .phantom import javascript_path
from .phantom import run_phantom_on_page
from .phantom import _PhantomProducedUnexpectedOutputError

## BWC re-export
from nti.futures.futures import ConcurrentExecutor
ConcurrentExecutor = ConcurrentExecutor

import os
import subprocess
import six

class _NotFound(object):
	"""A descriptive False object"""
	def __init__(self, msg):
		self.msg = msg

	def __nonzero__(self):
		return False
	__bool__ = __nonzero__

	def __str__(self):
		return self.msg

class _ExternalProgramSettings(object):
	"""
	Provisional API to standardize the way we find and run
	external programs.
	"""

	# Lacking a clean way to register new programs to verify

	def __init__(self):
		self._verify_cache = {}

	@property
	def gs(self):
		return os.environ.get('GHOSTSCRIPT', 'gs')
	@property
	def identify(self):
		# Identify is provided by ImageMagick
		return os.environ.get('IDENTIFY', 'identify')
	@property
	def convert(self):
		# convert is provided by ImageMagick
		return os.environ.get('CONVERT', 'convert')
	@property
	def pngcrush(self):
		return os.environ.get('PNGCRUSH', 'pngcrush')
	@property
	def pdfcrop(self):
		return os.environ.get("PDFCROP", 'pdfcrop')
	@property
	def pdf2svg(self):
		return os.environ.get("PDF2SVG", 'pdf2svg')

	def verify(self, programs=None):
		"""
		Check that all the needed programs are on the PATH and executable.

		:param programs: If given, a sequence of the program names to check for.
		"""
		if programs is not None and isinstance(programs, six.string_types):
			programs = (programs,)
		for k, v in self.__class__.__dict__.items():
			if not isinstance(v, property):
				continue
			if programs is not None and k not in programs:
				continue

			program = getattr(self, k)
			if k in self._verify_cache and self._verify_cache[k][0] == program:
				if not self._verify_cache[k][1]:
					return self._verify_cache[k][1]

			__traceback_info__ = k, program
			try:
				proc = subprocess.Popen(program,
										shell=False,
										stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
										close_fds=True)
				output, _ = proc.communicate()
			except OSError:
				output = None

			found = bool(output)
			if not found:
				found = _NotFound("Unable to find program %s for property %s" % (program, k))

			self._verify_cache[k] = program, found
			if not found:
				logger.warn(found)
				return found
		return True


_programs = _ExternalProgramSettings()
