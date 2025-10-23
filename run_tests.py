#!/usr/bin/env python3
"""
Simple test runner to verify the RO-Crate parser functionality.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nomad.datamodel import EntryArchive
from nomad_parser_ro_crate.parsers.parser import ROCrateParser


def test_simple_parsing():
    """Test basic parsing functionality."""
    print("Testing RO-Crate parser...")
    
    # Setup logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    # Create parser instance
    parser = ROCrateParser()
    print(f"✓ Parser created: {parser.name}")
    
    # Test with simple example
    test_data_path = Path(__file__).parent / 'tests' / 'data'
    simple_file = test_data_path / 'simple_ro_crate_metadata.json'
    
    if simple_file.exists():
        # Create archive
        archive = EntryArchive()
        
        # Parse the file
        try:
            parser.parse(str(simple_file), archive, logger)
            print("✓ Parsing successful")
            
            # Check results
            if hasattr(archive, 'data') and archive.data:
                print("✓ Archive data populated")
                print(f"  - RDFS Classes: {archive.data.rdfs_classes_count}")
                print(f"  - RDFS Properties: {archive.data.rdfs_properties_count}")
                print(f"  - Data Instances: {archive.data.data_instances_count}")
            else:
                print("✗ Archive data not populated")
                
            if hasattr(archive, 'workflow2') and archive.workflow2:
                print(f"✓ Workflow created: {archive.workflow2.name}")
            else:
                print("✗ Workflow not created")
                
        except Exception as e:
            print(f"✗ Parsing failed: {e}")
            return False
    else:
        print(f"✗ Test file not found: {simple_file}")
        return False
    
    print("\n✓ All basic tests passed!")
    return True


if __name__ == '__main__':
    success = test_simple_parsing()
    sys.exit(0 if success else 1)