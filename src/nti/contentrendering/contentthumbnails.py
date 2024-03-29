#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Functions related to creating thumbnails of content.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import tempfile
import subprocess

from nti.contentrendering import _programs
from nti.contentrendering import javascript_path
from nti.contentrendering import ConcurrentExecutor
from nti.contentrendering import run_phantom_on_page

from nti.contentrendering.interfaces import IRenderedBookTransformer

_rasterize_script = javascript_path('rasterize.js')
thumbnailsLocationName = 'thumbnails'


def create_thumbnail_of_html(page_location, page_ntiid, output_file_path,
                             width=180, height=251, zoom_factor=0.25):
    """
    Given an absolute path pointing to an HTML file, produce a PNG
    thumbnail image for the page in ``output_file_path``.

    This function may raise :class:`subprocess.CalledProcessError`,
    :class:`ValueError` or :class:`TypeError`.

    :param page_location: Either an absolute file path
            or a URL that phantomjs can open.

    :return: A two-tuple, the page's NTIID from ``page_ntiid`` and the path to the generated
            thumbnail.
    """
    # Rasterize the page to an image file as a side effect
    # For BWC, the size is odd, at best:
    # Generate a 180 x 251 image, at 25% scale
    run_phantom_on_page(page_location, _rasterize_script,
                        args=(output_file_path,
                              str(width),
                              str(height),
                              str(zoom_factor)),
                        expect_no_output=True)

    return (page_ntiid, output_file_path)
_create_thumbnail_of_html = create_thumbnail_of_html


def create_thumbnail_of_pdf(pdf_path, page=1, height=792, width=612):
    # NOTE: Tests for this live in plastexpackages/ntilatexmacros
    # A standard US page is 612x792 pts, height and width
    # need to be the same multiple of that to preserve aspect ratio
    # such as height=120, width=93
    # We generate a PNG of the complete thing at full size, and then
    # scale it to the various resource sizes when rendering
    # (TODO: Use pyPDF or gs itself to find the actual size of the first page?)
    if not _programs.verify('gs'):
        raise ValueError("Unable to create thumbnail, GS not available")
    GHOSTSCRIPT = _programs.gs

    fd, output_file = tempfile.mkstemp('.png', 'thumbnail')
    # DEVICE=jpeg is another option; using png works better with the image
    # renderer
    cmd = [GHOSTSCRIPT, '-dNOPAUSE', '-dSAFER',
           '-dBATCH', '-q',
           "-dFirstPage=%d" % page,
           "-dLastPage=%d" % page,
           "-dPDFFitPage",
           "-dTextAlphaBits=4",
           "-dGraphicsAlphaBits=4",
           "-sDEVICE=pngalpha",
           "-dDEVICEWIDTH=%d" % width,
           "-dDEVICEHEIGHT=%d" % height,
           "-sOutputFile=%s" % output_file,
           pdf_path]
    # Note that gs can also take "-" as
    # the source path to read from stdin, if we already have it
    # in memory
    __traceback_info__ = cmd
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    finally:
        os.close(fd)
    return output_file
_create_thumbnail_of_pdf = create_thumbnail_of_pdf


def transform(book, context=None):
    """
    Generate thumbnails for all pages and stuff them in the toc.
    """

    eclipseTOC = book.toc

    # generate a place to put the thumbnails
    thumbnails_dir = os.path.join(book.contentLocation,
                                  thumbnailsLocationName)

    if not os.path.isdir(thumbnails_dir):
        os.mkdir(thumbnails_dir)

    # Create the parallel sets of arguments
    # for _create_thumbnail_of_html
    page_paths = []
    page_ntiids = []
    thumbnail_paths = []

    for page in book.pages.values():
        page_paths.append(os.path.join(book.contentLocation, page.location))
        page_ntiids.append(page.ntiid)
        thumbnail_name = '%s.png' % os.path.splitext(page.filename)[0]
        thumbnail_paths.append(os.path.join(thumbnails_dir, thumbnail_name))

    with ConcurrentExecutor() as executor:
        # If _generateImage raises an exception, we will fail to
        # unpack the tuple result (because the exception is returned)
        # and this function will fail

        for ntiid, thumbnail_file in executor.map(_create_thumbnail_of_html,
                                                  page_paths,
                                                  page_ntiids,
                                                  thumbnail_paths):
            node = eclipseTOC.getPageNodeWithNTIID(ntiid)
            node.attributes['thumbnail'] = os.path.relpath(thumbnail_file,
                                                           start=book.contentLocation)
    eclipseTOC.save()


from zope import component
component.moduleProvides(IRenderedBookTransformer)
