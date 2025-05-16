import unittest
import tempfile
import os
import shutil
import copy

from mkdocs_protobuf_plugin.plugin import ProtobufPlugin
from mkdocs_protobuf_plugin.i18n_support import I18nSupport


class TestI18nSupport(unittest.TestCase):
    """Test the i18n compatibility features."""

    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Initialize plugin
        self.plugin = ProtobufPlugin()

        # Create a sample MkDocs config with i18n plugin
        self.mkdocs_config = {
            'docs_dir': os.path.join(self.temp_dir, "docs"),
            'plugins': [
                'search',
                {
                    'i18n': {
                        'default_language': 'en',
                        'languages': {
                            'en': 'English',
                            'fr': 'Français',
                            'es': 'Español'
                        },
                        'nav_translations': {
                            'fr': {
                                'API Reference': 'Référence d\'API'
                            },
                            'es': {
                                'API Reference': 'Referencia de API'
                            }
                        }
                    }
                }
            ],
            'nav': []
        }

    def tearDown(self):
        # Clean up
        shutil.rmtree(self.temp_dir)

    def test_i18n_plugin_detection(self):
        """Test that the i18n plugin is correctly detected."""
        is_active = I18nSupport.is_i18n_active(self.mkdocs_config)
        self.assertTrue(is_active, "i18n plugin should be detected as active")

        # Test with config without i18n
        config_no_i18n = copy.deepcopy(self.mkdocs_config)
        config_no_i18n['plugins'] = ['search']
        self.assertFalse(
            I18nSupport.is_i18n_active(config_no_i18n),
            "i18n plugin should be detected as inactive"
        )

    def test_language_extraction(self):
        """Test that languages are correctly extracted from the config."""
        languages = I18nSupport.get_languages(self.mkdocs_config)
        self.assertEqual(len(languages), 3, "Should extract 3 languages")
        self.assertIn('en', languages)
        self.assertIn('fr', languages)
        self.assertIn('es', languages)

    def test_default_language_extraction(self):
        """Test that the default language is correctly extracted."""
        default_lang = I18nSupport.get_default_language(self.mkdocs_config)
        self.assertEqual(default_lang, 'en', "Should extract 'en' as default language")

    def test_i18n_navigation_update(self):
        """Test that navigation is correctly updated for a specific language."""
        nav = []
        lang = 'fr'
        nav_tree = [
            {'Overview': 'api/index.md'},
            {'User': 'api/user.md'}
        ]

        # Update the navigation for the language
        I18nSupport.update_i18n_navigation(nav, lang, nav_tree)

        # Check that the language entry was created
        self.assertEqual(len(nav), 1)
        self.assertIn(lang, nav[0])

        # Check that the API Reference was added
        lang_nav = nav[0][lang]
        self.assertEqual(len(lang_nav), 1)
        self.assertIn('API Reference', lang_nav[0])

        # Check that the nav tree was correctly added
        api_ref = lang_nav[0]['API Reference']
        self.assertEqual(api_ref, nav_tree)

    def test_i18n_auto_detection(self):
        """Test that i18n support is automatically detected and used."""
        # Configure the plugin with just output_dir
        self.plugin.config = {
            'output_dir': 'api'
        }

        # Create a simple navigation tree and files list
        nav = []
        generated_files = [
            os.path.join(self.temp_dir, 'docs/en/api/test.md'),
            os.path.join(self.temp_dir, 'docs/fr/api/test.md')
        ]

        # Create necessary directories
        os.makedirs(os.path.join(self.temp_dir, 'docs/en/api'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'docs/fr/api'), exist_ok=True)

        # Create empty test files
        for file_path in generated_files:
            with open(file_path, 'w') as f:
                f.write('# Test API')

        # Mock the _are_files_in_nav method to return False so _update_navigation will proceed
        self.plugin._are_files_in_nav = lambda nav, generated_files, docs_dir: False

        # Mock _build_nav_tree to return a simple nav tree
        self.plugin._build_nav_tree = lambda file_paths: [{'Test': file_paths[0]}]

        # Call _update_navigation
        config = copy.deepcopy(self.mkdocs_config)
        config['nav'] = nav
        self.plugin._update_navigation(config, 'api', generated_files)

        # Verify that the nav was updated with i18n structure
        self.assertTrue(len(config['nav']) > 0, "Navigation should be updated")

        # Test with a config that doesn't have i18n
        config_no_i18n = {
            'docs_dir': os.path.join(self.temp_dir, "docs"),
            'plugins': ['search'],
            'nav': []
        }

        # Reset nav
        nav = []

        # Call _update_navigation again with non-i18n config
        config_no_i18n['nav'] = nav
        self.plugin._update_navigation(config_no_i18n, 'api', generated_files)

        # Verify that the nav was updated with regular structure
        self.assertTrue(len(config_no_i18n['nav']) > 0, "Navigation should be updated")


if __name__ == "__main__":
    unittest.main()
