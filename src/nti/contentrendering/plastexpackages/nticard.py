#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import urlparse
from hashlib import md5

import requests

from zope import interface

from zope.cachedescriptors.property import readproperty

from plasTeX import Base
from plasTeX import Command

from plone.namedfile import NamedImage

from nti.contentprocessing.interfaces import IContentMetadata

from nti.contentprocessing.metadata_extractors import get_metadata_from_content_location

from nti.contentrendering.contentthumbnails import create_thumbnail_of_pdf

from nti.contentrendering.interfaces import IEmbeddedContainer

from nti.contentrendering.plastexids import NTIIDMixin

from nti.contentrendering.plastexpackages._util import LocalContentMixin
from nti.contentrendering.plastexpackages._util import incoming_sources_as_plain_text

from nti.contentrendering.plastexpackages.graphics import _locate_image_file

from nti.contentrendering.plastexpackages.graphicx import includegraphics

from nti.ntiids.ntiids import TYPE_UUID
from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import is_valid_ntiid_string


class _Image(object):

    __slots__ = (b'image',)

    def __init__(self, image):
        self.image = image


class _Dimen(object):

    __slots__ = (b'px',)

    def __init__(self, px):
        self.px = px


def process_remote_data(self, url, data):
    # get file info
    filename = urlparse.urlparse(url).path.split('/')[-1]
    named_image = NamedImage(data=data,
                             filename=filename)
    width, height = named_image.getImageSize()
    # save it
    self.image = _Image(named_image)
    self.image.image.url = url
    self.image.image.width = _Dimen(width)
    self.image.image.height = _Dimen(height)
    return self


def process_remote_image(self, url):
    response = requests.get(url)
    return process_remote_data(self,
                               url=url,
                               data=response.content)


class nticardname(Command):
    pass


@interface.implementer(IEmbeddedContainer)
class nticard(LocalContentMixin, Base.Float, NTIIDMixin):
    """
    Implementation of the Card environment. There should be an ``includegraphics`` specifying
    a thumbnail as a child of this node (unless ``auto`` is used). The text contents of this
    node will form the card description.

    .. note::
            This environment is **NOT** intended for subclassing.

    Possible options include:

    creator
            The creator of the content

    auto
            If present and "true", then we will attempt to spider the ``href``
            to extract Twitter card or `Facebook OpenGraph <http://opengraphprotocol.org>`_
            data from it; this allows you to skip specifying an image and description.
    """
    args = 'href:str:source <options:dict>'

    # Note the options dict is in <>, and uses the default comma separator, which means
    # values cannot have commas (that's why href, which may be an NTIID is its own argument).
    # See also ntiassessment.naqsolution.

    #: A Float subclass to get \caption handling
    class caption(Base.Floats.Caption):
        counter = 'figure'

    # Only classes with counters can be labeled, and \label sets the
    # id property, which in turn is used as part of the NTIID (when no NTIID
    # is set explicitly)
    counter = 'nticard'

    _ntiid_type = 'NTICard'
    _ntiid_suffix = 'nticard.'

    # Use our counter to generate IDs if no ID is given
    _ntiid_title_attr_name = 'ref'
    _ntiid_allow_missing_title = False
    _ntiid_cache_map_name = '_nticard_ntiid_map'

    #: From IEmbeddedContainer
    mimeType = "application/vnd.nextthought.nticard"

    href = None
    image = None
    creator = None
    type = 'summary'

    blockType = True

    _href_override = None

    #: Derived from the href property. If the href itself specifies
    #: a complete NTIID, then it will have that value. Otherwise,
    #: one will be computed from the href; if the href is a absolute
    #: URL, then the computed NTIID will be the same whereever the URL
    #: is linked to, allowing this NTIID to be used as a ``containerId``
    target_ntiid = None

    # invoke method

    def _pdf_to_thumbnail(self, pdf_path, page=1, height=792, width=612):
        return create_thumbnail_of_pdf(pdf_path,
                                       page=page,
                                       height=height,
                                       width=width)

    def auto_populate(self):
        real_href = self._href_override or self.href
        metadata = get_metadata_from_content_location(real_href)
        if not IContentMetadata.providedBy(metadata):
            return False

        self.title = metadata.title or self.title
        self.creator = metadata.creator or self.creator
        self.href = metadata.contentLocation or self.href
        self.description = metadata.description or self.description

        if metadata.contentMimeType == 'application/pdf':
            # Generate and use the real thing
            thumb_file = self._pdf_to_thumbnail(metadata.sourcePath)
            include = includegraphics()
            include.style['width'] = "93px"
            include.style['height'] = "120px"
            include.attributes['file'] = thumb_file
            include.argSource = r'[width=93pt,height=120pt]{%s}' % thumb_file
            self.appendChild(include)
        elif     metadata.images \
            and (metadata.images[0].width and metadata.images[0].height):
            # Yay, got the real size already
            self.image = _Image(metadata.images[0])
        elif metadata.images:
            # Download and save the image?
            # Right now we are downloading it for size purposes (which may not be
            # needed) but we could choose to cache it locally

            # Get filename and url
            val = metadata.images[0].url
            process_remote_image(self, val)

        return True
    _auto_populate = auto_populate

    def proces_local_href(self, tex=None):
        # Resolve local files to full paths with the same algorithm that
        # includegraphics uses
        if (    'href' in self.attributes
            and '//' not in self.attributes['href']  # not a HTTP[S] url
            and not self.attributes['href'].startswith('tag:')):  # not an NTIID

            the_file = _locate_image_file(self, tex,
                                          self.attributes['href'],
                                          includegraphics.packageName,
                                          [],
                                          # No extensions to search: must be
                                          # complete filename or path
                                          query_extensions=False)
            if the_file:
                self._href_override = the_file
                return True
        return False

    def invoke(self, tex):
        res = super(nticard, self).invoke(tex)
        self.proces_local_href(tex)
        return res

    # digest methods

    def process_target_ntiid(self):
        if is_valid_ntiid_string(self.href):
            self.target_ntiid = self.href
        else:
            # TODO: Hmm, what to use as the provider?
            # Look for a hostname in the URL?
            self.target_ntiid = make_ntiid(provider='NTI',
                                           nttype=TYPE_UUID,
                                           specific=md5(self.href).hexdigest())

    def process_digest(self):
        options = self.attributes.get('options', {}) or {}
        __traceback_info__ = options, self.attributes

        if 'href' not in self.attributes or not self.attributes['href']:
            raise ValueError("Must provide href argument")
        self.href = self.attributes['href']

        if 'auto' in options and options['auto'].lower() == 'true':
            self.auto_populate()

        if not getattr(self, 'title', ''):
            raise ValueError("Must specify a title using \\caption")

        self.attributes['nti-requirements'] = u''
        requirements = options.get('nti-requirements', u'').split()
        for requirement in requirements:
            if requirement == u'flash':
                requirement = u'mime-type:application/x-shockwave-flash'
            value = self.attributes['nti-requirements']
            self.attributes['nti-requirements'] = ' '.join([value, requirement])

        self.attributes['nti-requirements'] = self.attributes['nti-requirements'].strip()
        if self.attributes['nti-requirements'] == u'':
            self.attributes['nti-requirements'] = None

        if 'creator' in options:
            self.creator = options['creator']

        images = self.getElementsByTagName('includegraphics')
        if images:
            # Must leave the image in the dom so it can be found by the resourceDB
            # images[0].parentNode.removeChild( images[0] )
            self.image = images[0]

        self.process_target_ntiid()

    def digest(self, tokens):
        res = super(nticard, self).digest(tokens)
        if self.macroMode == self.MODE_BEGIN:
            self.process_digest()
        return res

    @readproperty
    def description(self):
        texts = []
        for child in self.allChildNodes:
            # extract the text children, ignoring the caption and label, etc
            if      child.nodeType == self.TEXT_NODE \
                    and (child.parentNode == self or child.parentNode.nodeName == 'par'):
                texts.append(unicode(child))
        return incoming_sources_as_plain_text(texts)
