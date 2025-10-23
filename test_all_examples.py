#!/usr/bin/env python3
"""
Test runner for complex RO-Crate examples.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nomad.datamodel import EntryArchive
from nomad_parser_ro_crate.parsers.parser import ROCrateParser


def test_all_examples():
    """Test all RO-Crate examples."""
    print("Testing all RO-Crate examples...")
    
    # Setup logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    # Create parser instance
    parser = ROCrateParser()
    
    # Test data path
    test_data_path = Path(__file__).parent / 'tests' / 'data'
    
    # Test files and their expected counts
    test_cases = [
        ('simple_ro_crate_metadata.json', 1, 1, 2),
        ('complex_ro_crate_metadata.json', 2, 3, 4),
        ('no_schema_ro_crate_metadata.json', 0, 0, 2),
        ('real_example_ro_crate_metadata.json', 13, 28, 9),
    ]
    
    success_count = 0
    
    for filename, expected_classes, expected_props, expected_instances in test_cases:
        test_file = test_data_path / filename
        
        if not test_file.exists():
            print(f"✗ Test file not found: {filename}")
            continue
            
        print(f"\nTesting {filename}:")
        
        try:
            # Create fresh archive
            archive = EntryArchive()
            
            # Parse the file
            parser.parse(str(test_file), archive, logger)
            
            # Check results
            classes_count = archive.data.rdfs_classes_count
            props_count = archive.data.rdfs_properties_count
            instances_count = archive.data.data_instances_count
            
            print(f"  - RDFS Classes: {classes_count} (expected {expected_classes})")
            print(f"  - RDFS Properties: {props_count} (expected {expected_props})")
            print(f"  - Data Instances: {instances_count} (expected {expected_instances})")
            
            # Validate counts
            if (classes_count == expected_classes and 
                props_count == expected_props and 
                instances_count == expected_instances):
                print(f"  ✓ {filename} passed all tests")
                success_count += 1
            else:
                print(f"  ✗ {filename} failed validation")
                
        except Exception as e:
            print(f"  ✗ {filename} failed with error: {e}")
    
    print(f"\n{'='*50}")
    print(f"Results: {success_count}/{len(test_cases)} tests passed")
    
    if success_count == len(test_cases):
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == '__main__':
    success = test_all_examples()
    sys.exit(0 if success else 1)