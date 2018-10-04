#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import codecs
import logging
import argparse
import simplejson as json

from zope import interface

from zope.exceptions.log import Formatter as LogFormatter

from nti.contentrendering.utils import EmptyMockDocument
from nti.contentrendering.utils import NoConcurrentPhantomRenderedBook

from nti.contentrendering.interfaces import IRenderedBookExtractor
interface.moduleProvides(IRenderedBookExtractor)

logger = __import__('logging').getLogger(__name__)


DEFAULT_LOG_FORMAT = '[%(asctime)-15s] [%(name)s] %(levelname)s: %(message)s'


def configure_logging(level='INFO', fmt=DEFAULT_LOG_FORMAT):
    level = getattr(logging, level.upper(), None)
    level = logging.INFO if not isinstance(level, int) else level
    logging.basicConfig(level=level)
    logging.root.handlers[0].setFormatter(LogFormatter(fmt))
_configure_logging = configure_logging


def _update_parent_pages(element, index, pagenumber):
    try:
        parent = element.parentNode
    except AttributeError:
        return

    ntiid = getattr(parent, 'ntiid', None)
    if ntiid:
        index['NTIIDs'][ntiid].append(pagenumber)
    _update_parent_pages(parent, index, pagenumber)


def _build_index(element, index, container_ntiid=None, nav_ntiid=None):
    """
    Recurse through the element adding realpagenumber objects to the index,
    keyed off of NTIIDs.

    :param dict index: The containing index node.
    """
    _last_page_seen = None
    ntiid = getattr(element, 'ntiid', None)
    _nav_ntiid = getattr(element, 'embedded_doc_cross_ref_url', nav_ntiid)
    _container_ntiid = ntiid or container_ntiid
    try:
        if index['NTIIDs'][container_ntiid]:
            _last_page_seen = index['NTIIDs'][container_ntiid][-1]
    except KeyError:
        pass

    if not ntiid:
        realpagenumber = getattr(element, 'pagenumber', None)
        if realpagenumber:
            realpagenumber = unicode(realpagenumber)
            index['real-pages'][realpagenumber] = {
                'NTIID': _container_ntiid,
                'NavNTIID': _nav_ntiid or _container_ntiid
            }
            _update_parent_pages(element, index, realpagenumber)
    elif ntiid not in index['NTIIDs']:
        index['NTIIDs'][ntiid] = []
        if _last_page_seen:
            index['NTIIDs'][ntiid].append(_last_page_seen)
    else:
        logger.error("NTIID must be unique %s", ntiid)
        return

    __traceback_info__ = index

    for child in element.childNodes:
        if child.hasChildNodes():  # Recurse for children if needed
            _build_index(child, index, container_ntiid=_container_ntiid, nav_ntiid=_nav_ntiid)


def transform(book, savetoc=True, outpath=None):
    __traceback_info__ = savetoc, outpath
    outpath = outpath or book.contentLocation
    outpath = os.path.expanduser(outpath)
    target = os.path.join(outpath, 'real_pages.json')

    index = {'real-pages': {}, 'NTIIDs': {}}
    documents = book.document.getElementsByTagName('document')
    if not documents:
        return

    _build_index(documents[0], index)

    if index['real-pages']:  # check if there is something
        logger.info("extracting real page numbers to %s", target)
        with codecs.open(target, 'w', encoding='utf-8') as fp:
            # sort_keys for repeatability. Do force ensure_ascii because even though
            # we're using codes to  encode automatically, the reader might not
            # decode
            json.dump(index,
                      fp,
                      indent='\t',
                      sort_keys=True,
                      ensure_ascii=True)
            fp.write('\n')
    return index


def extract(contentpath, outpath=None, jobname=None):
    jobname = jobname or os.path.basename(contentpath)
    document = EmptyMockDocument()
    document.userdata['jobname'] = jobname
    book = NoConcurrentPhantomRenderedBook(document, contentpath)
    return transform(book, outpath)


def main():
    def register():
        from zope.configuration import xmlconfig
        from zope.configuration.config import ConfigurationMachine
        from zope.configuration.xmlconfig import registerCommonDirectives
        context = ConfigurationMachine()
        registerCommonDirectives(context)

        import nti.contentrendering as contentrendering
        xmlconfig.file("configure.zcml", contentrendering, context=context)
    register()

    configure_logging()
    arg_parser = argparse.ArgumentParser(description="Content page extractor")
    arg_parser.add_argument('contentpath', help="Content book location")
    arg_parser.add_argument('-v', '--verbose', help="Be verbose",
                            action='store_true', dest='verbose')
    args = arg_parser.parse_args()

    contentpath = os.path.expanduser(args.contentpath)
    jobname = os.path.basename(contentpath)
    if contentpath.endswith(os.path.sep):
        contentpath = contentpath[:-1]
    extract(contentpath, jobname=jobname)


if __name__ == '__main__':
    main()
