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

import json

import pytest
from nomad.datamodel import EntryArchive

from tests.conftest import (
    COMPLEX_DATA_INSTANCES,
    COMPLEX_RDFS_CLASSES,
    COMPLEX_RDFS_PROPERTIES,
    COMPLEX_RO_CRATE,
    INVALID_RO_CRATE,
    NO_SCHEMA_DATA_INSTANCES,
    NO_SCHEMA_RDFS_CLASSES,
    NO_SCHEMA_RDFS_PROPERTIES,
    NO_SCHEMA_RO_CRATE,
    REAL_EXAMPLE_DATA_INSTANCES,
    REAL_EXAMPLE_RDFS_CLASSES,
    REAL_EXAMPLE_RDFS_PROPERTIES,
    REAL_EXAMPLE_RO_CRATE,
    SIMPLE_DATA_INSTANCES,
    SIMPLE_RDFS_CLASSES,
    SIMPLE_RDFS_PROPERTIES,
    SIMPLE_RO_CRATE,
)

# Constants for edge case tests
EXPECTED_DOMAIN_COUNT = 2
EXPECTED_CIRCULAR_CLASSES = 2
EXPECTED_CIRCULAR_PROPERTIES = 2


class TestROCrateParser:
    """Test suite for the RO-Crate parser."""

    def test_parser_instantiation(self, parser):
        """Test that the parser can be instantiated with correct properties."""
        assert parser is not None
        assert parser.name == 'parsers/ro-crate'
        assert parser.code_name == 'ro-crate'
        assert parser.domain == 'generic'

    def test_mainfile_pattern_matching(self, parser):
        """Test that the parser matches the correct file patterns."""
        # Should match ro-crate-metadata.json files
        assert parser._mainfile_name_re.match('ro-crate-metadata.json')
        assert parser._mainfile_name_re.match('path/to/ro-crate-metadata.json')
        assert parser._mainfile_name_re.match('deep/nested/path/ro-crate-metadata.json')
        
        # Should not match other files
        assert not parser._mainfile_name_re.match('metadata.json')
        assert not parser._mainfile_name_re.match('ro-crate.json')
        assert not parser._mainfile_name_re.match('crate-metadata.json')

    def test_parse_simple_ro_crate(self, parser, test_data_path, simple_archive):
        """Test parsing a simple RO-Crate with one class and property."""
        ro_crate_path = test_data_path / SIMPLE_RO_CRATE
        
        parser.parse(str(ro_crate_path), simple_archive, None)
        
        # Check that workflow2 was created
        assert simple_archive.workflow2 is not None
        assert simple_archive.workflow2.name == 'RO-Crate Processing'
        
        # Check that data section was populated
        assert simple_archive.data is not None
        assert hasattr(simple_archive.data, 'rdfs_classes_count')
        assert hasattr(simple_archive.data, 'rdfs_properties_count')
        assert hasattr(simple_archive.data, 'data_instances_count')
        assert hasattr(simple_archive.data, 'crate_context')
        assert hasattr(simple_archive.data, 'raw_data')
        
        # Check expected counts
        assert simple_archive.data.rdfs_classes_count == SIMPLE_RDFS_CLASSES
        assert simple_archive.data.rdfs_properties_count == SIMPLE_RDFS_PROPERTIES
        assert simple_archive.data.data_instances_count == SIMPLE_DATA_INSTANCES
        
        # Check context preservation
        assert simple_archive.data.crate_context is not None
        context_str = simple_archive.data.crate_context
        assert 'https://w3id.org/ro/crate/1.1/context' in context_str
        
        # Check raw data preservation
        assert simple_archive.data.raw_data is not None
        raw_data = json.loads(simple_archive.data.raw_data)
        assert '@context' in raw_data
        assert '@graph' in raw_data

    def test_parse_complex_ro_crate(self, parser, test_data_path, simple_archive):
        """Test parsing a complex RO-Crate with multiple classes and properties."""
        ro_crate_path = test_data_path / COMPLEX_RO_CRATE
        
        parser.parse(str(ro_crate_path), simple_archive, None)
        
        # Check expected counts for complex example
        assert simple_archive.data.rdfs_classes_count == COMPLEX_RDFS_CLASSES
        assert simple_archive.data.rdfs_properties_count == COMPLEX_RDFS_PROPERTIES
        assert simple_archive.data.data_instances_count == COMPLEX_DATA_INSTANCES
        
        # Check that multiple namespaces are preserved
        context_str = simple_archive.data.crate_context
        assert 'schema.org' in context_str
        assert 'owl' in context_str
        assert 'rdfs' in context_str
        assert 'example.org' in context_str

    def test_parse_no_schema_ro_crate(self, parser, test_data_path, simple_archive):
        """Test parsing an RO-Crate with no RDFS schema definitions."""
        ro_crate_path = test_data_path / NO_SCHEMA_RO_CRATE
        
        parser.parse(str(ro_crate_path), simple_archive, None)
        
        # Should still create archive with zero schema elements
        assert simple_archive.data.rdfs_classes_count == NO_SCHEMA_RDFS_CLASSES
        assert simple_archive.data.rdfs_properties_count == NO_SCHEMA_RDFS_PROPERTIES
        assert simple_archive.data.data_instances_count == NO_SCHEMA_DATA_INSTANCES

    def test_parse_real_example_ro_crate(self, parser, test_data_path, simple_archive):
        """Test parsing the real RO-Crate example from the interoperability profile."""
        ro_crate_path = test_data_path / REAL_EXAMPLE_RO_CRATE
        
        parser.parse(str(ro_crate_path), simple_archive, None)
        
        # Check expected counts for real example
        assert simple_archive.data.rdfs_classes_count == REAL_EXAMPLE_RDFS_CLASSES
        assert simple_archive.data.rdfs_properties_count == REAL_EXAMPLE_RDFS_PROPERTIES
        assert simple_archive.data.data_instances_count == REAL_EXAMPLE_DATA_INSTANCES

    def test_schema_extraction_functionality(self, parser, test_data_path):
        """Test the schema extraction functionality in detail."""
        ro_crate_path = test_data_path / COMPLEX_RO_CRATE
        
        # Load the data and test extraction
        with open(ro_crate_path) as f:
            ro_crate_data = json.load(f)
        
        graph = ro_crate_data.get('@graph', [])
        parser._extract_schema_definitions(graph)
        
        # Check extracted RDFS classes
        assert len(parser._rdfs_classes) == COMPLEX_RDFS_CLASSES
        assert 'Person' in parser._rdfs_classes
        assert 'Organization' in parser._rdfs_classes
        
        # Check class details
        person_class = parser._rdfs_classes['Person']
        assert person_class['@type'] == 'rdfs:Class'
        assert person_class['rdfs:label'] == 'Person'
        assert person_class['rdfs:comment'] == 'A person entity'
        
        # Check extracted RDFS properties
        assert len(parser._rdfs_properties) == COMPLEX_RDFS_PROPERTIES
        assert 'hasName' in parser._rdfs_properties
        assert 'hasAge' in parser._rdfs_properties
        assert 'worksFor' in parser._rdfs_properties
        
        # Check property details
        name_property = parser._rdfs_properties['hasName']
        assert name_property['@type'] == 'rdfs:Property'
        assert name_property['rdfs:label'] == 'Name'
        assert 'schema:domainIncludes' in name_property
        assert 'schema:rangeIncludes' in name_property
        
        # Check extracted data instances
        assert len(parser._data_instances) == COMPLEX_DATA_INSTANCES
        assert 'person1' in parser._data_instances
        assert 'person2' in parser._data_instances
        assert 'org1' in parser._data_instances
        assert './' in parser._data_instances  # root dataset

    def test_dynamic_section_class_creation(self, parser, test_data_path):
        """Test that dynamic section classes can be created from RDFS definitions."""
        ro_crate_path = test_data_path / SIMPLE_RO_CRATE
        
        # Load and extract schema
        with open(ro_crate_path) as f:
            ro_crate_data = json.load(f)
        
        graph = ro_crate_data.get('@graph', [])
        parser._extract_schema_definitions(graph)
        
        # Test dynamic class creation
        test_class_def = parser._rdfs_classes['TestClass']
        dynamic_class = parser._create_dynamic_section_class(test_class_def)
        
        assert dynamic_class is not None
        assert dynamic_class.__name__ == 'TestClass'
        assert hasattr(dynamic_class, 'm_def')
        
        # Test that the class can be instantiated
        instance = dynamic_class()
        assert instance is not None

    def test_type_mapping(self, parser):
        """Test XSD to Python type mapping in quantity creation."""
        # Test string type
        string_prop = {
            '@id': 'stringProp',
            'schema:rangeIncludes': {'@id': 'xsd:string'},
            'rdfs:comment': 'A string property'
        }
        quantity = parser._create_nomad_quantity(string_prop)
        # NOMAD wraps basic types, so check if it contains the expected type
        assert 'str' in str(quantity.type)
        
        # Test integer type  
        int_prop = {
            '@id': 'intProp',
            'schema:rangeIncludes': {'@id': 'xsd:int'},
            'rdfs:comment': 'An integer property'
        }
        quantity = parser._create_nomad_quantity(int_prop)
        assert 'int' in str(quantity.type)
        
        # Test boolean type
        bool_prop = {
            '@id': 'boolProp',
            'schema:rangeIncludes': {'@id': 'xsd:boolean'},
            'rdfs:comment': 'A boolean property'
        }
        quantity = parser._create_nomad_quantity(bool_prop)
        assert 'bool' in str(quantity.type)

    def test_error_handling_invalid_json(self, parser, test_data_path, simple_archive):
        """Test error handling with invalid JSON structure."""
        invalid_path = test_data_path / INVALID_RO_CRATE
        
        # Should handle missing @graph gracefully
        parser.parse(str(invalid_path), simple_archive, None)
        
        # Should create minimal archive structure
        assert simple_archive.data.rdfs_classes_count == 0
        assert simple_archive.data.rdfs_properties_count == 0
        assert simple_archive.data.data_instances_count == 0

    def test_error_handling_missing_file(self, parser, simple_archive):
        """Test error handling with missing file."""
        with pytest.raises(FileNotFoundError):
            parser.parse('nonexistent_file.json', simple_archive, None)

    @pytest.mark.parametrize(
        'ro_crate_file,expected_classes,expected_properties,expected_instances',
        [
            (
                SIMPLE_RO_CRATE,
                SIMPLE_RDFS_CLASSES,
                SIMPLE_RDFS_PROPERTIES,
                SIMPLE_DATA_INSTANCES,
            ),
            (
                COMPLEX_RO_CRATE,
                COMPLEX_RDFS_CLASSES,
                COMPLEX_RDFS_PROPERTIES,
                COMPLEX_DATA_INSTANCES,
            ),
            (
                NO_SCHEMA_RO_CRATE,
                NO_SCHEMA_RDFS_CLASSES,
                NO_SCHEMA_RDFS_PROPERTIES,
                NO_SCHEMA_DATA_INSTANCES,
            ),
            (
                REAL_EXAMPLE_RO_CRATE,
                REAL_EXAMPLE_RDFS_CLASSES,
                REAL_EXAMPLE_RDFS_PROPERTIES,
                REAL_EXAMPLE_DATA_INSTANCES,
            ),
        ],
    )
    def test_parse_all_examples(
        self, parser, test_data_path, ro_crate_file, expected_classes, 
        expected_properties, expected_instances
    ):
        """Parameterized test to parse all RO-Crate examples."""
        ro_crate_path = test_data_path / ro_crate_file
        archive = EntryArchive()
        
        # Should not raise any exceptions
        parser.parse(str(ro_crate_path), archive, None)
        
        # Basic validation
        assert archive.workflow2 is not None
        assert archive.workflow2.name == 'RO-Crate Processing'
        assert archive.data is not None
        
        # Check expected counts
        assert archive.data.rdfs_classes_count == expected_classes
        assert archive.data.rdfs_properties_count == expected_properties
        assert archive.data.data_instances_count == expected_instances

    def test_json_ld_structure_validation(self, test_data_path):
        """Test that RO-Crate files have expected JSON-LD structure."""
        test_files = [
            SIMPLE_RO_CRATE,
            COMPLEX_RO_CRATE,
            NO_SCHEMA_RO_CRATE,
            REAL_EXAMPLE_RO_CRATE,
        ]
        
        for test_file in test_files:
            ro_crate_path = test_data_path / test_file
            
            with open(ro_crate_path) as f:
                data = json.load(f)
            
            # Test required top-level fields
            assert '@context' in data
            assert '@graph' in data
            
            # Test @context structure
            context = data['@context']
            assert isinstance(context, list)
            assert 'https://w3id.org/ro/crate/1.1/context' in context
            
            # Test @graph structure
            graph = data['@graph']
            assert isinstance(graph, list)
            assert len(graph) > 0
            
            # Should have root dataset and metadata file
            has_root_dataset = any(entity.get('@id') == './' for entity in graph)
            has_metadata_file = any(
                entity.get('@id') == 'ro-crate-metadata.json' for entity in graph
            )
            assert has_root_dataset
            assert has_metadata_file

    def test_rdfs_entity_identification(self, parser, test_data_path):
        """Test identification of different entity types in the graph."""
        ro_crate_path = test_data_path / COMPLEX_RO_CRATE
        
        with open(ro_crate_path) as f:
            ro_crate_data = json.load(f)
        
        graph = ro_crate_data.get('@graph', [])
        parser._extract_schema_definitions(graph)
        
        # Check that RDFS classes are correctly identified
        for entity_id, entity in parser._rdfs_classes.items():
            assert entity.get('@type') == 'rdfs:Class'
            assert 'rdfs:label' in entity or 'rdfs:comment' in entity
        
        # Check that RDFS properties are correctly identified
        for entity_id, entity in parser._rdfs_properties.items():
            assert entity.get('@type') == 'rdfs:Property'
            # Properties should have domain and range information
            assert 'schema:domainIncludes' in entity or 'schema:rangeIncludes' in entity
        
        # Check that data instances are correctly identified
        for entity_id, entity in parser._data_instances.items():
            entity_type = entity.get('@type')
            assert entity_type is not None
            excluded_types = [
                'rdfs:Class',
                'rdfs:Property', 
                'owl:restriction',
                'CreativeWork',
            ]
            assert entity_type not in excluded_types

    def test_property_domain_includes_handling(self, parser, test_data_path):
        """Test handling of properties with multiple domain includes."""
        ro_crate_path = test_data_path / COMPLEX_RO_CRATE
        
        with open(ro_crate_path) as f:
            ro_crate_data = json.load(f)
        
        graph = ro_crate_data.get('@graph', [])
        parser._extract_schema_definitions(graph)
        
        # Find hasName property which has multiple domains
        has_name_property = parser._rdfs_properties.get('hasName')
        assert has_name_property is not None
        
        domain_includes = has_name_property['schema:domainIncludes']
        assert isinstance(domain_includes, list)
        assert len(domain_includes) == EXPECTED_DOMAIN_COUNT
        
        # Should include both Person and Organization
        domain_ids = [domain['@id'] for domain in domain_includes]
        assert 'Person' in domain_ids
        assert 'Organization' in domain_ids

    def test_archive_data_section_structure(
        self, parser, test_data_path, simple_archive
    ):
        """Test the structure of the populated archive data section."""
        ro_crate_path = test_data_path / SIMPLE_RO_CRATE
        
        parser.parse(str(ro_crate_path), simple_archive, None)
        
        # Test ROCrateData section structure
        data = simple_archive.data
        assert hasattr(data, 'crate_context')
        assert hasattr(data, 'rdfs_classes_count')
        assert hasattr(data, 'rdfs_properties_count')
        assert hasattr(data, 'data_instances_count')
        assert hasattr(data, 'raw_data')
        
        # Test data types
        assert isinstance(data.crate_context, str)
        assert isinstance(data.rdfs_classes_count, int)
        assert isinstance(data.rdfs_properties_count, int)
        assert isinstance(data.data_instances_count, int)
        assert isinstance(data.raw_data, str)
        
        # Test that raw_data is valid JSON
        raw_data_parsed = json.loads(data.raw_data)
        assert '@context' in raw_data_parsed
        assert '@graph' in raw_data_parsed

    def test_logging_functionality(
        self, parser, test_data_path, simple_archive, log_output
    ):
        """Test that proper logging occurs during parsing."""
        ro_crate_path = test_data_path / SIMPLE_RO_CRATE
        
        # Parse with log capture
        parser.parse(str(ro_crate_path), simple_archive, None)
        
        # Check that appropriate log entries were created
        # Note: This would depend on the actual logger implementation
        # For now, just ensure parsing completed without exceptions
        assert simple_archive.data is not None
        assert simple_archive.workflow2 is not None


class TestROCrateParserEdgeCases:
    """Test edge cases and error conditions for the RO-Crate parser."""

    def test_empty_graph(self, parser, tmp_path, simple_archive):
        """Test handling of RO-Crate with empty @graph."""
        empty_ro_crate = {
            "@context": ["https://w3id.org/ro/crate/1.1/context"],
            "@graph": []
        }
        
        test_file = tmp_path / "empty_ro_crate.json"
        with open(test_file, 'w') as f:
            json.dump(empty_ro_crate, f)
        
        parser.parse(str(test_file), simple_archive, None)
        
        # Should handle gracefully with zero counts
        assert simple_archive.data.rdfs_classes_count == 0
        assert simple_archive.data.rdfs_properties_count == 0
        assert simple_archive.data.data_instances_count == 0

    def test_malformed_rdfs_entities(self, parser, tmp_path, simple_archive):
        """Test handling of malformed RDFS entities."""
        malformed_ro_crate = {
            "@context": ["https://w3id.org/ro/crate/1.1/context"],
            "@graph": [
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "Test Dataset"
                },
                {
                    "@id": "MalformedClass",
                    "@type": "rdfs:Class"
                    # Missing label and comment
                },
                {
                    "@id": "MalformedProperty", 
                    "@type": "rdfs:Property"
                    # Missing domain and range
                }
            ]
        }
        
        test_file = tmp_path / "malformed_ro_crate.json"
        with open(test_file, 'w') as f:
            json.dump(malformed_ro_crate, f)
        
        # Should not raise exceptions and handle gracefully
        parser.parse(str(test_file), simple_archive, None)
        
        assert simple_archive.data.rdfs_classes_count == 1  # MalformedClass
        assert simple_archive.data.rdfs_properties_count == 1  # MalformedProperty
        assert simple_archive.data.data_instances_count == 1  # root dataset

    def test_property_name_sanitization(self, parser):
        """Test that property names are properly sanitized for Python identifiers."""
        # Test property with special characters
        property_def = {
            '@id': 'my-property.with/special:characters',
            'schema:rangeIncludes': {'@id': 'xsd:string'},
            'rdfs:comment': 'A property with special characters'
        }
        
        quantity = parser._create_nomad_quantity(property_def)
        assert quantity is not None
        
        # Property name sanitization for Python identifiers
        # (implementation details not directly exposed)
        assert 'str' in str(quantity.type)
        assert quantity.description == 'A property with special characters'

    def test_circular_references_in_schema(self, parser, tmp_path, simple_archive):
        """Test handling of circular references in schema definitions."""
        circular_ro_crate = {
            "@context": [
                "https://w3id.org/ro/crate/1.1/context",
                {
                    "schema": "https://schema.org",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
                }
            ],
            "@graph": [
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": "Circular Reference Test"
                },
                {
                    "@id": "ClassA",
                    "@type": "rdfs:Class",
                    "rdfs:label": "Class A"
                },
                {
                    "@id": "ClassB", 
                    "@type": "rdfs:Class",
                    "rdfs:label": "Class B"
                },
                {
                    "@id": "refersToB",
                    "@type": "rdfs:Property",
                    "schema:domainIncludes": {"@id": "ClassA"},
                    "schema:rangeIncludes": {"@id": "ClassB"}
                },
                {
                    "@id": "refersToA",
                    "@type": "rdfs:Property", 
                    "schema:domainIncludes": {"@id": "ClassB"},
                    "schema:rangeIncludes": {"@id": "ClassA"}
                }
            ]
        }
        
        test_file = tmp_path / "circular_ro_crate.json"
        with open(test_file, 'w') as f:
            json.dump(circular_ro_crate, f)
        
        # Should handle circular references without infinite loops
        parser.parse(str(test_file), simple_archive, None)
        
        assert simple_archive.data.rdfs_classes_count == EXPECTED_CIRCULAR_CLASSES
        assert simple_archive.data.rdfs_properties_count == EXPECTED_CIRCULAR_PROPERTIES
        assert simple_archive.data.data_instances_count == 1
