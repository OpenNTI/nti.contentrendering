#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

import os
import sys
import time
import logging
import argparse
import functools
import subprocess

import zope.exceptions.log

from zope import component

import zope.dublincore.xmlmetadata

from plasTeX.Logging import getLogger
logger = getLogger(__name__)

from nti.contentrendering import archive
from nti.contentrendering import jsonpbuilder
from nti.contentrendering import contentchecks
from nti.contentrendering import tociconsetter
from nti.contentrendering import html5cachefile
from nti.contentrendering import ntiidlinksetter
from nti.contentrendering import contentsizesetter
from nti.contentrendering import relatedlinksetter
from nti.contentrendering import sectionvideoadder

from nti.contentrendering.interfaces import JobComponents
from nti.contentrendering.interfaces import IRenderedBookTransformer

from nti.contentrendering.RenderedBook import RenderedBook

from nti.contentrendering.render_document import parse_tex
from nti.contentrendering.render_document import resource_filename

from nti.contentrendering.resources.ResourceDB import ResourceDB
from nti.contentrendering.resources.ResourceRenderer import createResourceRenderer
from nti.contentrendering.resources.resourcetypeoverrides import ResourceTypeOverrides

from nti.contentrendering.transforms import performTransforms

DEFAULT_LOG_FORMAT = '[%(asctime)-15s] [%(name)s] %(levelname)s: %(message)s'


def configure_logging(level='INFO', fmt=DEFAULT_LOG_FORMAT):
    level = getattr(logging, level.upper(), None)
    level = logging.INFO if not isinstance(level, int) else level
    logging.basicConfig(level=level)
    logging.root.handlers[0].setFormatter(zope.exceptions.log.Formatter(fmt))
_configure_logging = configure_logging


def catching(f):
    @functools.wraps(f)
    def y():
        try:
            f()
        except subprocess.CalledProcessError as spe:
            logger.exception("Failed to run subprocess")
            sys.exit(spe.returncode)
        except:
            logger.exception("Failed to run main")
            sys.exit(1)
    return y
_catching = catching


def set_argparser():
    arg_parser = argparse.ArgumentParser(
        description="Render NextThought content.")
    arg_parser.add_argument('contentpath',
                            help="Path to top level content file.")
    arg_parser.add_argument('-c', '--config',
                            help='Used by render_content wrapper. Ignore if running '
                            'nti_render standalone.')
    arg_parser.add_argument('--nochecking',
                            action='store_true',
                            default=False,
                            help="Perform content checks.")
    arg_parser.add_argument('-o', '--outputformat',
                            default='xhtml',
                            help="Output format for rendered files. Default is xhtml")
    arg_parser.add_argument('--loglevel',
                            default='INFO',
                            help="Set logging level to INFO, DEBUG, WARNING, ERROR or "
                            "CRITICAL. Default is INFO.")
    return arg_parser
_set_argparser = set_argparser


def post_render(document,
                contentLocation='.',
                jobname='prealgebra',
                context=None,
                dochecking=True,
                docachefile=True):
    # FIXME: This was not particularly well thought out. We're using components,
    # but named utilities, not generalized adapters or subscribers.
    # That makes this not as extensible as it should be.

    # We very likely will get a book that has no pages
    # because NTIIDs are not added yet.
    start_t = time.time()
    logger.info('Creating rendered book')
    book = RenderedBook(document, contentLocation)
    elapsed = time.time() - start_t
    logger.info("Rendered book created in %s(s)", elapsed)

    # This step adds NTIIDs to the TOC in addition to modifying
    # on-disk content.
    logger.info('Adding icons to toc and pages')
    tociconsetter.transform(book, context=context)

    logger.info('Storing content height in pages')
    contentsizesetter.transform(book, context=context)

    logger.info('Adding related links to toc')
    relatedlinksetter.performTransforms(book, context=context)

    # SAJ: Disabled until we determine what thumbnails we need and how to create them
    # in a useful manner.
    # logger.info('Generating thumbnails for pages')
    # contentthumbnails.transform(book, context=context)

    # PhantomJS doesn't cope well with the iframes
    # for embedded videos: you get a black box, and we put them at the top
    # of the pages, so many thumbnails end up looking the same, and looking
    # bad. So do this after taking thumbnails.
    logger.info('Adding videos')
    sectionvideoadder.performTransforms(book, context=context)

    if dochecking:
        logger.info('Running checks on content')
        contentchecks.performChecks(book, context=context)

    contentPath = os.path.realpath(contentLocation)

    if docachefile:
        # TODO: Aren't the things in the archive mirror file the same things
        # we want to list in the manifest? If so, we should be able to combine
        # these steps (if nothing else, just list the contents of the archive to get the
        # manifest)
        logger.info("Creating html cache-manifest %s", contentPath)
        html5cachefile.main(contentPath, contentPath)

    logger.info('Changing intra-content links')
    ntiidlinksetter.transform(book)

    # In case order matters, we sort by the name of the
    # utility. To register, use patterns like 001, 002, etc.
    # Ideally order shouldn't matter, and if it does it should be
    # handled by a specialized dispatching utility.
    transformers = component.getUtilitiesFor(IRenderedBookTransformer)
    for name, extractor in sorted(transformers):
        logger.info("Extracting %s/%s", name, extractor)
        extractor.transform(book)

    logger.info("Creating JSONP content")
    jsonpbuilder.transform(book)

    logger.info("Creating an archive file")
    archive.create_archive(book, name=jobname)
postRender = post_render


def render_document(document, rname, db):
    renderer = createResourceRenderer(rname, db, unmix=False)
    renderer.render(document)
    return renderer


def to_xml(document, jobname):
    outfile = '%s.xml' % jobname
    with open(outfile, 'w') as f:
        f.write(document.toXML().encode('utf-8'))
toXml = to_xml


def write_dc_metadata(document, jobname):
    """
    Write an XML file containing the DublinCore metadata we can
    extract for this document.
    """
    mapping = {}
    metadata = document.userdata

    logger.info("Writing DublinCore Metadata.")

    if 'author' in metadata:
        # latex author and DC Creator are both arrays
        mapping['Creator'] = [x.textContent for x in metadata['author']]

    if 'title' in metadata:
        # DC Title is an array, latex title is scalar
        # Sometimes title may be a string or it may be a TeXElement, depending
        # on what packages have dorked things up
        mapping['Title'] = (getattr(metadata['title'],
                                    'textContent',
                                    metadata['title']),)

    # The 'date' command in latex is free form, which is not
    # what we want for DC...what do we want?

    # For other options, see zope.dublincore.dcterms.name_to_element
    # Publisher, in particular, would be a good one
    if not mapping:
        return

    xml_string = zope.dublincore.xmlmetadata.dumpString(mapping)
    xml_string = unicode(xml_string.decode('utf-8'))
    with open('dc_metadata.xml', 'w') as f:
        f.write(xml_string.encode('utf-8'))


def generate_images(document):
    # Generates required images ###
    # Replace this with configuration/use of ZCA?
    OVERRIDE_INDEX_NAME = getattr(ResourceTypeOverrides, 'OVERRIDE_INDEX_NAME')
    local_overrides = os.path.join(os.getcwd(), '../nti.resourceoverrides')
    if os.path.exists(os.path.join(local_overrides, OVERRIDE_INDEX_NAME)):
        overrides = local_overrides
    else:
        overrides = resource_filename(__name__, 'resourceoverrides')
    db = ResourceDB(document, overridesLocation=overrides)
    db.generateResourceSets()
    return db
generateImages = generate_images


def process_document(document, jobname, components=None,
                     out_format='xhtml', dochecking=True, db=None,
                     docachefile=True):
    if components is None:
        logger.info("Perform prerender transforms.")
        components = JobComponents(jobname)
        performTransforms(document, context=components)

    if      db is None \
        and out_format in ('images', 'xhtml', 'text'):
        logger.info("Generating images")
        db = generate_images(document)

    if out_format == 'xhtml':
        logger.info("Begin render")
        render_document(document,
                        document.config['general']['renderer'],
                        db)
        logger.info("Begin post render")
        post_render(document,
                    jobname=jobname,
                    context=components,
                    dochecking=dochecking,
                    docachefile=docachefile)
    elif out_format == 'xml':
        logger.info("To Xml.")
        to_xml(document, jobname)

    elif out_format == 'text':
        logger.info("Begin render")
        render_document(document,
                        document.config['general']['renderer'],
                        db)

    logger.info("Write metadata.")
    write_dc_metadata(document, jobname)
    return document


def render(sourceFile, provider='AOPS', out_format='xhtml', 
           nochecking=False, docachefile=True, 
           load_configs=True, set_chameleon_cache=True):
    logger.info("Start rendering for %s", sourceFile)
    start_t = time.time()
    dochecking = not nochecking
    document, components, jobname, _ = parse_tex(sourceFile,
                                                 provider=provider,
                                                 outFormat=out_format,
                                                 load_configs=load_configs,
                                                 set_chameleon_cache=set_chameleon_cache)
    process_document(document, 
                     jobname, 
                     components, 
                     out_format, 
                     dochecking=dochecking,
                     docachefile=docachefile)

    elapsed = time.time() - start_t
    logger.info("Rendering took %s(s)", elapsed)
    return document


@catching
def main():
    """
    Main program routine
    """
    argv = sys.argv[1:]
    arg_parser = set_argparser()
    args = arg_parser.parse_args(args=argv)

    configure_logging(args.loglevel)
    render(args.contentpath,
           out_format=args.outputformat,
           nochecking=args.nochecking)
