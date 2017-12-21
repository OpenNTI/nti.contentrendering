#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import base64

from zope import interface
from zope import component

from zope.configuration import xmlconfig

import nti.contentrendering

from nti.contentrendering.interfaces import IIconFinder
from nti.contentrendering.interfaces import IRenderedBook
from nti.contentrendering.interfaces import IEclipseMiniDomTopic
from nti.contentrendering.interfaces import IBackgroundImageFinder
from nti.contentrendering.interfaces import IRenderedBookTransformer

from nti.contentrendering.interfaces import JobComponents

from nti.contentrendering.RenderedBook import RenderedBook

interface.moduleProvides(IRenderedBookTransformer)

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IIconFinder)
@component.adapter(IRenderedBook, IEclipseMiniDomTopic)
class SimpleConventionIconFinder(object):
    """
    Follows a simple convention to find icons for topics: looks in the
    'icons/chapters' directory for a file named 'CX.png', where 'X' is the
    chapter (topic) number.
    """
    path_type = 'icons'

    def __init__(self, book, topic):
        self._book = book
        self._topic = topic

    def find_icon(self):
        # Note that the return is in URL-space using /, but the check
        # for existence uses local path conventions
        imagename = 'C' + str(self._topic.ordinal) + '.png'

        path = os.path.join(self._book.contentLocation,
                            self.path_type,
                            'chapters',
                            imagename)
        if os.path.exists(path):
            return self.path_type + '/chapters/' + imagename


@interface.implementer_only(IBackgroundImageFinder)
@component.adapter(IRenderedBook, IEclipseMiniDomTopic)
class SimpleConventionBackgroundImageFinder(SimpleConventionIconFinder):
    """
    Just like the super class, but looks in the 'images/chapters' directory.
    """
    path_type = 'images'
    find_background_image = SimpleConventionIconFinder.find_icon


def _query_finder(book, topic, iface, context=None):
    # If nothing for the job, query the global default. This should be handled
    # by our customized components implementation
    result = component.queryMultiAdapter((book, topic), iface, context=context)
    return result


def _handle_sub_topics(topic):
    """
    Set the NTIID for all sub topics
    """
    modified = False
    for node in topic.childTopics:
        modified = node.set_ntiid() or modified
    return modified


def _handle_topic(book, _topic, context=None):
    modified = False

    if _topic.is_chapter():
        if not _topic.has_icon():
            icon_finder = _query_finder(book, _topic, IIconFinder,
                                        context=context)
            icon_path = icon_finder.find_icon() if icon_finder else None
            modified = _topic.set_icon(icon_path) if icon_path else modified

        modified = _topic.set_ntiid() or modified
        bg_finder = _query_finder(book, _topic, IBackgroundImageFinder,
                                  context=context)
        bg_path = bg_finder.find_background_image() if bg_finder else None
        modified |= _topic.set_background_image(bg_path) if bg_path else modified

        # modify the sub-topics
        modified = _handle_sub_topics(_topic) or modified

    return modified


def _get_safe_icon_filename(title):
    """
    Get the safe icon path from the (possibly user generated) title.
    """
    result = None
    if isinstance(title, bytes):
        result = title
    else:
        # encode for the filesystem. Not all systems (e.g., Unix)
        # will have an encoding specified
        encoding = sys.getfilesystemencoding() or 'utf-8'
        try:
            result = title.encode(encoding, 'surrogateescape')
        except LookupError:
            # Can't encode it, and the error handler doesn't
            # exist. Probably on Python 2 with an astral character.
            # Not sure how to handle this.
            pass
    if result is not None:
        result = base64.urlsafe_b64encode(result)
    return result


def _handle_toc(toc, book, save_dom, context=None):
    contentLocation = book.contentLocation
    attributes = toc.attributes
    if not attributes.has_key('href'):
        logger.warn("Assuming index.html for root node in %s", book)
        attributes['href'] = "index.html"
    modified = True
    # For testing, we return the child nodes we modify
    # (otherwise don't waste the memory)
    child_nodes = []
    if contentLocation:
        index = book.toc.root_topic
        modified = index.set_ntiid()

        title = index.get_title()
        if title:
            modified = index.set_label(title) or modified
            filename = _get_safe_icon_filename(title) or b'book'
            path = "icons/chapters/" + filename + "-icon.png"
            if os.path.exists(os.path.join(contentLocation, path)):
                modified = index.set_icon(path) or modified
            else:
                path = "icons/chapters/generic_book.png"
                modified = index.set_icon(path) or modified

            path = "images/backgrounds/default.png"
            if os.path.exists(os.path.join(contentLocation, path)):
                modified = index.set_background(path) or modified

            path = "images/backgrounds/default.jpg"
            if os.path.exists(os.path.join(contentLocation, path)):
                modified = index.set_background(path) or modified

        for node in index.childTopics:
            node.save_dom = save_dom
            _handle_topic(book, node, context=context)
            if not save_dom:
                child_nodes.append(node)

    return modified, child_nodes


def main(args):
    contentLocation = args[0]

    xmlconfig.file('configure.zcml', package=nti.contentrendering)
    zope_conf_name = os.path.join(contentLocation, '..', 'configure.zcml')
    if os.path.exists(zope_conf_name):
        xmlconfig.file(os.path.abspath(zope_conf_name),
                       package=nti.contentrendering)

    path = os.path.abspath(contentLocation)
    context = JobComponents(os.path.split(path)[-1])

    book = RenderedBook(None, contentLocation)
    transform(book, context=context)


def transform(book, save_toc=True, context=None):
    """
    Modifies the TOC dom by: reading NTIIDs out of HTML content and adding them
    to the TOC, setting icon attributes in the TOC. Also modifies HTML content
    to include background images when appropriate.
    """
    dom = book.toc.dom
    toc = dom.getElementsByTagName("toc")
    if toc:
        modified, child_nodes = _handle_toc(toc[0], book,
                                            save_toc, context=context)
        if save_toc:
            if modified:
                book.toc.save()
            return modified
        # Testing mode: return a tuple
        return modified, child_nodes

    raise Exception("Failed to transform %s" % (book))


if __name__ == '__main__':
    main(sys.argv[1:])
