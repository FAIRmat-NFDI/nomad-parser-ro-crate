#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from nomad.config.models.plugins import ParserEntryPoint
from pydantic import Field


class ROCrateParserEntryPoint(ParserEntryPoint):
    """
    Entry point for the RO-Crate JSON-LD parser.
    
    This parser processes RO-Crate metadata files (ro-crate-metadata.json)
    that follow the RO-Crate specification and extracts schema definitions
    and data instances for NOMAD integration.
    """
    
    parser_class_name: str = Field(
        'nomad_parser_ro_crate.parsers.parser.ROCrateParser',
        description="""
        The fully qualified name of the Python class that implements the parser.
        This class must have a function `def parse(self, mainfile, archive, logger)`.
        """,
    )
    level: int = Field(
        0,
        description="""
        Order of execution of parser with respect to other parsers.
        """,
    )
    code_name: str | None = 'RO-Crate'
    code_homepage: str | None = 'https://w3id.org/ro/crate'
    code_category: str | None = 'Data management'
    metadata: dict | None = Field(
        {
            'codeCategory': 'Data management',
            'codeLabel': 'RO-Crate',
            'codeLabelStyle': 'RO in capitals, hyphen, Crate with capital C',
            'codeName': 'ro-crate',
            'codeUrl': 'https://w3id.org/ro/crate',
            'parserDirName': 'dependencies/parsers/nomad-parser-ro-crate/',
            'parserGitUrl': 'https://github.com/nomad-coe/nomad-parser-ro-crate.git',
            'parserSpecific': '''## Usage notes
The parser processes RO-Crate metadata files that follow the RO-Crate specification.
It extracts RDFS schema definitions (classes and properties) and data instances
from the JSON-LD @graph structure.

The parser supports:
- RDFS class and property definitions
- Dynamic metainfo section creation from schema
- Data instance extraction and validation
- Context preservation (@context field)
- Raw JSON-LD data preservation

For optimal parsing results:
- Ensure ro-crate-metadata.json follows the RO-Crate 1.1 specification
- Include RDFS schema definitions in the @graph for dynamic typing
- Use standard schema.org vocabulary where possible
''',
            'preamble': '',
            'status': 'development',
            'tableOfFiles': '''| Input Filename | Description |
| --- | --- |
| `ro-crate-metadata.json` | **Mainfile**: RO-Crate metadata file in JSON-LD format |
| Other files referenced in RO-Crate | Additional files described in the metadata |
''',
        },
        description="""
        Metadata passed to the UI for display and documentation.
        """,
    )

    def load(self):
        from nomad.parsing import MatchingParserInterface
        return MatchingParserInterface(**self.dict())


parser_entry_point = ROCrateParserEntryPoint(
    name='parsers/ro-crate',
    aliases=['parsers/ro-crate'],
    description='NOMAD parser for RO-Crate JSON-LD metadata files.',
    mainfile_name_re=r'(^|.*/)ro-crate-metadata\.json$',
    mainfile_mime_re=r'application/json',
)
