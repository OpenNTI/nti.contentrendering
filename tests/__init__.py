import unittest
import nti.contentrendering

from pyramid.testing import setUp as psetUp
from pyramid.testing import tearDown as ptearDown
from pyramid.testing import DummyRequest

from zope.configuration import xmlconfig
import zope.component

class ConfiguringTestBase(unittest.TestCase):

	def setUp( self ):
		psetUp(request=DummyRequest())
		# Notice that the pyramid testing setup
		# FAILS to make the sitemanager a child of the global sitemanager.
		# this breaks the zope component APIs in many bad ways
		zope.component.getSiteManager().__bases__ = (zope.component.getGlobalSiteManager(),)
		#xmlconfig.XMLConfig( 'configure.zcml', module=dataserver )()
		xmlconfig.file( 'configure.zcml', package=nti.contentrendering )




	def tearDown( self ):
		ptearDown()
