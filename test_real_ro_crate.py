#!/usr/bin/env python3
"""
Test the RO-Crate parser with a real example file.
"""

import sys
from pathlib import Path

# Add the source directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_real_ro_crate():
    """Test the parser with a real RO-Crate example file."""
    
    # Import our parser
    from nomad_parser_ro_crate.parsers.parser import ROCrateParser
    
    real_file = Path("test_real_ro_crate.json")
    if not real_file.exists():
        print("❌ Real RO-Crate file not found")
        return
    
    try:
        # Create parser instance
        parser = ROCrateParser()
        print(f"Created parser: {parser.name}")
        
        # Load and analyze the real file
        import json
        with open(real_file) as f:
            ro_crate_data = json.load(f)
        
        graph = ro_crate_data.get('@graph', [])
        parser._extract_schema_definitions(graph)
        
        print(f"\nReal RO-Crate analysis:")
        print(f"  Total entities in @graph: {len(graph)}")
        print(f"  RDFS classes: {len(parser._rdfs_classes)}")
        print(f"  RDFS properties: {len(parser._rdfs_properties)}")
        print(f"  Data instances: {len(parser._data_instances)}")
        
        print(f"\nRDFS Classes found:")
        for class_id in parser._rdfs_classes:
            print(f"  - {class_id}")
        
        print(f"\nRDFS Properties found (first 10):")
        for i, prop_id in enumerate(parser._rdfs_properties):
            if i >= 10:
                print(f"  ... and {len(parser._rdfs_properties) - 10} more")
                break
            print(f"  - {prop_id}")
            
        print(f"\nData Instances found (first 10):")
        for i, instance_id in enumerate(parser._data_instances):
            if i >= 10:
                print(f"  ... and {len(parser._data_instances) - 10} more")
                break
            instance = parser._data_instances[instance_id]
            instance_type = instance.get('@type', 'Unknown')
            print(f"  - {instance_id} (type: {instance_type})")
        
        # Test the full parser
        logger = type('MockLogger', (), {
            'info': lambda *args, **kwargs: print(f"INFO: {args[1] if len(args) > 1 else args[0]}"),
            'warning': lambda *args, **kwargs: print(f"WARNING: {args[1] if len(args) > 1 else args[0]}"),
            'error': lambda *args, **kwargs: print(f"ERROR: {args[1] if len(args) > 1 else args[0]}")
        })()
        
        # Create a mock archive
        archive = type('MockArchive', (), {})()
        
        print(f"\nRunning full parser...")
        parser.parse(str(real_file), archive, logger)
        
        print(f"\nParser completed successfully!")
        if hasattr(archive, 'data'):
            print(f"  Archive populated with RO-Crate data")
            print(f"  Classes: {getattr(archive.data, 'rdfs_classes_count', 0)}")
            print(f"  Properties: {getattr(archive.data, 'rdfs_properties_count', 0)}")
            print(f"  Instances: {getattr(archive.data, 'data_instances_count', 0)}")
        
        print("\n✅ Real RO-Crate test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing with real RO-Crate: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_ro_crate()