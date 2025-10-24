import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

from nomad.config import config
from nomad.datamodel.data import EntryData
from nomad.datamodel.metainfo.workflow import Workflow
from nomad.metainfo import (
    MSection,
    Quantity,
    Section,
)
from nomad.parsing.parser import MatchingParser

configuration = config.get_plugin_entry_point(
    'nomad_parser_ro_crate.parsers:parser_entry_point'
)


class ROCrateData(EntryData):
    """A section to hold RO-Crate data."""

    crate_context = Quantity(
        type=str,
        description='The @context from the RO-Crate JSON-LD',
        a_eln={'component': 'StringEditQuantity'},
    )

    rdfs_classes_count = Quantity(
        type=int,
        description='Number of RDFS classes found in the RO-Crate',
        a_eln={'component': 'NumberEditQuantity'},
    )

    rdfs_properties_count = Quantity(
        type=int,
        description='Number of RDFS properties found in the RO-Crate',
        a_eln={'component': 'NumberEditQuantity'},
    )

    data_instances_count = Quantity(
        type=int,
        description='Number of data instances found in the RO-Crate',
        a_eln={'component': 'NumberEditQuantity'},
    )

    raw_data = Quantity(
        type=str,
        description='Raw JSON-LD data from the RO-Crate file',
        a_eln={'component': 'StringEditQuantity'},
    )


class ROCrateParser(MatchingParser):
    """
    A parser for RO-Crate JSON-LD metadata files.
    
    This parser:
    1. Reads RO-Crate JSON-LD files (ro-crate-metadata.json)
    2. Extracts schema definitions
    3. Creates dynamic metainfo sections based on the schema
    4. Populates the archive with data instances following the schema
    """

    def __init__(self):
        super().__init__(
            name='parsers/ro-crate',
            code_name='ro-crate',
            domain='generic',
            # Make MIME type more specific to reduce conflicts
            mainfile_mime_re=r'application/json',
            mainfile_name_re=r'(^|.*/)ro-crate-metadata\.json$',
            # Set higher priority to resolve conflicts
            mainfile_alternative=False,
        )
        self._rdfs_classes = {}
        self._rdfs_properties = {}
        self._data_instances = {}

    def _extract_schema_definitions(self, graph: list[dict[str, Any]]) -> None:
        """Extract RDFS class and property definitions from the RO-Crate graph."""
        self._rdfs_classes = {}
        self._rdfs_properties = {}
        self._data_instances = {}

        for entity in graph:
            entity_type = entity.get('@type')
            entity_id = entity.get('@id')

            if entity_type == 'rdfs:Class':
                self._rdfs_classes[entity_id] = entity
            elif entity_type == 'rdfs:Property':
                self._rdfs_properties[entity_id] = entity
            elif entity_type and entity_type not in [
                'rdfs:Class',
                'rdfs:Property',
                'owl:restriction',
                'CreativeWork',
            ]:
                # This is a data instance
                self._data_instances[entity_id] = entity

    def _create_dynamic_section_class(self, class_def: dict[str, Any]) -> type:
        """Create a dynamic NOMAD Section class from an RDFS class definition."""
        class_id = class_def.get('@id', 'unknown')
        class_name = class_id.split(':')[-1] if ':' in class_id else class_id

        # Clean the class name to be a valid Python identifier
        clean_name = class_name.replace('.', '_').replace('-', '_').replace('/', '_')

        description = class_def.get('rdfs:comment', class_def.get('rdfs:label', ''))

        # Create quantities for properties that have this class as domain
        quantities = {}

        for prop_id, prop_def in self._rdfs_properties.items():
            domain_includes = prop_def.get('schema:domainIncludes')
            if domain_includes:
                # Handle both single domain and list of domains
                domains = (
                    domain_includes
                    if isinstance(domain_includes, list)
                    else [domain_includes]
                )
                for domain in domains:
                    domain_id = (
                        domain.get('@id') if isinstance(domain, dict) else domain
                    )
                    if domain_id == class_id:
                        prop_name = (
                            prop_id.split(':')[-1] if ':' in prop_id else prop_id
                        )
                        prop_name = (
                            prop_name.replace('.', '_')
                            .replace('-', '_')
                            .replace('/', '_')
                        )

                        # Determine the type based on schema:rangeIncludes
                        range_includes = prop_def.get('schema:rangeIncludes', {})
                        range_type = (
                            range_includes.get('@id', 'xsd:string')
                            if isinstance(range_includes, dict)
                            else 'xsd:string'
                        )

                        # Map XSD types to Python types
                        if 'string' in range_type:
                            quantity_type = str
                        elif 'int' in range_type:
                            quantity_type = int
                        elif 'float' in range_type or 'double' in range_type:
                            quantity_type = float
                        elif 'dateTime' in range_type:
                            quantity_type = str
                        elif 'boolean' in range_type:
                            quantity_type = bool
                        else:
                            quantity_type = str

                        prop_description = prop_def.get(
                            'rdfs:comment', prop_def.get('rdfs:label', '')
                        )

                        component = (
                            'StringEditQuantity'
                            if quantity_type == str
                            else 'NumberEditQuantity'
                        )

                        quantities[prop_name] = Quantity(
                            type=quantity_type,
                            description=prop_description,
                            a_eln={'component': component},
                        )

        # Create the dynamic class
        dynamic_class = type(
            clean_name,
            (MSection,),
            {
                '__module__': __name__,
                'm_def': Section(description=description),
                **quantities,
            },
        )

        return dynamic_class

    def _create_nomad_quantity(self, prop_def: dict[str, Any]) -> Quantity:
        """Create a NOMAD Quantity from an RDFS property definition."""
        prop_description = prop_def.get('rdfs:comment', prop_def.get('rdfs:label', ''))

        # Determine the type based on schema:rangeIncludes
        range_includes = prop_def.get('schema:rangeIncludes', {})
        range_type = (
            range_includes.get('@id', 'xsd:string')
            if isinstance(range_includes, dict)
            else 'xsd:string'
        )

        # Map XSD types to Python types
        if 'string' in range_type:
            quantity_type = str
        elif 'int' in range_type:
            quantity_type = int
        elif 'float' in range_type or 'double' in range_type:
            quantity_type = float
        elif 'dateTime' in range_type:
            quantity_type = str
        elif 'boolean' in range_type:
            quantity_type = bool
        else:
            quantity_type = str

        component = (
            'StringEditQuantity' if quantity_type == str else 'NumberEditQuantity'
        )

        return Quantity(
            type=quantity_type,
            description=prop_description,
            a_eln={'component': component},
        )

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] = None,
    ) -> None:
        """Parse an RO-Crate JSON-LD metadata file."""
        print(f'DEBUG RO-CRATE: PROCESSING {mainfile} (archive id: {id(archive)})')
        if logger:
            logger.info(f'Starting RO-Crate processing for: {mainfile}')

        try:
            # Load the RO-Crate JSON-LD file
            with open(mainfile, encoding='utf-8') as f:
                ro_crate_data = json.load(f)

            # Create minimal empty archive for testing
            if not archive.data:
                archive.data = ROCrateData()

            # Extract the graph
            graph = ro_crate_data.get('@graph', [])
            if logger:
                logger.info(f'Found {len(graph)} entities in @graph')

            if not graph:
                if logger:
                    logger.warning('No @graph found in RO-Crate file')
                # Create minimal data section even for invalid files
                archive.data.crate_context = str(ro_crate_data.get('@context', ''))
                archive.data.rdfs_classes_count = 0
                archive.data.rdfs_properties_count = 0
                archive.data.data_instances_count = 0
                archive.data.raw_data = json.dumps(ro_crate_data, indent=2)
                return

            # Extract schema definitions
            if logger:
                logger.info('Starting schema extraction...')
            self._extract_schema_definitions(graph)
            if logger:
                logger.info(
                    f'Extracted {len(self._rdfs_classes)} RDFS classes and '
                    f'{len(self._rdfs_properties)} properties and '
                    f'{len(self._data_instances)} data instances'
                )

            # Set basic info with proper schema extraction
            archive.data.crate_context = str(ro_crate_data.get('@context', ''))
            archive.data.rdfs_classes_count = len(self._rdfs_classes)
            archive.data.rdfs_properties_count = len(self._rdfs_properties)
            archive.data.data_instances_count = len(self._data_instances)
            archive.data.raw_data = json.dumps(ro_crate_data, indent=2)

            # Set workflow information
            archive.workflow2 = Workflow(
                name='RO-Crate Processing', workflow_type='data_management'
            )

            print(f'DEBUG RO-CRATE: SUCCESSFULLY PROCESSED {mainfile}')
            if logger:
                logger.info(f'Successfully opened and parsed RO-Crate file: {mainfile}')

        except Exception as e:
            error_msg = f'Error processing RO-Crate file {mainfile}: {e}'
            print(f'DEBUG RO-CRATE: ERROR - {error_msg}')
            if logger:
                logger.error(error_msg, exc_info=True)
            raise