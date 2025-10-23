#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import importlib
import logging
import re

try:
    from nomad.datamodel import EntryArchive
except ImportError:
    # For local testing when nomad is not available
    EntryArchive = None

try:
    from nomad_parser_ro_crate.parsers import parser_entry_point
except ImportError:
    # For local testing when the package is not installed
    parser_entry_point = None


class TestMatchingInterface:
    """Test suite for the RO-Crate parser matching interface."""

    def test_parser_entry_point_configuration(self):
        """Test that the parser entry point is properly configured."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        assert parser_entry_point.name == 'parsers/ro-crate'
        expected_description = 'NOMAD parser for RO-Crate JSON-LD metadata files.'
        assert parser_entry_point.description == expected_description
        assert parser_entry_point.code_name == 'RO-Crate'
        assert parser_entry_point.code_homepage == 'https://w3id.org/ro/crate'
        assert parser_entry_point.code_category is None  # No category set
        assert parser_entry_point.plugin_package is None  # Default when run locally

    def test_mainfile_pattern_matching(self):
        """Test that the mainfile pattern matches correct files."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        pattern = parser_entry_point.mainfile_name_re

        # Should match ro-crate-metadata.json files
        valid_files = [
            'ro-crate-metadata.json',
            'path/to/ro-crate-metadata.json',
            'deep/nested/path/ro-crate-metadata.json',
            '/absolute/path/ro-crate-metadata.json',
        ]

        for filename in valid_files:
            assert re.match(pattern, filename), f'Pattern should match {filename}'

        # Should not match other files
        invalid_files = [
            'metadata.json',
            'ro-crate.json',
            'crate-metadata.json',
            'ro-crate-metadata.txt',
            'ro-crate-metadata.json.bak',
            'not-ro-crate-metadata.json',
        ]

        for filename in invalid_files:
            message = f'Pattern should not match {filename}'
            assert not re.match(pattern, filename), message

    def test_mime_type_matching(self):
        """Test that the MIME type pattern is correct."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        mime_pattern = parser_entry_point.mainfile_mime_re
        assert mime_pattern == 'application/json'

    def test_parser_interface_loading(self):
        """Test that the parser interface loads correctly."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        parser_interface = parser_entry_point.load()

        # Check that we get a MatchingParserInterface
        assert parser_interface is not None
        assert type(parser_interface).__name__ == 'MatchingParserInterface'

    def test_parser_class_resolution(self):
        """Test that the parser class can be resolved and instantiated."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        parser_class_name = parser_entry_point.parser_class_name
        expected_class = 'nomad_parser_ro_crate.parsers.parser.ROCrateParser'
        assert parser_class_name == expected_class

        # Try to import and instantiate the parser class
        module_name, class_name = parser_class_name.rsplit('.', 1)

        parser_module = importlib.import_module(module_name)
        parser_class = getattr(parser_module, class_name)

        # Instantiate the parser
        parser_instance = parser_class()

        # Check parser properties
        assert parser_instance.name == 'parsers/ro-crate'
        assert parser_instance.code_name == 'ro-crate'
        assert parser_instance.domain == 'generic'
        assert hasattr(parser_instance, 'parse')

    def test_parser_metadata(self):
        """Test that parser metadata is properly configured."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        metadata = parser_entry_point.metadata

        assert metadata is not None
        assert metadata['codeCategory'] is None
        assert metadata['codeLabel'] == 'RO-Crate'
        expected_style = 'RO in capitals, hyphen, Crate with capital C'
        assert metadata['codeLabelStyle'] == expected_style
        assert metadata['codeName'] == 'ro-crate'
        assert metadata['codeUrl'] == 'https://w3id.org/ro/crate'
        assert metadata['status'] == 'development'

        # Check that documentation sections exist
        assert 'parserSpecific' in metadata
        assert 'tableOfFiles' in metadata
        assert 'ro-crate-metadata.json' in metadata['tableOfFiles']

    def test_parser_aliases(self):
        """Test that parser aliases are configured."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        aliases = parser_entry_point.aliases
        assert aliases == ['parsers/ro-crate']

    def test_parser_level(self):
        """Test that parser execution level is set correctly."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        assert parser_entry_point.level == 0

    def test_integration_with_test_file(self, test_data_path):
        """Test complete integration with an actual RO-Crate file."""
        if parser_entry_point is None or EntryArchive is None:
            raise ImportError('Required dependencies not available')

        # Get the parser class and instantiate it
        parser_class_name = parser_entry_point.parser_class_name
        module_name, class_name = parser_class_name.rsplit('.', 1)

        parser_module = importlib.import_module(module_name)
        parser_class = getattr(parser_module, class_name)
        parser_instance = parser_class()

        # Test with a simple RO-Crate file
        test_file = test_data_path / 'simple_ro_crate_metadata.json'

        if test_file.exists():
            # Create archive and logger
            archive = EntryArchive()
            logger = logging.getLogger(__name__)

            # Parse the file - should not raise exceptions
            parser_instance.parse(str(test_file), archive, logger)

            # Basic validation that parsing worked
            assert archive.data is not None
            assert hasattr(archive.data, 'rdfs_classes_count')
            assert hasattr(archive.data, 'rdfs_properties_count')
            assert hasattr(archive.data, 'data_instances_count')

    def test_entry_point_dictionary_serialization(self):
        """Test that the entry point can be serialized to dictionary."""
        if parser_entry_point is None:
            raise ImportError('Parser entry point not available')

        entry_dict = parser_entry_point.dict()

        # Check key fields are present
        assert 'name' in entry_dict
        assert 'description' in entry_dict
        assert 'mainfile_name_re' in entry_dict
        assert 'mainfile_mime_re' in entry_dict
        assert 'parser_class_name' in entry_dict
        assert 'code_name' in entry_dict
        assert 'metadata' in entry_dict

        # Check values
        assert entry_dict['name'] == 'parsers/ro-crate'
        expected_parser_class = 'nomad_parser_ro_crate.parsers.parser.ROCrateParser'
        assert entry_dict['parser_class_name'] == expected_parser_class
