# NOMAD RO-Crate Parser

A NOMAD parser for RO-Crate metadata files that works similarly to the MetaInfoParser. This parser can read RO-Crate JSON-LD files and extract schema definitions and data instances into NOMAD archives.

## Features

- **RO-Crate JSON-LD Support**: Reads `ro-crate-metadata.json` files following the RO-Crate specification
- **Schema Extraction**: Automatically extracts RDFS class and property definitions from the RO-Crate
- **Dynamic Metainfo**: Creates NOMAD metainfo structures based on the discovered schema
- **Data Population**: Populates NOMAD archives with data instances following the extracted schema
- **MetaInfoParser-like Functionality**: Similar workflow to NOMAD's existing MetaInfoParser for YAML files

## How It Works

1. **JSON-LD Parsing**: Loads the RO-Crate metadata file and extracts the `@graph` array
2. **Schema Discovery**: Identifies RDFS classes (`rdfs:Class`) and properties (`rdfs:Property`) 
3. **Type Mapping**: Maps XSD data types to Python types for NOMAD quantities
4. **Archive Population**: Creates a structured NOMAD archive with:
   - Context information from the RO-Crate
   - Counts of discovered schema elements
   - Raw JSON-LD data for reference

## Supported File Pattern

The parser matches files with the pattern: `.*ro-crate-metadata\.json$`

## Example Usage

The parser automatically processes RO-Crate files when they are uploaded to NOMAD. For testing:

```bash
# Run the test with a simple example
uv run python test_ro_crate_parser.py

# Run the test with a real RO-Crate file
uv run python test_real_ro_crate.py
```

## Archive Structure

The parser creates a `ROCrateData` section in the archive containing:

- `crate_context`: The `@context` from the RO-Crate JSON-LD
- `rdfs_classes_count`: Number of RDFS classes found
- `rdfs_properties_count`: Number of RDFS properties found  
- `data_instances_count`: Number of data instances found
- `raw_data`: Complete raw JSON-LD data

## RO-Crate Interoperability Profile Support

This parser is designed to work with the RO-Crate Interoperability Profile, supporting:

- RDFS class and property definitions
- Schema.org vocabulary mappings
- OWL restrictions and cardinalities
- Custom namespace definitions

## Example RO-Crate Structure

```json
{
  "@context": [
    "https://w3id.org/ro/crate/1.1/context",
    {
      "schema": "https://schema.org",
      "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
    }
  ],
  "@graph": [
    {
      "@id": "MyClass",
      "@type": "rdfs:Class",
      "rdfs:label": "My Custom Class"
    },
    {
      "@id": "myProperty", 
      "@type": "rdfs:Property",
      "schema:domainIncludes": {"@id": "MyClass"},
      "schema:rangeIncludes": {"@id": "xsd:string"}
    },
    {
      "@id": "instance1",
      "@type": "MyClass",
      "myProperty": "Hello World!"
    }
  ]
}
```

## Development

If you want to develop locally this plugin, clone the project and in the plugin folder, create a virtual environment (you can use Python 3.10, 3.11 or 3.12):
```sh
git clone https://github.com/FAIRmat-NFDI/nomad-parser-ro-crate.git
cd nomad-parser-ro-crate
python3.11 -m venv .pyenv
. .pyenv/bin/activate
```

Make sure to have `pip` upgraded:
```sh
pip install --upgrade pip
```

We recommend installing `uv` for fast pip installation of the packages:
```sh
pip install uv
```

Install the `nomad-lab` package:
```sh
uv pip install -e '.[dev]'
```

### Run the tests

You can run locally the tests:
```sh
python -m pytest -sv tests
```

where the `-s` and `-v` options toggle the output verbosity.

Our CI/CD pipeline produces a more comprehensive test report using the `pytest-cov` package. You can generate a local coverage report:
```sh
uv pip install pytest-cov
python -m pytest --cov=src tests
```

### Run linting and auto-formatting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting the code. Ruff auto-formatting is also a part of the GitHub workflow actions. You can run locally:
```sh
ruff check .
ruff format . --check
```

### Debugging

For interactive debugging of the tests, use `pytest` with the `--pdb` flag. We recommend using an IDE for debugging, e.g., _VSCode_. If that is the case, add the following snippet to your `.vscode/launch.json`:
```json
{
  "configurations": [
      {
        "name": "<descriptive tag>",
        "type": "debugpy",
        "request": "launch",
        "cwd": "${workspaceFolder}",
        "program": "${workspaceFolder}/.pyenv/bin/pytest",
        "justMyCode": true,
        "env": {
            "_PYTEST_RAISE": "1"
        },
        "args": [
            "-sv",
            "--pdb",
            "<path-to-plugin-tests>",
        ]
    }
  ]
}
```

where `<path-to-plugin-tests>` must be changed to the local path to the test module to be debugged.

The settings configuration file `.vscode/settings.json` automatically applies the linting and formatting upon saving the modified file.

### Documentation on Github pages

To view the documentation locally, install the related packages using:
```sh
uv pip install -r requirements_docs.txt
```

Run the documentation server:
```sh
mkdocs serve
```

## Adding this plugin to NOMAD

Currently, NOMAD has two distinct flavors that are relevant depending on your role as an user:
1. [A NOMAD Oasis](#adding-this-plugin-in-your-nomad-oasis): any user with a NOMAD Oasis instance.
2. [Local NOMAD installation and the source code of NOMAD](#adding-this-plugin-in-your-local-nomad-installation-and-the-source-code-of-nomad): internal developers.

### Adding this plugin in your NOMAD Oasis

Read the [NOMAD plugin documentation](https://nomad-lab.eu/prod/v1/staging/docs/howto/oasis/plugins_install.html) for all details on how to deploy the plugin on your NOMAD instance.

### Adding this plugin in your local NOMAD installation and the source code of NOMAD

We now recommend using the dedicated [`nomad-distro-dev`](https://github.com/FAIRmat-NFDI/nomad-distro-dev) repository to simplify the process. Please refer to that repository for detailed instructions.

### Template update

We use [`cruft`](https://github.com/cruft/cruft) to update the project based on template changes. To run the check for updates locally, run `cruft update` in the root of the project. More details see the instructions on [`cruft` website](https://cruft.github.io/cruft/#updating-a-project).

## Main contributors
| Name | E-mail     |
|------|------------|
| Joseph Rudzinski | [joseph.rudzinski@physik.hu-berlin.de](mailto:joseph.rudzinski@physik.hu-berlin.de)
