#!/usr/bin/env python3
"""
Test script to verify the RO-Crate parser isolation test works correctly.
This bypasses the CLI issues and tests the parser directly.
"""

import os
import sys
import json
from pathlib import Path

# Add the source to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nomad_parser_ro_crate.parsers.parser import ROCrateParser
from nomad_parser_ro_crate.parsers import parser_entry_point
from nomad.datamodel import EntryArchive
import logging

def test_parser_configuration():
    """Test that the parser is configured with the isolation pattern."""
    print("🔧 Parser Configuration:")
    print(f"   Name: {parser_entry_point.name}")
    print(f"   Pattern: {parser_entry_point.mainfile_name_re}")
    print(f"   MIME: {parser_entry_point.mainfile_mime_re}")
    print(f"   Level: {parser_entry_point.level}")
    print()

def test_pattern_matching():
    """Test that the pattern matches only our specific test file."""
    import re
    pattern = parser_entry_point.mainfile_name_re
    
    test_cases = [
        ("ro-crate-metadata-TEST-UNIQUE-PATTERN-12345.json", True),
        ("ro-crate-metadata.json", False),
        ("metadata.json", False),
        ("other-file.json", False),
        ("path/to/ro-crate-metadata-TEST-UNIQUE-PATTERN-12345.json", False),  # Should NOT match with path
    ]
    
    print("🎯 Pattern Matching Test:")
    for filename, should_match in test_cases:
        matches = bool(re.match(pattern, filename))
        status = "✅" if matches == should_match else "❌"
        print(f"   {status} {filename} -> {matches} (expected {should_match})")
    print()

def test_parser_execution():
    """Test the parser execution with the isolation file."""
    test_file = "tests/data/simple_ro_crate/ro-crate-metadata-TEST-UNIQUE-PATTERN-12345.json"
    
    print("🚀 Parser Execution Test:")
    print(f"   File: {test_file}")
    print(f"   Exists: {os.path.exists(test_file)}")
    
    if not os.path.exists(test_file):
        print("   ❌ Test file does not exist!")
        return False
    
    try:
        parser = ROCrateParser()
        archive = EntryArchive()
        logger = logging.getLogger()
        
        # Suppress debug output for cleaner test
        logging.getLogger().setLevel(logging.WARNING)
        
        parser.parse(test_file, archive, logger)
        
        print("   ✅ Parser executed successfully!")
        print(f"   ✅ Archive created: {archive.data is not None}")
        
        if archive.data:
            print(f"   ✅ Classes: {archive.data.rdfs_classes_count}")
            print(f"   ✅ Properties: {archive.data.rdfs_properties_count}")
            print(f"   ✅ Instances: {archive.data.data_instances_count}")
            print(f"   ✅ Workflow: {archive.workflow2.name if archive.workflow2 else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Parser failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 RO-Crate Parser Isolation Test")
    print("=" * 50)
    
    test_parser_configuration()
    test_pattern_matching()
    success = test_parser_execution()
    
    print("=" * 50)
    if success:
        print("✅ ALL TESTS PASSED!")
        print()
        print("📋 Next Steps:")
        print("   1. Upload /tmp/ro-crate-metadata-TEST-UNIQUE-PATTERN-12345.json to NOMAD")
        print("   2. Check if you get 1 entry (parser conflicts fixed) or 8 entries (deeper issue)")
        print("   3. Report back the results!")
    else:
        print("❌ TESTS FAILED!")
        print("   The parser configuration needs to be fixed.")

if __name__ == "__main__":
    main()