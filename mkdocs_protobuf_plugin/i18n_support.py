"""
MkDocs Protobuf Plugin - i18n Support

This module provides compatibility with the mkdocs-static-i18n plugin.
"""
import logging
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import PluginCollection
from typing import Optional, Any, Union

# Set up logging
log = logging.getLogger("mkdocs.plugins.protobuf.i18n")


class I18nSupport:
    """Support for the mkdocs-static-i18n plugin."""

    @staticmethod
    def is_i18n_active(config: MkDocsConfig) -> bool:
        """Check if mkdocs-static-i18n plugin is active in the MkDocs configuration."""
        plugins = config.plugins
        if isinstance(plugins, list):
            return any(p == "i18n" or (isinstance(p, dict) and "i18n" in p) for p in plugins)
        return "i18n" in plugins

    @staticmethod
    def get_languages(config: MkDocsConfig) -> list[str]:
        """Extract configured languages from mkdocs-static-i18n configuration."""
        plugins: PluginCollection = config.plugins
        i18n_config: dict[str, Any] = None

        # Extract i18n plugin config based on its structure
        if isinstance(plugins, list):
            for p in plugins:
                if isinstance(p, dict) and "i18n" in p:
                    i18n_config = p["i18n"]
                    break
        elif "i18n" in plugins:
            i18n_config = plugins["i18n"]

        if not i18n_config:
            return []

        # Get languages from config
        if isinstance(languages, list):
            return [lang.get("locale") if isinstance(lang, dict) else lang for lang in languages]
        return list(languages.keys()) if isinstance(languages, dict) else []

    @staticmethod
    def get_default_language(config):
        """Get default language from mkdocs-static-i18n configuration."""
        plugins = config.get("plugins", {})
        i18n_config = None

        # Extract i18n plugin config
        if isinstance(plugins, list):
            for p in plugins:
                if isinstance(p, dict) and "i18n" in p:
                    i18n_config = p["i18n"]
                    break
        elif "i18n" in plugins:
            i18n_config = plugins["i18n"]

        if not i18n_config:
            return None

        return i18n_config.get("default_language")

    @staticmethod
    def update_i18n_navigation(nav, lang, nav_tree):
        """Update or create a language-specific API Reference in the navigation."""
        # Look for a language section in the navigation
        lang_entry = None
        for i, entry in enumerate(nav):
            if isinstance(entry, dict) and lang in entry:
                lang_entry = i
                break

        if lang_entry is not None:
            # Language section exists, update it
            lang_nav = nav[lang_entry][lang]
            api_entry = None

            if isinstance(lang_nav, list):
                for i, entry in enumerate(lang_nav):
                    if isinstance(entry, dict) and "API Reference" in entry:
                        api_entry = i
                        break

            if api_entry is not None:
                # Update existing API Reference
                lang_nav[api_entry]["API Reference"] = nav_tree
            else:
                # Add API Reference to language section
                if isinstance(lang_nav, list):
                    lang_nav.append({"API Reference": nav_tree})
                else:
                    nav[lang_entry][lang] = [{"API Reference": nav_tree}]
        else:
            # Create a new language section with API Reference
            nav.append({lang: [{"API Reference": nav_tree}]})

    @staticmethod
    def build_i18n_nav_tree(file_paths, languages):
        """Build navigation trees for each language."""
        lang_trees = {}

        # Group files by language
        for lang in languages:
            lang_prefix = f"{lang}/"
            # Filter files for this language
            lang_files = [f for f in file_paths if f.startswith(lang_prefix)]
            if lang_files:
                # Strip the language prefix for tree building
                stripped_files = [f[len(lang_prefix):] for f in lang_files]
                lang_trees[lang] = stripped_files

        return lang_trees
