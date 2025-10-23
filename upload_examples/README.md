# RO-Crate Upload Examples

This directory contains clean RO-Crate examples ready for upload to NOMAD.

## Upload Instructions

⚠️ **IMPORTANT**: Upload ONE RO-Crate at a time. Do NOT upload the entire `upload_examples/` directory as this will create duplicate entries for each RO-Crate.

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

### ❌ Wrong Way (Creates Duplicates)
```bash
# DON'T DO THIS - creates multiple entries
zip -r all_examples.zip upload_examples/
```

### ✅ Correct Way (One Entry Per RO-Crate)
```bash
# DO THIS - upload one at a time
cd upload_examples/
zip -r simple_example.zip simple_ro_crate/
# Upload simple_example.zip
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

- **openbis_profile_ro_crate**: OpenBIS Publications Export
  Example dataset exported from OpenBIS containing publication metadata with RDFS schema

- **no_schema_ro_crate**: No Schema Dataset
  A dataset with no RDFS schema definitions

- **comprehensive_ro_crate**: Example RO-Crate with Schema
  A comprehensive example of an RO-Crate following the interoperability profile with RDFS schema definitions and data instances.

- **real_example_ro_crate**: name
  description

- **complex_ro_crate**: Complex Test Dataset
  A complex test RO-Crate dataset with multiple classes and properties

- **simple_ro_crate**: Simple Test Dataset
  A simple test RO-Crate dataset for parser testing

