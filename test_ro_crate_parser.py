#!/usr/bin/env python3
"""
Simple test script for the RO-Crate parser.
"""

import json
import sys
from pathlib import Path

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_parser_with_example():
    """Test the parser with the RO-Crate example file."""
    
    # Import our parser
    from nomad_parser_ro_crate.parsers.parser import ROCrateParser
    
    # Create a simple test RO-Crate metadata file
    test_data = {
        "@context": [
            "https://w3id.org/ro/crate/1.1/context",
            {
                "schema": "https://schema.org",
                "owl": "http://www.w3.org/2002/07/owl#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            }
        ],
        "@graph": [
            # Root dataset
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "Test Dataset",
                "description": "A test RO-Crate dataset"
            },
            # RO-Crate metadata file
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}
            },
            # RDFS Class definition
            {
                "@id": "TestClass",
                "@type": "rdfs:Class",
                "rdfs:label": "Test Class",
                "rdfs:comment": "A test class for demonstration"
            },
            # RDFS Property definition
            {
                "@id": "testProperty",
                "@type": "rdfs:Property",
                "rdfs:label": "Test Property",
                "rdfs:comment": "A test property",
                "schema:domainIncludes": {"@id": "TestClass"},
                "schema:rangeIncludes": {"@id": "xsd:string"}
            },
            # Data instance
            {
                "@id": "test-instance-1",
                "@type": "TestClass",
                "testProperty": "Hello World!"
            }
        ]
    }
    
    # Write test data to a temporary file
    test_file = Path("test_ro_crate_metadata.json")
    with open(test_file, "w") as f:
        json.dump(test_data, f, indent=2)
    
    try:
        # Create parser instance
        parser = ROCrateParser()
        print(f"Created parser: {parser.name}")
        print(f"Matches pattern: {getattr(parser, '_mainfile_name_re', 'N/A')}")
        
        # Test the schema extraction method directly
        graph = test_data["@graph"]
        parser._extract_schema_definitions(graph)
        
        print(f"\nExtracted {len(parser._rdfs_classes)} RDFS classes:")
        for class_id in parser._rdfs_classes:
            print(f"  - {class_id}")
        
        print(f"\nExtracted {len(parser._rdfs_properties)} RDFS properties:")
        for prop_id in parser._rdfs_properties:
            print(f"  - {prop_id}")
            
        print(f"\nExtracted {len(parser._data_instances)} data instances:")
        for instance_id in parser._data_instances:
            print(f"  - {instance_id}")
        
        # Test schema package creation
        logger = type('MockLogger', (), {
            'info': lambda *args, **kwargs: print(f"INFO: {args}"),
            'warning': lambda *args, **kwargs: print(f"WARNING: {args}"),
            'error': lambda *args, **kwargs: print(f"ERROR: {args}")
        })()
        
        # Create a mock archive
        archive = type('MockArchive', (), {})()
        
        # Test the full parse method
        parser.parse(str(test_file), archive, logger)
        
        print("\nArchive data populated:")
        if hasattr(archive, 'data'):
            context_val = getattr(archive.data, 'crate_context', 'N/A')
            print(f"  Context: {context_val}")
            
            classes_count = getattr(archive.data, 'rdfs_classes_count', 'N/A')
            print(f"  Classes count: {classes_count}")
            
            props_count = getattr(archive.data, 'rdfs_properties_count', 'N/A')
            print(f"  Properties count: {props_count}")
            
            instances_count = getattr(archive.data, 'data_instances_count', 'N/A')
            print(f"  Instances count: {instances_count}")
        else:
            print("  No data section found")
        
        print("\n✅ Parser test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing parser: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    test_parser_with_example()