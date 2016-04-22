#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import six
import subprocess

# BWC re-export
from nti.contentrendering.phantom import _closing
from nti.contentrendering.phantom import javascript_path
from nti.contentrendering.phantom import run_phantom_on_page
from nti.contentrendering.phantom import _PhantomProducedUnexpectedOutputError

# BWC re-export
from nti.futures.futures import ConcurrentExecutor
ConcurrentExecutor = ConcurrentExecutor

class _NotFound(object):
	"""
	A descriptive False object
	"""

	def __init__(self, msg):
		self.msg = msg

	def __nonzero__(self):
		return False
	__bool__ = __nonzero__

	def __str__(self):
		return self.msg

class _programproperty(object):
	"""
	A readproperty (meaning you can override in the instance)
	that knows how to hold verification arguments.
	"""

	def __init__(self, env_name, prog_name, verify_arg=''):
		self.env_name = env_name
		self.prog_name = prog_name
		self.verify_arg = verify_arg

	def __get__(self, inst, klass):
		if inst is None:
			return self
		return os.environ.get(self.env_name, self.prog_name)

class _ExternalProgramSettings(object):
	"""
	Provisional API to standardize the way we find and run
	external programs.
	"""

	# Lacking a clean way to register new programs to verify

	def __init__(self):
		self._verify_cache = {}

	gs = _programproperty('GHOSTSCRIPT', 'gs', '--help')
	# Identify is provided by ImageMagick
	identify = _programproperty('IDENTIFY', 'identify')
	# convert is provided by ImageMagick
	convert = _programproperty('CONVERT', 'convert')
	pngcrush = _programproperty('PNGCRUSH', 'pngcrush')
	pdfcrop = _programproperty("PDFCROP", 'pdfcrop')
	pdf2svg = _programproperty("PDF2SVG", 'pdf2svg')

	def verify(self, programs=None):
		"""
		Check that all the needed programs are on the PATH and executable.

		:param programs: If given, a sequence of the program names to check for.
		"""
		if programs is not None and isinstance(programs, six.string_types):
			programs = (programs,)

		for k, v in self.__class__.__dict__.items():
			if not isinstance(v, _programproperty):
				continue
			if programs is not None and k not in programs:
				continue

			program = getattr(self, k)
			if k in self._verify_cache and self._verify_cache[k][0] == program:
				if not self._verify_cache[k][1]:
					return self._verify_cache[k][1]
				continue

			__traceback_info__ = k, program
			try:
				command = [program, v.verify_arg] if v.verify_arg else program
				proc = subprocess.Popen(command,
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
