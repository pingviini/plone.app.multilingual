import unittest2 as unittest
from plone.app.multilingual.testing import\
        PLONEAPPMULTILINGUAL_INTEGRATION_TESTING
from zope.component import getMultiAdapter
from zope.interface import alsoProvides

from Products.CMFCore.utils import getToolByName

from Products.LinguaPlone.tests.utils import makeContent, makeTranslation
from plone.multilingual.interfaces import ITranslationManager
from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.app.multilingual.interfaces import IPloneAppMultilingualInstalled


class migrationLPToPAM(unittest.TestCase):

    layer = PLONEAPPMULTILINGUAL_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        alsoProvides(self.request, IPloneAppMultilingualInstalled)
        language_tool = getToolByName(self.portal, 'portal_languages')
        language_tool.addSupportedLanguage('ca')
        language_tool.addSupportedLanguage('es')

    def createLinguaPloneStructure(self):
        self.folder = makeContent(self.portal, 'Folder', id='folder')
        self.folder.setLanguage('en')
        self.folder_ca = makeTranslation(self.folder, 'ca')
        self.folder_es = makeTranslation(self.folder, 'es')

        self.doc1 = makeContent(self.portal, 'Document', id='doc1')
        self.doc1.setLanguage('en')
        self.doc1_ca = makeTranslation(self.doc1, 'ca')
        self.doc1_ca.edit(title="Foo-ca", language='ca')
        self.doc1_es = makeTranslation(self.doc1, 'es')
        self.doc1_es.edit(title="Foo-es", language='es')

        self.doc2 = makeContent(self.folder, 'Document', id='doc2')
        self.doc2.setLanguage('en')
        self.doc2_ca = makeTranslation(self.doc2, 'ca')
        self.doc2_ca.edit(title="Bar-ca", language='ca')
        self.doc2_es = makeTranslation(self.doc2, 'es')
        self.doc2_es.edit(title="Bar-es", language='es')

        self.doc3 = makeContent(self.folder_ca, 'Document', id='doc3')
        self.doc3.setLanguage('ca')
        self.doc3_es = makeTranslation(self.doc3, 'es')
        self.doc3_es.edit(title="Woot", language="es")

        self.doc4 = makeContent(self.folder_es, 'Document', id='doc4')
        self.doc4.setLanguage('es')
        self.doc4_en = makeTranslation(self.doc4, 'en')
        self.doc4_en.edit(title="Woot woot", language="en")

    def testSupportedLanguages(self):
        language_tool = getToolByName(self.portal, 'portal_languages')
        self.failUnless(language_tool.getSupportedLanguages(),
                        ['en', 'ca', 'es'])

    def testMigration(self):
        self.createLinguaPloneStructure()
        migration_view = getMultiAdapter((self.portal, self.request),
                                         name='migration-view')
        migration_view()
        self.assertEqual(ITranslationManager(self.doc1).get_translations(),
                         {'ca': self.doc1_ca,
                          'en': self.doc1,
                          'es': self.doc1_es})

        self.assertEqual(ITranslationManager(self.folder).get_translations(),
                         {'ca': self.folder_ca,
                          'en': self.folder,
                          'es': self.folder_es})

        self.assertEqual(ITranslationManager(self.doc2).get_translations(),
                         {'ca': self.doc2_ca,
                          'en': self.doc2,
                          'es': self.doc2_es})

        self.assertEqual(ITranslationManager(self.doc3).get_translations(),
                         {'ca': self.doc3,
                          'es': self.doc3_es})

        self.assertEqual(ITranslationManager(self.doc4).get_translations(),
                         {'en': self.doc4_en,
                          'es': self.doc4})

    def testRelocator(self):
        self.doc5 = makeContent(self.portal, 'Document', id='doc5')
        self.doc5.setLanguage('en')
        self.doc5_ca = makeTranslation(self.doc5, 'ca')
        self.doc5_ca.edit(title="Foo", language='ca')
        self.doc5_es = makeTranslation(self.doc5, 'es')
        self.doc5_es.edit(title="Foo", language='es')
        workflowTool = getToolByName(self.portal, "portal_workflow")
        workflowTool.setDefaultChain('simple_publication_workflow')
        setupTool = SetupMultilingualSite()
        setupTool.setupSite(self.portal)

        relocator_view = getMultiAdapter((self.portal, self.request),
                                          name='relocateContentByLanguage')
        relocator_view()

        self.assertTrue(getattr(self.portal.en, 'doc5', False))
        self.assertTrue(getattr(self.portal.es, 'doc5-es', False))
        self.assertTrue(getattr(self.portal.ca, 'doc5-ca', False))
