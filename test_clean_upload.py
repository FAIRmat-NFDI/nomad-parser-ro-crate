#!/usr/bin/env python3
"""
Create a clean RO-Crate for testing upload behavior.
"""

import sys
import os
import json
import tempfile
import shutil
import zipfile
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, 'src')

try:
    from nomad.datamodel import EntryArchive
    from nomad_parser_ro_crate.parsers.parser import ROCrateParser
    from nomad_parser_ro_crate.parsers import parser_entry_point
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


def create_clean_ro_crate():
    """Create a clean RO-Crate in a temporary directory."""
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix='ro_crate_test_'))
    ro_crate_dir = temp_dir / 'my_research_data'
    ro_crate_dir.mkdir()
    
    # Create the RO-Crate metadata
    ro_crate_metadata = {
        "@context": [
            "https://w3id.org/ro/crate/1.1/context",
            {
                "schema": "https://schema.org",
                "owl": "http://www.w3.org/2002/07/owl#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
            }
        ],
        "@graph": [
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "My Research Dataset",
                "description": "A research dataset with measurement data and analysis",
                "creator": {
                    "@type": "Person",
                    "name": "Test Researcher"
                },
                "dateCreated": "2024-10-23",
                "license": {"@id": "https://creativecommons.org/licenses/by/4.0/"}
            },
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
                "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"}
            },
            {
                "@id": "data.csv",
                "@type": "File",
                "name": "Measurement Data",
                "description": "Raw measurement data in CSV format",
                "encodingFormat": "text/csv"
            },
            {
                "@id": "analysis.py", 
                "@type": "File",
                "name": "Analysis Script",
                "description": "Python script for data analysis",
                "encodingFormat": "text/x-python"
            },
            # RDFS Schema definitions
            {
                "@id": "Measurement",
                "@type": "rdfs:Class",
                "rdfs:label": "Measurement",
                "rdfs:comment": "A measurement taken in the experiment"
            },
            {
                "@id": "temperature",
                "@type": "rdfs:Property",
                "rdfs:label": "Temperature",
                "rdfs:comment": "Temperature in Celsius",
                "schema:domainIncludes": {"@id": "Measurement"},
                "schema:rangeIncludes": {"@id": "xsd:float"}
            },
            {
                "@id": "measurement1",
                "@type": "Measurement",
                "temperature": 25.5,
                "description": "First measurement taken at room temperature"
            }
        ]
    }
    
    # Write the metadata file
    metadata_file = ro_crate_dir / 'ro-crate-metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(ro_crate_metadata, f, indent=2)
    
    # Create some sample data files
    data_file = ro_crate_dir / 'data.csv'
    with open(data_file, 'w') as f:
        f.write("timestamp,temperature,humidity\n")
        f.write("2024-10-23T10:00:00,25.5,60.2\n")
        f.write("2024-10-23T11:00:00,26.1,58.7\n")
        f.write("2024-10-23T12:00:00,27.3,55.9\n")
    
    analysis_file = ro_crate_dir / 'analysis.py'
    with open(analysis_file, 'w') as f:
        f.write("""#!/usr/bin/env python3
import pandas as pd

# Load the data
data = pd.read_csv('data.csv')

# Basic analysis
print(f"Average temperature: {data['temperature'].mean():.1f}°C")
print(f"Temperature range: {data['temperature'].min():.1f} - {data['temperature'].max():.1f}°C")
""")
    
    return temp_dir, ro_crate_dir


def test_single_ro_crate_upload():
    """Simulate uploading a single RO-Crate directory."""
    
    temp_dir, ro_crate_dir = create_clean_ro_crate()
    
    try:
        print(f"🧪 Testing single RO-Crate upload simulation")
        print(f"Created test RO-Crate at: {ro_crate_dir}")
        
        # List files in the RO-Crate
        files = list(ro_crate_dir.rglob('*'))
        files = [f for f in files if f.is_file()]
        
        print(f"\n📁 Files in RO-Crate:")
        for file in files:
            rel_path = file.relative_to(ro_crate_dir)
            print(f"  - {rel_path} ({file.stat().st_size} bytes)")
        
        # Test pattern matching
        metadata_file = ro_crate_dir / 'ro-crate-metadata.json'
        pattern = parser_entry_point.mainfile_name_re
        
        # Test different path representations
        test_paths = [
            str(metadata_file.relative_to(ro_crate_dir.parent)),  # relative to parent
            str(metadata_file.relative_to(ro_crate_dir)),  # relative to crate (should be just filename)
            metadata_file.name,  # just filename
        ]
        
        print(f"\n🔍 Pattern matching tests:")
        print(f"  Pattern: {pattern}")
        
        import re
        for test_path in test_paths:
            match = re.match(pattern, test_path)
            status = '✅' if match else '❌'
            print(f"  {status} {test_path}")
        
        # Test parsing
        print(f"\n🔧 Testing parser:")
        
        parser = ROCrateParser()
        archive = EntryArchive()
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Parse the metadata file
        parser.parse(str(metadata_file), archive, logger)
        
        print(f"✅ Parsing successful")
        print(f"  Archive.data populated: {archive.data is not None}")
        
        if archive.data:
            print(f"  RDFS classes: {archive.data.rdfs_classes_count}")
            print(f"  RDFS properties: {archive.data.rdfs_properties_count}")
            print(f"  Data instances: {archive.data.data_instances_count}")
            
            # Check if we can access the raw data
            if hasattr(archive.data, 'raw_data') and archive.data.raw_data:
                raw_data = json.loads(archive.data.raw_data)
                graph_entities = len(raw_data.get('@graph', []))
                print(f"  Graph entities: {graph_entities}")
        
        # Create a ZIP file version for testing
        zip_file = temp_dir / 'my_research_data.zip'
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                arcname = file.relative_to(ro_crate_dir)
                zf.write(file, arcname)
        
        print(f"\n📦 Created ZIP version: {zip_file.name} ({zip_file.stat().st_size} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    success = test_single_ro_crate_upload()
    if success:
        print(f"\n✅ All tests passed!")
        print(f"\n💡 Upload recommendations:")
        print(f"  1. Upload the RO-Crate as a single directory")
        print(f"  2. Or zip the RO-Crate directory and upload the ZIP file")
        print(f"  3. Avoid uploading multiple RO-Crates or extra JSON files together")
        print(f"  4. The parser will automatically detect ro-crate-metadata.json files")
    else:
        print(f"\n❌ Tests failed!")
        sys.exit(1)