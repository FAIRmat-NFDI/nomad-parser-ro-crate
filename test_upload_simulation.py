#!/usr/bin/env python3
"""
Simulate NOMAD upload process for RO-Crate files.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, 'src')

try:
    from nomad.datamodel import EntryArchive
    from nomad_parser_ro_crate.parsers.parser import ROCrateParser
    from nomad_parser_ro_crate.parsers import parser_entry_point
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure NOMAD is installed and the parser is available")
    sys.exit(1)


def simulate_nomad_upload(ro_crate_dir: Path):
    """
    Simulate what happens when NOMAD processes a RO-Crate directory upload.
    """
    print(f"🧪 Simulating NOMAD upload for: {ro_crate_dir}")
    print(f"Directory exists: {ro_crate_dir.exists()}")
    
    if not ro_crate_dir.exists():
        print(f"❌ Directory not found: {ro_crate_dir}")
        return
    
    # List all files in the directory
    files = list(ro_crate_dir.rglob('*'))
    files = [f for f in files if f.is_file()]
    
    print(f"\n📁 Files in RO-Crate directory:")
    for file in files:
        print(f"  - {file.relative_to(ro_crate_dir)}")
    
    # Find the main file (ro-crate-metadata.json)
    main_file = ro_crate_dir / 'ro-crate-metadata.json'
    
    if not main_file.exists():
        print(f"❌ Main file not found: {main_file}")
        return
    
    print(f"\n🎯 Main file found: {main_file.relative_to(ro_crate_dir)}")
    
    # Test pattern matching
    import re
    pattern = parser_entry_point.mainfile_name_re
    relative_path = str(main_file.relative_to(ro_crate_dir.parent))
    match = re.match(pattern, relative_path)
    
    print(f"\n🔍 Pattern matching:")
    print(f"  Pattern: {pattern}")
    print(f"  File path: {relative_path}")
    print(f"  Match: {'✅ YES' if match else '❌ NO'}")
    
    # Test parsing
    print(f"\n🔧 Testing parser:")
    
    try:
        parser = ROCrateParser()
        archive = EntryArchive()
        logger = logging.getLogger(__name__)
        
        # Parse the file
        parser.parse(str(main_file), archive, logger)
        
        print(f"✅ Parsing successful")
        print(f"  Archive has data: {archive.data is not None}")
        
        if archive.data:
            print(f"  RDFS classes: {getattr(archive.data, 'rdfs_classes_count', 'N/A')}")
            print(f"  RDFS properties: {getattr(archive.data, 'rdfs_properties_count', 'N/A')}")
            print(f"  Data instances: {getattr(archive.data, 'data_instances_count', 'N/A')}")
            
            # Check if raw data is populated
            if hasattr(archive.data, 'raw_data') and archive.data.raw_data:
                raw_data = json.loads(archive.data.raw_data)
                graph_size = len(raw_data.get('@graph', []))
                print(f"  Graph entities: {graph_size}")
            
        else:
            print(f"❌ Archive.data is None")
            
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with different file approaches
    print(f"\n🧩 Testing alternative file paths:")
    
    # Test absolute path
    try:
        archive2 = EntryArchive()
        parser.parse(str(main_file.absolute()), archive2, logger)
        print(f"  Absolute path parsing: {'✅' if archive2.data else '❌'}")
    except Exception as e:
        print(f"  Absolute path parsing: ❌ {e}")
    
    # Test relative path from current directory
    try:
        archive3 = EntryArchive()
        rel_path = os.path.relpath(main_file)
        parser.parse(rel_path, archive3, logger)
        print(f"  Relative path parsing: {'✅' if archive3.data else '❌'}")
    except Exception as e:
        print(f"  Relative path parsing: ❌ {e}")


def main():
    """Test all RO-Crate examples."""
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    test_data_dir = Path('tests/data')
    
    if not test_data_dir.exists():
        print(f"❌ Test data directory not found: {test_data_dir}")
        return
    
    # Find all RO-Crate directories
    ro_crate_dirs = []
    for item in test_data_dir.iterdir():
        if item.is_dir() and (item / 'ro-crate-metadata.json').exists():
            ro_crate_dirs.append(item)
    
    if not ro_crate_dirs:
        print(f"❌ No RO-Crate directories found in {test_data_dir}")
        return
    
    print(f"Found {len(ro_crate_dirs)} RO-Crate directories to test:")
    for ro_crate_dir in ro_crate_dirs:
        print(f"  - {ro_crate_dir.name}")
    
    print(f"\n" + "="*80)
    
    # Test each RO-Crate
    for i, ro_crate_dir in enumerate(ro_crate_dirs, 1):
        print(f"\n[{i}/{len(ro_crate_dirs)}] Testing: {ro_crate_dir.name}")
        print("="*60)
        simulate_nomad_upload(ro_crate_dir)
        
        if i < len(ro_crate_dirs):
            print(f"\n" + "-"*40)


if __name__ == '__main__':
    main()