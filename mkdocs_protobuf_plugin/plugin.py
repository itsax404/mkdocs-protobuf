import os
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mkdocs.plugins import BasePlugin
from mkdocs.config.config_options import Type
from mkdocs.config.defaults import MkDocsConfig

from .converter import ProtoToMarkdownConverter
from .file_cache import ProtoFileCache
from .i18n_support import I18nSupport

log = logging.getLogger("mkdocs.plugins.protobuf")


class ProtoFileEventHandler(FileSystemEventHandler):
    def __init__(self, converter: ProtoToMarkdownConverter, proto_paths: list[str], proto_dirs: list[str],
                 output_dir: str, config: MkDocsConfig, plugin: "ProtobufPlugin"):
        self.converter = converter
        self.proto_paths = proto_paths
        self.proto_dirs = proto_dirs
        self.output_dir = output_dir
        self.config = config
        self.plugin = plugin

    def __process_proto_file__(self, file_path: str):
        """Process a single proto file if it's within our watched paths"""
        abs_path = str(Path(file_path).absolute())

        # Check if the file is in one of our watched paths
        in_watched_path = False
        for proto_path in self.proto_paths:
            abs_proto_path = os.path.abspath(proto_path)
            try:
                if os.path.commonpath([abs_proto_path, abs_path]) == abs_proto_path:
                    in_watched_path = True
                    break
            except ValueError:
                continue

        if in_watched_path:
            # Check if this is an output directory file
            output_path = os.path.abspath(self.output_dir)
            try:
                if os.path.commonpath([output_path, abs_path]) == output_path:
                    log.debug(f"Ignoring file in output directory: {file_path}")
                    return False
            except ValueError:
                pass

            # Check if the file has changed since last processing
            if not self.plugin.file_cache.is_file_changed(abs_path):
                log.debug(f"Skipping unchanged proto file: {file_path}")
                return False

            log.info(f"Processing proto file: {file_path}")
            generated_files = self.converter.convert_proto_files(
                [abs_path], self.output_dir
            )

            # Update the file hash in the cache
            self.plugin.file_cache.update_file_hash(abs_path)

            # Update the navigation with the new files
            self.plugin.update_navigation(
                self.config, self.output_dir, generated_files
            )
            return True
        return False

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".proto"):
            # Skip files in the output directory
            output_path = os.path.abspath(self.output_dir)
            abs_event_path = os.path.abspath(event.src_path)

            try:
                if os.path.commonpath([output_path, abs_event_path]) == output_path:
                    log.debug(
                        f"Ignoring modified file in output directory: {event.src_path}"
                    )
                    return
            except ValueError:
                pass

            # Check if file has actually changed (using the cache)
            if not self.plugin.file_cache.is_file_changed(abs_event_path):
                log.debug(f"File content unchanged, skipping: {event.src_path}")
                return

            self._process_proto_file(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".proto"):
            # Skip files in the output directory
            output_path = os.path.abspath(self.output_dir)
            abs_event_path = os.path.abspath(event.src_path)

            try:
                if os.path.commonpath([output_path, abs_event_path]) == output_path:
                    log.debug(
                        f"Ignoring created file in output directory: {event.src_path}"
                    )
                    return
            except ValueError:
                pass

            self._process_proto_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith(".proto"):
            # Find the corresponding markdown file and delete it
            abs_path = str(Path(event.src_path).absolute())
            for proto_dir in self.proto_dirs:
                try:
                    abs_proto_dir = os.path.abspath(proto_dir)
                    if os.path.commonpath([abs_proto_dir, abs_path]) == abs_proto_dir:
                        rel_path = os.path.relpath(abs_path, abs_proto_dir)
                        md_file = os.path.join(
                            self.output_dir, os.path.splitext(rel_path)[0] + ".md"
                        )
                        if os.path.exists(md_file):
                            log.info(
                                f"Deleting markdown file for removed proto: {md_file}"
                            )
                            os.remove(md_file)
                            break
                except (ValueError, OSError) as e:
                    log.warning(f"Error handling deleted proto file: {str(e)}")

            # Re-process all proto files to update navigation
            proto_files = []
            for proto_path in self.proto_paths:
                abs_path = os.path.abspath(proto_path)
                if os.path.isdir(abs_path):
                    for root, _, files in os.walk(abs_path):
                        for file in files:
                            if file.endswith(".proto"):
                                proto_files.append(os.path.join(root, file))
                elif os.path.isfile(abs_path) and abs_path.endswith(".proto"):
                    proto_files.append(abs_path)

            generated_files = self.converter.convert_proto_files(
                proto_files, self.output_dir
            )
            self.plugin._update_navigation(
                self.config, self.output_dir, generated_files
            )


class ProtobufPlugin(BasePlugin):
    config_scheme = (
        ("proto_paths", Type(list, default=[])),
        ("output_dir", Type(str, default="docs/generated")),
    )

    def __init__(self):
        self.observer = None
        self.watch_handlers = []
        self.proto_dirs: list[str] = []
        self.converter = ProtoToMarkdownConverter(self.proto_dirs)
        self.file_cache = ProtoFileCache()

    def on_config(self, config: MkDocsConfig):
        """
        Process the proto_paths from the config and convert the proto files
        """
        # Get the absolute path to proto files
        proto_paths = self.config.get("proto_paths", [])
        output_dir = self.config.get("output_dir", "docs/generated")

        # Make sure output directory exists
        output_path = os.path.join(config["docs_dir"], output_dir)
        os.makedirs(output_path, exist_ok=True)

        # Store directory paths for directory structure preservation
        self.proto_dirs = [path for path in proto_paths if os.path.isdir(path)]

        # Share proto_dirs with the converter
        self.converter.proto_dirs = self.proto_dirs

        # Convert all proto files at startup
        generated_files = self.__process_proto_files__(proto_paths, output_path)

        # Update navigation if needed
        self._update_navigation(config, output_dir, generated_files)

        # Return the config
        return config

    def on_serve(self, server, config, **kwargs):
        """
        Start watching proto files for changes when in serve mode
        """
        proto_paths = self.config.get("proto_paths", [])
        output_dir = os.path.join(
            config["docs_dir"], self.config.get("output_dir", "docs/generated")
        )

        # Get absolute path to docs directory to filter events
        docs_dir_abs = os.path.abspath(config["docs_dir"])

        # Create file system observer
        self.observer = Observer()

        # Add watchers for each proto path
        for path in proto_paths:
            abs_path = os.path.abspath(path)

            # Skip paths that are inside or overlap with the docs directory to prevent infinite rebuild
            try:
                if os.path.exists(abs_path) and not (
                    os.path.commonpath([abs_path, docs_dir_abs])
                    in [abs_path, docs_dir_abs]
                ):
                    event_handler = ProtoFileEventHandler(
                        self.converter,
                        proto_paths,
                        self.proto_dirs,
                        output_dir,
                        config,
                        self,
                    )
                    self.observer.schedule(event_handler, abs_path, recursive=True)
                    self.watch_handlers.append(event_handler)
                    log.info(f"Watching proto files in: {abs_path}")
                else:
                    log.warning(
                        f"Skipping proto path that overlaps with docs directory: {abs_path}"
                    )
            except (ValueError, OSError) as e:
                log.warning(f"Error setting up watch for path {abs_path}: {str(e)}")

        # Start the observer
        self.observer.start()

        return server

    def __update_navigation__(self, config, output_dir, generated_files):
        """
        Update the MkDocs navigation configuration to include generated markdown files
        """
        # If there are no nav entries or no generated files, nothing to do
        if not generated_files or "nav" not in config:
            return

        # Check if we have manually defined all API files in the nav
        # If all generated files are already covered by the nav, we don't need to update it
        if self._are_files_in_nav(config["nav"], generated_files, config["docs_dir"]):
            log.info("All API files are already in the navigation, not updating nav")
            return

        # Check if i18n plugin is active
        is_i18n_active = I18nSupport.is_i18n_active(config)
        languages = I18nSupport.get_languages(config) if is_i18n_active else []

        # Convert paths to be relative to docs_dir
        docs_dir = config["docs_dir"]
        rel_files = []
        for file_path in generated_files:
            if os.path.isabs(file_path):
                try:
                    rel_path = os.path.relpath(file_path, docs_dir)
                    rel_files.append(rel_path)
                except ValueError:
                    # Skip files that can't be made relative to docs_dir
                    log.warning(
                        f"Could not make path relative to docs_dir: {file_path}"
                    )
            else:
                rel_files.append(file_path)

        # Handle navigation based on whether i18n is active
        if is_i18n_active and languages:
            # For i18n, we need to organize files by language
            lang_file_groups = {}
            for lang in languages:
                lang_prefix = f"{lang}/"
                # Files for this language (starting with lang prefix)
                lang_files = [f for f in rel_files if f.startswith(lang_prefix)]

                if lang_files:
                    # Strip language prefix for nav tree building
                    stripped_files = [f[len(lang_prefix):] for f in lang_files]
                    lang_file_groups[lang] = stripped_files

            # Process each language separately
            for lang, lang_files in lang_file_groups.items():
                # Build navigation tree for this language
                lang_nav_tree = self._build_nav_tree(lang_files)

                # Update language-specific navigation
                self._update_lang_nav(config["nav"], lang, lang_nav_tree, output_dir)
        else:
            # Regular (non-i18n) navigation handling
            # Build a navigation tree
            api_nav = self._build_nav_tree(rel_files)

            # Check if we need to create a default nav
            if "nav" not in config or not config["nav"]:
                # Create API Reference entry
                config["nav"] = [{"API Reference": api_nav}]
            else:
                # Check for an existing API Reference entry
                api_entry = None
                for i, entry in enumerate(config["nav"]):
                    if isinstance(entry, dict) and list(entry.keys())[0] in [
                        "API Reference",
                        "API",
                        output_dir,
                    ]:
                        api_entry = i
                        break

                if api_entry is not None:
                    # Update existing API Reference entry
                    nav_key = list(config["nav"][api_entry].keys())[0]
                    config["nav"][api_entry][nav_key] = api_nav
                else:
                    # Add API Reference entry
                    config["nav"].append({"API Reference": api_nav})

            log.info(f"Updated navigation with {len(rel_files)} API documentation files")

    def __update_lang_nav__(self, nav, lang, nav_tree, output_dir):
        """
        Update language-specific navigation with API documentation
        """
        # Look for language section in the navigation
        lang_entry = None
        for i, entry in enumerate(nav):
            if isinstance(entry, dict) and lang in entry:
                lang_entry = i
                break

        if lang_entry is not None:
            # Language section exists
            lang_nav = nav[lang_entry][lang]

            # Look for API Reference in this language section
            api_entry = None
            api_keys = ["API Reference", "API", output_dir]

            if isinstance(lang_nav, list):
                for i, entry in enumerate(lang_nav):
                    if isinstance(entry, dict) and any(key in entry for key in api_keys):
                        api_entry = i
                        break

            if api_entry is not None:
                # Update existing API Reference in this language
                api_key = next(key for key in api_keys if key in lang_nav[api_entry])
                lang_nav[api_entry][api_key] = nav_tree
            else:
                # Add API Reference to this language section
                if isinstance(lang_nav, list):
                    lang_nav.append({"API Reference": nav_tree})
                else:
                    nav[lang_entry][lang] = [{"API Reference": nav_tree}]
        else:
            # Language section doesn't exist, create it with API Reference
            nav.append({lang: [{"API Reference": nav_tree}]})

        log.info(f"Updated navigation for language '{lang}' with API documentation")

    def __are_files_in_nav__(self, nav, generated_files, docs_dir):
        """
        Check if all generated files are already included in the navigation
        """
        # Convert absolute paths to relative for comparison
        rel_generated_files = []
        for file_path in generated_files:
            if os.path.isabs(file_path):
                try:
                    rel_path = os.path.relpath(file_path, docs_dir)
                    rel_generated_files.append(rel_path)
                except ValueError:
                    rel_generated_files.append(file_path)
            else:
                rel_generated_files.append(file_path)

        # Recursively search for all file paths in the nav
        nav_files = []
        self.__extract_nav_files__(nav, nav_files)

        # Check if all generated files are in the nav
        missing_files = [f for f in rel_generated_files if f not in nav_files]
        return len(missing_files) == 0

    def _extract_nav_files(self, nav_item, result):
        """
        Recursively extract all file paths from a nav item
        """
        if isinstance(nav_item, list):
            for item in nav_item:
                self.__extract_nav_files__(item, result)
        elif isinstance(nav_item, dict):
            for key, value in nav_item.items():
                if isinstance(value, str):
                    result.append(value)
                else:
                    self.__extract_nav_files__(value, result)
        elif isinstance(nav_item, str):
            result.append(nav_item)

    def __build_nav_tree__(self, file_paths):
        """
        Build a nested navigation tree from a list of file paths
        """
        nav_tree = {}

        for file_path in file_paths:
            # Split the path into components
            components = file_path.replace("\\", "/").split("/")
            current = nav_tree

            # Process each path component except the last one (filename)
            for i, component in enumerate(components[:-1]):
                # Skip empty components
                if not component:
                    continue

                if component not in current:
                    current[component] = {}

                current = current[component]

            # Add the file to the current level
            filename = components[-1]
            name = os.path.splitext(filename)[0]  # Remove extension

            # Use the filename as the title
            current[name] = file_path

        # Convert nested dicts to MkDocs nav format
        return self.__convert_nav_tree__(nav_tree)

    def __convert_nav_tree__(self, nav_tree):
        """
        Convert a nested dictionary to MkDocs nav format
        """
        result = []

        for key, value in sorted(nav_tree.items()):
            if isinstance(value, dict):
                # This is a directory, recurse
                result.append({key: self.__convert_nav_tree__(value)})
            else:
                # This is a file
                result.append({key: value})

        return result

    def on_shutdown(self):
        """
        Stop the file watcher when shutting down
        """
        if self.observer:
            self.observer.stop()
            self.observer.join()

        # Save the file cache
        self.file_cache.save_cache()

    def __process_proto_files__(self, proto_paths: list[str], output_dir: str):
        """
        Process all proto files from the given paths
        Returns a list of generated markdown files
        """
        proto_files: set[str] = set()  # Use a set to avoid duplicates
        generated_files = []

        # Get absolute path to output directory to filter paths
        output_dir_abs = os.path.abspath(output_dir)

        # First, process directories to collect all their files
        dir_paths = [p for p in proto_paths if os.path.isdir(os.path.abspath(p))]
        file_paths = [
            p
            for p in proto_paths
            if os.path.isfile(os.path.abspath(p)) and p.endswith(".proto")
        ]

        # Process directories first
        for path in dir_paths:
            abs_path = os.path.abspath(path)

            # Skip directories that overlap with the output directory
            try:
                if os.path.exists(abs_path):
                    # Check if this directory overlaps with the output directory
                    if os.path.commonpath([abs_path, output_dir_abs]) in [
                        abs_path,
                        output_dir_abs,
                    ]:
                        log.warning(
                            f"Skipping proto directory that overlaps with output directory: {abs_path}"
                        )
                        continue

                    for root, _, files in os.walk(abs_path):
                        for file in files:
                            if file.endswith(".proto"):
                                file_path = os.path.join(root, file)
                                # Skip files in the output directory
                                try:
                                    if (
                                        os.path.commonpath(
                                            [output_dir_abs, os.path.abspath(file_path)]
                                        )
                                        == output_dir_abs
                                    ):
                                        continue
                                except ValueError:
                                    pass
                                proto_files.add(file_path)
            except ValueError as e:
                log.warning(f"Error processing proto path {abs_path}: {str(e)}")
            except Exception as e:
                log.warning(f"Proto path not found or error: {abs_path}, {str(e)}")

        # Then add individual files that weren't already added from directories
        for path in file_paths:
            abs_path = os.path.abspath(path)

            # Skip files in the output directory
            try:
                if os.path.commonpath([output_dir_abs, abs_path]) == output_dir_abs:
                    log.warning(f"Skipping proto file in output directory: {abs_path}")
                    continue
            except ValueError:
                pass

            if os.path.exists(abs_path) and abs_path not in proto_files:
                proto_files.add(abs_path)
            elif not os.path.exists(abs_path):
                log.warning(f"Proto file not found: {abs_path}")

        if proto_files:
            # Filter files that have changed
            changed_files: list[str] = []
            for file_path in proto_files:
                abs_path = os.path.abspath(file_path)
                if self.file_cache.is_file_changed(abs_path):
                    changed_files.append(file_path)
                    # Update the cache with the new file hash
                    self.file_cache.update_file_hash(abs_path)

            if changed_files:
                # Only process files that have changed
                try:
                    generated_files = self.converter.convert_proto_files(
                        changed_files, output_dir
                    )
                    log.info(
                        f"Processed {len(changed_files)} changed proto files out of {len(proto_files)} total"
                    )
                except Exception as e:
                    log.error(f"Error processing proto files: {str(e)}")
            else:
                log.info(
                    "No proto files have changed since last build, skipping conversion"
                )
        else:
            log.warning("No proto files found in the specified paths")

        return generated_files
