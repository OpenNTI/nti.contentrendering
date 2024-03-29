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
import glob
import codecs
import string
import datetime

import isodate

from plasTeX import Base
from plasTeX import TeXDocument

from plasTeX.Logging import getLogger
logger = getLogger(__name__)

from plasTeX.TeX import TeX

import zope.browserpage

from zope import interface

from zope.configuration import xmlconfig

from zope.location.interfaces import IContained

from z3c.autoinclude.zcml import includePluginsDirective

import nti.contentrendering

from nti.contentrendering.interfaces import JobComponents

from nti.contentrendering.plastexids import patch_all

from nti.contentrendering.transforms import performTransforms

from nti.contentrendering.utils.chameleon import setupChameleonCache

from nti.ntiids.ntiids import escape_provider

resource_filename = __import__('pkg_resources').resource_filename

out_format_to_render_name = {'xhtml': 'XHTML', 'text': 'Text'}


@interface.implementer(IContained)
class PluginPoint(object):

    __parent__ = None

    def __init__(self, name):
        self.__name__ = name
PP_CONTENT_RENDERING = PluginPoint('nti.contentrendering')


# setup id generation
patch_all()


def prepare_rendering_context(context=None):
    context = xmlconfig.file('configure.zcml',
                             package=nti.contentrendering,
                             context=context)

    # Include zope.browserpage.meta.zcml for tales:expressiontype
    # before including the products
    xmlconfig.include(context, file="meta.zcml", package=zope.browserpage)

    # include plugins
    includePluginsDirective(context, PP_CONTENT_RENDERING)
    return context


def load_packages(source_dir=None, context=None, load_configs=True):
    # Set up imports for style files. The preferred, if verbose, way is to
    # use a fully qualified Python name. But for legacy and convenience
    # reasons, we support non-qualified imports (if the module does)
    # by adding that directory directly to the path
    packages_path = os.path.join(os.path.dirname(__file__),
                                 'plastexpackages')
    if packages_path not in sys.path:
        sys.path.append(packages_path)

    # Also allow the source directory to cntain a 'plastexpackages'
    # directory. If it exists, it should be a directory containing
    # packages that are referenced by fully-qualified name
    # or possibly raw modules that are referenced by a short name;
    # note that in the module case, they won't be able to import each other.
    # Also note that the content-local `configure.zcml` file can (SHOULD) be used
    # to register IPythonPackage adapters/utilities
    if source_dir is not None:
        local_packages_path = os.path.join(source_dir,
                                           'plastexpackages')
        if local_packages_path not in sys.path:
            sys.path.append(local_packages_path)

        zope_pre_conf_name = os.path.join(source_dir,
                                          'pre_configure.zcml')
        if os.path.exists(zope_pre_conf_name):
            if context is None:
                context = xmlconfig.file(os.path.abspath(zope_pre_conf_name),
                                         package=nti.contentrendering)
            else:
                context = xmlconfig.file(os.path.abspath(zope_pre_conf_name),
                                         package=nti.contentrendering,
                                         context=context)
    if load_configs:
        context = prepare_rendering_context(context)
    return context, packages_path


def prepare_xml_context(source_file, context=None, load_configs=True):
    source_file = os.path.abspath(os.path.expanduser(source_file))
    source_dir = os.path.dirname(source_file)
    context, packages_path = load_packages(source_dir, context, load_configs)
    return source_dir, packages_path, context


def prepare_document_settings(document,
                              outFormat=u'xhtml',
                              perform_transforms=True,
                              provider=u'NTI',
                              working_dir=None,
                              specific_ntiid=None):
    # setup default config options we want
    document.config['files']['split-level'] = 1
    document.config['document']['sec-num-depth'] = 10
    document.config['document']['toc-non-files'] = True
    document.config['document']['toc-depth'] = sys.maxsize

    if outFormat and outFormat in out_format_to_render_name:
        renderer_name = out_format_to_render_name[outFormat]
        document.config['general']['renderer'] = renderer_name

    # By outputting in ASCII, we are still valid UTF-8, but we use
    # XML entities for high characters. This is more likely to survive
    # through various processing steps that may not be UTF-8 aware
    document.config['files']['output-encoding'] = 'ascii'

    document.config['general']['theme'] = 'NTIDefault'
    document.config['general']['theme-base'] = 'NTIDefault'

    # Read a config if present
    document.config.add_section('NTI')
    document.config.set('NTI',
                        'provider',
                        escape_provider(os.environ.get('NTI_PROVIDER', provider)))

    document.config.set('NTI', 'extra-scripts', '')
    document.config.set('NTI', 'extra-styles', '')
    document.config.set('NTI', 'timezone-name', 'US/Central')

    # For BWC, we need to set this to false (TODO: Can we look at file
    # dates somewhere and figure out "new" content and go to true
    # automatically for it?)
    document.config.set('NTI', 'strict-ntiids', False)

    document.userdata['working-dir'] = working_dir or os.getcwd()

    now = datetime.datetime.utcnow()
    document.userdata['generated_time'] = isodate.datetime_isoformat(now)

    # This variable contains either a time.tzname tuple or a pytz timezone
    # name
    NTI_CFG = document.config['NTI']
    document.userdata['extra_styles'] = NTI_CFG['extra-styles'].split()
    document.userdata['extra_scripts'] = NTI_CFG['extra-scripts'].split()
    document.userdata['document_timezone_name'] = NTI_CFG['timezone-name']

    document.userdata['specific_ntiid'] = specific_ntiid
    document.userdata['transform_process'] = perform_transforms
    # When changes are made to the rendering process that would impact the ability
    # of deployed code to properly consume documents, this needs to be incremented.
    # Currently it is for an entire renderable package (book) but in the future we
    # might need/want to make it per-page/per-feature (e.g., if a unit doesn't use
    # new quiz functionality, it may be compatible with older viewers)
    document.userdata['renderVersion'] = 2
    return document


def setup_environ(document, jobname, packages_path, source_dir=None):
    cwd = document.userdata['working-dir']

    # Load aux files for cross-document references
    pauxname = '%s.paux' % jobname
    for dirname in [cwd] + document.config['general']['paux-dirs']:
        for fname in glob.glob(os.path.join(dirname, '*.paux')):
            if os.path.basename(fname) == pauxname:
                continue
            document.context.restore(fname,
                                     document.config['general']['renderer'])

    # Set up TEXINPUTS to include the current directory for the renderer,
    # plus our packages directory
    if source_dir is not None:
        texinputs = (os.getcwd(),
                     source_dir,
                     packages_path,
                     os.environ.get('TEXINPUTS', ''))
        os.environ['TEXINPUTS'] = os.path.pathsep.join(texinputs)

    # Likewise for the renderers, with the addition of the legacy 'zpts' directory.
    # Parts of the code (notably tex2html._find_theme_mathjaxconfig) depend on
    # the local Template being first. Note that earlier values will take precedence
    # over later values.
    xhtmltemplates = (os.path.join(os.getcwd(), 'Templates'),
                      packages_path,
                      resource_filename(__name__, 'zpts'),
                      os.environ.get('XHTMLTEMPLATES', ''))
    os.environ['XHTMLTEMPLATES'] = os.path.pathsep.join(xhtmltemplates)


def parse_tex(sourceFile,
              outFormat=u'xhtml',
              provider=u'NTI',
              outdir=None,
              load_configs=True,
              perform_transforms=True,
              set_chameleon_cache=True,
              xml_conf_context=None,
              encoding='utf-8'):

    source_dir, packages_path, xml_conf_context = \
        prepare_xml_context(sourceFile, xml_conf_context, load_configs)

    # Create document instance that output will be put into
    document = TeXDocument()

    # Certain things like to assume that the root document is called index.html. Make it so.
    # This is actually plasTeX.Base.LaTeX.Document.document, but games are played
    # with imports. damn it (html suffix added automatically).
    Base.document.filenameoverride = property(lambda unused: 'index')

    prepare_document_settings(document,
                              outFormat,
                              provider=provider)

    conf_name = os.path.join(source_dir, "nti_render_conf.ini")
    document.config.read((conf_name,))

    # Configure components and utilities
    zope_conf_name = os.path.join(source_dir, 'configure.zcml')
    if load_configs and os.path.exists(zope_conf_name):
        xml_conf_context = xmlconfig.file(os.path.abspath(zope_conf_name),
                                          package=nti.contentrendering,
                                          context=xml_conf_context)

    # Instantiate the TeX processor
    fp = codecs.open(sourceFile, 'r', encoding, 'replace')
    tex = TeX(document, file=fp)

    # Populate variables for use later
    jobname = tex.jobname
    document.userdata['specific_ntiid'] = document.userdata['jobname'] = jobname

    # Create a component lookup ("site manager") that will
    # look for components named for the job implicitly
    # TODO: Consider installing hooks and using 'with site()' for this?
    components = JobComponents(jobname)

    setup_environ(document, jobname, packages_path, source_dir)

    if set_chameleon_cache:
        setupChameleonCache(config=True)

    # Parse the document
    logger.info("Tex Parsing %s", sourceFile)
    tex.parse()

    # Change to specified directory to output to
    outdir = outdir or document.config['files']['directory']
    if outdir:
        outdir = string.Template(outdir).substitute({'jobname': jobname})
        outdir = os.path.expanduser(outdir)
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        logger.info('Directing output files to directory: %s.', outdir)
        os.chdir(outdir)

    # Perform prerender transforms
    if perform_transforms:
        logger.info("Perform prerender transforms.")
        performTransforms(document, context=components)

    return document, components, jobname, outdir
