#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.schema import Int
from zope.schema import Object
from zope.schema import Iterable
from zope.schema import TextLine


class IEclipseMiniDomTOC(interface.Interface):
    """
    Represents the 'eclipse-toc' in a :mod:`xml.dom.minidom` format.
    """

    filename = TextLine(title="The location on disk of the "
                        "eclipse-toc.xml file.")

    dom = interface.Attribute("The minidom representing the parsed contents "
                              "of the file.")

    def save():
        """
        Causes the in-memory contents of the `dom` to be written to disk.
        """


class IEclipseMiniDomTopic(interface.Interface):
    """
    Represents a `topic` element from the table-of-contents.
    """

    ordinal = Int(title="The number (starting at 1) representing which "
                        "nth child of the parent I am.")

    childTopics = Iterable(title="All the child topics of this topic.")

    dom = interface.Attribute('The :class:`pyquery.pyquery.PyQuery` object representing the '
                              'HTML contents. Will be None if not parsable')

    ntiid = TextLine(title='The NTIID of this content')

    def write_dom(force=False):
        """
        Causes the in-memory `dom` to be written to disk at the file it was read from.
        """


class IRenderedBook(interface.Interface):

    document = interface.Attribute("The plasTeX Document object used to create "
                                   "the rendering.")

    contentLocation = TextLine(title=u"The location of the directory on disk "
                                     "containing the content")

    toc = Object(IEclipseMiniDomTOC,
                 title="The shared in-memory TOC for this book.")

    jobname = TextLine(title="The name of the rendering job that produced this book, "
                             "or the empty string.",
                       default='')

    tocFile = TextLine(title=u"The location of the eclipse toc file")


class IIconFinder(interface.Interface):
    """
    Something that can find an icon for a topic in a rendered book.
    """

    def find_icon():
        """
        :return: A URL path relative to the content location giving
                an icon, or None if there is no icon.
        """


class IBackgroundImageFinder(interface.Interface):
    """
    Something that can find a background image for a topic in a rendered book.
    """

    def find_background_image():
        """
        :return: A URL path relative to the content location giving
                an image, or None if there is no icon.
        """


class IDocumentTransformer(interface.Interface):
    """
    Given a plasTeX DOM document, mutate the document
    in place to achieve some specified end. IDocumentTransformer
    *should* perform an idempotent transformation.
    """

    def transform(document):
        """
        Perform the document transformation.
        """


class IRenderedBookTransformer(interface.Interface):
    """
    Given a :class:`IRenderedBook`, mutate its on-disk state
    to achieve some specified end. This *should* be idempotent.
    """

    def transform(book):
        """
        Perform the book transformation.

        :param book: The :class:`IRenderedBook`.
        """


class IRenderedBookValidator(interface.Interface):
    """
    Given a rendered book, check that its in-memory and on
    disk state meets some criteria. At this time, this interface
    does not define what happens if that is not true.
    """

    def check(book):
        """
        Check the book's adherence to the rule of this interface.

        :return: Undefined.
        """


class IRenderedBookArchiver(interface.Interface):
    """
    Given a :class:`IRenderedBook`, it creates an offline archive.
    """

    def archive(book, out_dir=None, verbose=False):
        """
        Perform the book archiving.

        :param book: The :class:`IRenderedBook`.
        :param out_dir: The output directory
        :param verbose: Verbose mode
        """


class IStaticRelatedItemsAdder(IRenderedBookTransformer):
    """
    Transforms the book's TOC by adding related items mined from
    the book.
    """


class IVideoAdder(IRenderedBookTransformer):
    """
    Transforms the contents of the book by adding videos.
    """


class IStaticVideoAdder(IVideoAdder):
    """
    Adds videos using static information.
    """


class IStaticYouTubeEmbedVideoAdder(IStaticVideoAdder):
    """
    Uses static information to add embedded YouTube video references to the book content.
    """

# Embedded subcontainers


try:
    from plasTeX.interfaces import IEmbeddedContainer as _IEmbeddedContainerBase
except ImportError:
    # Old plasTeX version
    from zope.mimetype.interfaces import IContentTypeAware as _IEmbeddedContainerBase


class IEmbeddedContainer(_IEmbeddedContainerBase):
    """
    Intended to be implemented (or adapted from) nodes in the plasTeX
    DOM tree, this object represents a portion of content, embedded
    in other content, that should function as its own user-generated
    data container. Typically these will be rendered in HTML with ``<object>``
    tags, and the attributes declared in this interface will be
    echoed in the rendered version.

    We inherit a ``mimeType`` attribute from our parent interface; this
    should be the ``mimeType`` of the container being pointed to.

    We add a stricter definition of the ntiid attribute.
    """

    ntiid = TextLine(title="The NTIID of the embedded container itself.")

# Extractors


class IRenderedBookExtractor(IRenderedBookTransformer):

    def transform(book, savetoc=True, outpath=None):
        pass


class INTIMediaExtractor(IRenderedBookExtractor):
    """
    marker interface for NTI media elements
    """


class INTIVideoExtractor(INTIMediaExtractor):
    """
    Looks through the rendered book and extracts NTIVideos.
    """


class INTIAudioExtractor(INTIMediaExtractor):
    """
    Looks through the rendered book and extracts NTIAudios.
    """


class ICourseExtractor(IRenderedBookExtractor):
    """
    Looks through the rendered book and extracts course information.
    """


class IContentUnitStatistics(IRenderedBookExtractor):
    """
    Looks through the rendered book and extracts content unit statistics.
    """


class IConceptsExtractor(IRenderedBookExtractor):
    """
    Looks through the rendered book and extracts concepts tree.
    """


class IRelatedWorkExtractor(IRenderedBookExtractor):
    """
    Looks through the rendered book and extracts related work information.
    """


class IDiscussionExtractor(IRenderedBookExtractor):
    """
    Looks through the rendered book and extracts discussions.
    """


class ISlideDeckExtractor(IRenderedBookExtractor):
    """
    Looks through the rendered book and extracts slide decks.
    """


class ITimelineExtractor(IRenderedBookExtractor):
    """
    Looks through the rendered book and extracts timelime information.
    """


class IJSONTransformer(interface.Interface):
    """
    Given a :class:`plasTeX.Node`, create a JSON serializable dictionary.
    """

    def transform(*args, **kwargs):
        pass


from zope.component import getGlobalSiteManager

from zope.interface.registry import Components


class JobComponents(Components):
    """
    A component registry (IComponentLookup) that automatically attempts to
    find things using the current job name first when no name is given.

    TODO: In the future, this might also consider the provider.

    """

    def __init__(self, jobname=None, **kwargs):
        self._jobname = jobname
        assert self._jobname
        super(JobComponents, self).__init__(**kwargs)
        if not self.__bases__:
            self.__bases__ = (getGlobalSiteManager(),)

    # TODO: Could probably do some meta programming and avoid duplicating the
    # similar patterns
    def queryUtility(self, provided, name='', default=None):
        result = default
        if name == '':
            result = super(JobComponents, self).queryUtility(provided,
                                                             self._jobname,
                                                             default=default)
            if result is not default:
                return result

        return super(JobComponents, self).queryUtility(provided,
                                                       name=name,
                                                       default=default)

    def queryAdapter(self, obj, interface, name='', default=None):
        result = default
        if name == '':
            result = super(JobComponents, self).queryAdapter(obj,
                                                             interface,
                                                             name=self._jobname,
                                                             default=default)
            if result is not default:
                return result
        return super(JobComponents, self).queryAdapter(obj,
                                                       interface,
                                                       name=name,
                                                       default=default)

    def queryMultiAdapter(self, objects, interface, name='', default=None):
        result = default
        if name == '':
            result = super(JobComponents, self).queryMultiAdapter(objects,
                                                                  interface,
                                                                  name=self._jobname,
                                                                  default=default)
            if result is not default:
                return result
        return super(JobComponents, self).queryMultiAdapter(objects,
                                                            interface,
                                                            name=name,
                                                            default=default)
