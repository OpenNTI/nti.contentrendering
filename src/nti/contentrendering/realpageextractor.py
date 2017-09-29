#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import codecs
import os
import argparse
import simplejson as json

from zope import interface

from .utils import EmptyMockDocument
from .utils import NoConcurrentPhantomRenderedBook

from .interfaces import IRenderedBookExtractor
interface.moduleProvides(IRenderedBookExtractor)

def _update_parent_pages(element, index, pagenumber):
    try:
        parent = element.parentNode
    except AttributeError:
        return

    ntiid = getattr(parent, 'ntiid', None)
    if ntiid:
        index['NTIIDs'][ntiid].append(pagenumber)
    _update_parent_pages(parent, index, pagenumber)

def _build_index(element, index, container_ntiid=None):
    """
    Recurse through the element adding realpagenumber objects to the index,
    keyed off of NTIIDs.

    :param dict index: The containing index node.
    """
    ntiid = getattr(element, 'ntiid', None)
    _container_ntiid = ntiid or container_ntiid
    _last_page_seen = None
    try:
        if index['NTIIDs'][container_ntiid]:
            _last_page_seen = index['NTIIDs'][container_ntiid][-1]
    except KeyError:
        pass

    if not ntiid:
        realpagenumber = getattr(element, 'pagenumber', None)
        if realpagenumber:
            realpagenumber = unicode(realpagenumber)
            index['real-pages'][realpagenumber] = _container_ntiid
            _update_parent_pages(element, index, realpagenumber)
    else:
        assert ntiid not in index['NTIIDs'], \
               ("NTIIDs must be unique", ntiid, index['NTIIDs'].keys())
        index['NTIIDs'][ntiid] = []
        if _last_page_seen:
            index['NTIIDs'][ntiid].append(_last_page_seen)

    __traceback_info__ = index

    for child in element.childNodes:
        if child.hasChildNodes():  # Recurse for children if needed
            _build_index(child, index, container_ntiid=_container_ntiid)

def transform(book, savetoc=True, outpath=None):
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

    arg_parser = argparse.ArgumentParser(description="Content indexer")
    arg_parser.add_argument('contentpath', help="Content book location")
    arg_parser.add_argument('-v', '--verbose', help="Be verbose", 
                            action='store_true', dest='verbose')
    args = arg_parser.parse_args()

    contentpath = os.path.expanduser(args.contentpath)
    jobname = os.path.basename(contentpath)
    contentpath = contentpath[:-1] if contentpath.endswith(os.path.sep) else contentpath
    extract(contentpath, jobname=jobname)

if __name__ == '__main__':
    main()
