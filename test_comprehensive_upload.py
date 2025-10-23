#!/usr/bin/env python3
"""
Test RO-Crate upload behavior more comprehensively.
"""

import sys
import logging
import tempfile
import shutil
import json
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, 'src')

try:
    from nomad.datamodel import EntryArchive
    from nomad_parser_ro_crate.parsers.parser import ROCrateParser
    from nomad_parser_ro_crate.parsers import parser_entry_point
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)


def test_individual_ro_crates():
    """Test each RO-Crate individually to verify they work."""

    print('🧪 Testing individual RO-Crates...')

    test_data_dir = Path('tests/data')
    ro_crate_dirs = []

    for item in test_data_dir.iterdir():
        if item.is_dir() and (item / 'ro-crate-metadata.json').exists():
            ro_crate_dirs.append(item)

    if not ro_crate_dirs:
        print('❌ No RO-Crate directories found')
        return False

    parser = ROCrateParser()
    logger = logging.getLogger(__name__)

    all_passed = True

    for i, ro_crate_dir in enumerate(ro_crate_dirs, 1):
        print(f'\n[{i}/{len(ro_crate_dirs)}] Testing {ro_crate_dir.name}')
        print('-' * 50)

        metadata_file = ro_crate_dir / 'ro-crate-metadata.json'

        try:
            # Create fresh archive for each test
            archive = EntryArchive()

            # Parse the RO-Crate
            parser.parse(str(metadata_file), archive, logger)

            # Verify results
            if archive.data is None:
                print(f'❌ No archive.data populated')
                all_passed = False
                continue

            print(f'✅ Parsing successful')
            print(f'  Classes: {archive.data.rdfs_classes_count}')
            print(f'  Properties: {archive.data.rdfs_properties_count}')
            print(f'  Instances: {archive.data.data_instances_count}')

            # Verify raw data
            if archive.data.raw_data:
                raw_data = json.loads(archive.data.raw_data)
                graph_size = len(raw_data.get('@graph', []))
                print(f'  Graph entities: {graph_size}')

                # Check for dataset metadata
                dataset_entity = None
                for entity in raw_data.get('@graph', []):
                    if entity.get('@id') == './' and entity.get('@type') == 'Dataset':
                        dataset_entity = entity
                        break

                if dataset_entity:
                    name = dataset_entity.get('name', 'Unnamed')
                    description = dataset_entity.get('description', 'No description')
                    print(f'  Dataset: {name}')
                    print(
                        f"  Description: {description[:50]}{'...' if len(description) > 50 else ''}"
                    )

            else:
                print(f'❌ No raw data available')
                all_passed = False

        except Exception as e:
            print(f'❌ Parsing failed: {e}')
            all_passed = False

    return all_passed


def simulate_multi_file_upload():
    """Simulate what happens when multiple JSON files are uploaded together."""

    print(f'\n🔍 Simulating multi-file upload scenario...')

    test_data_dir = Path('tests/data')

    # Find all JSON files (like NOMAD would see during upload)
    json_files = list(test_data_dir.rglob('*.json'))

    print(f'Found {len(json_files)} JSON files:')
    for json_file in json_files:
        rel_path = json_file.relative_to(test_data_dir)
        print(f'  - {rel_path}')

    # Test pattern matching for each file
    import re

    pattern = parser_entry_point.mainfile_name_re

    print(f'\nPattern matching results (pattern: {pattern}):')

    matching_files = []
    non_matching_files = []

    for json_file in json_files:
        rel_path = str(json_file.relative_to(test_data_dir))
        match = re.match(pattern, rel_path)

        if match:
            matching_files.append(json_file)
            print(f'  ✅ {rel_path}')
        else:
            non_matching_files.append(json_file)
            print(f'  ❌ {rel_path}')

    print(f'\nSummary:')
    print(f'  Matching files: {len(matching_files)}')
    print(f'  Non-matching files: {len(non_matching_files)}')

    if len(matching_files) > 1:
        print(f'\n⚠️  Multiple files would match the parser pattern!')
        print(f'   This could cause NOMAD to create multiple entries.')
        print(f'   Recommendation: Upload each RO-Crate separately.')

    return len(matching_files) == ro_crate_dirs_expected


def create_upload_ready_examples():
    """Create clean examples ready for upload."""

    print(f'\n📦 Creating upload-ready examples...')

    output_dir = Path('upload_examples')
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    test_data_dir = Path('tests/data')

    # Copy each RO-Crate as a separate upload example
    for item in test_data_dir.iterdir():
        if item.is_dir() and (item / 'ro-crate-metadata.json').exists():
            dest = output_dir / item.name
            shutil.copytree(item, dest)
            print(f'  ✅ Created: {dest}')

    # Create a README for upload instructions
    readme_content = """# RO-Crate Upload Examples

This directory contains clean RO-Crate examples ready for upload to NOMAD.

## Upload Instructions

### Option 1: Upload Individual Directories
Upload each directory (e.g., `simple_ro_crate/`) as a separate upload to NOMAD.

### Option 2: Create ZIP Files
You can also zip each directory and upload the ZIP file:

```bash
# Example: Create ZIP for simple_ro_crate
cd simple_ro_crate
zip -r ../simple_ro_crate.zip .
cd ..
# Upload simple_ro_crate.zip to NOMAD
```

## What to Expect

- NOMAD will detect the `ro-crate-metadata.json` file
- The RO-Crate parser will process the JSON-LD metadata
- Archive data will be populated with:
  - RDFS class and property counts
  - Data instance counts
  - Raw JSON-LD data
  - Extracted schema definitions

## Troubleshooting

If the parser doesn't work:

1. **Check file structure**: Ensure `ro-crate-metadata.json` is at the root level
2. **Upload one at a time**: Don't upload multiple RO-Crates together
3. **Avoid extra files**: Don't include non-RO-Crate JSON files in the upload
4. **Check JSON syntax**: Ensure the metadata file is valid JSON-LD

## Examples Included

"""

    for item in output_dir.iterdir():
        if item.is_dir():
            metadata_file = item / 'ro-crate-metadata.json'
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        data = json.load(f)

                    # Find dataset info
                    dataset_name = 'Unknown'
                    dataset_desc = 'No description'

                    for entity in data.get('@graph', []):
                        if (
                            entity.get('@id') == './'
                            and entity.get('@type') == 'Dataset'
                        ):
                            dataset_name = entity.get('name', 'Unknown')
                            dataset_desc = entity.get('description', 'No description')
                            break

                    readme_content += f'- **{item.name}**: {dataset_name}\n'
                    readme_content += f'  {dataset_desc}\n\n'

                except Exception:
                    readme_content += f'- **{item.name}**: RO-Crate example\n\n'

    with open(output_dir / 'README.md', 'w') as f:
        f.write(readme_content)

    print(f"  ✅ Created: {output_dir / 'README.md'}")
    print(f'\n💡 Upload examples are ready in: {output_dir}')

    return True


def main():
    """Run comprehensive RO-Crate upload tests."""

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()],
    )

    print('🧪 RO-Crate Upload Test Suite')
    print('=' * 50)

    # Test 1: Individual RO-Crates
    test1_passed = test_individual_ro_crates()

    # Test 2: Multi-file upload simulation
    global ro_crate_dirs_expected
    ro_crate_dirs_expected = 6  # Expected number of RO-Crates
    test2_passed = simulate_multi_file_upload()

    # Test 3: Create upload examples
    test3_passed = create_upload_ready_examples()

    print(f'\n' + '=' * 50)
    print(f'📊 Test Results:')
    print(f"  Individual RO-Crate parsing: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Multi-file upload analysis: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"  Upload examples creation: {'✅ PASS' if test3_passed else '❌ FAIL'}")

    if test1_passed and test2_passed and test3_passed:
        print(f'\n✅ All tests passed!')
        print(f'\n💡 Key findings:')
        print(f'  - RO-Crate parser works correctly')
        print(f'  - Archive.data is populated properly')
        print(f'  - Upload examples are ready for testing')
        print(f'\n📋 Next steps:')
        print(f"  1. Try uploading examples from 'upload_examples/' directory")
        print(f'  2. Upload one RO-Crate at a time')
        print(f'  3. Check NOMAD logs for any processing errors')
        return True
    else:
        print(f'\n❌ Some tests failed!')
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
