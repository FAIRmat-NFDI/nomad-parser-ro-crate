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
        a_eln={'component': 'StringEditQuantity'}
    )
    
    rdfs_classes_count = Quantity(
        type=int,
        description='Number of RDFS classes found in the RO-Crate',
        a_eln={'component': 'NumberEditQuantity'}
    )
    
    rdfs_properties_count = Quantity(
        type=int,
        description='Number of RDFS properties found in the RO-Crate',
        a_eln={'component': 'NumberEditQuantity'}
    )
    
    data_instances_count = Quantity(
        type=int,
        description='Number of data instances found in the RO-Crate',
        a_eln={'component': 'NumberEditQuantity'}
    )
    
    raw_data = Quantity(
        type=str,
        description='Raw JSON-LD data from the RO-Crate file',
        a_eln={'component': 'StringEditQuantity'}
    )


class ROCrateParser(MatchingParser):
    """
    A parser for RO-Crate metadata files that works similarly to MetaInfoParser.
    
    This parser:
    1. Reads RO-Crate JSON-LD files (ro-crate-metadata.json)
    2. Extracts schema definitions (RDFS classes and properties)
    3. Creates dynamic metainfo sections based on the schema
    4. Populates the archive with data instances following the schema
    """

    def __init__(self):
        super().__init__(
            name='parsers/ro-crate',
            code_name='ro-crate',
            domain='generic',
            mainfile_mime_re='application/json',
            mainfile_name_re=r'(^|.*/)ro-crate-metadata\.json$',
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
                'rdfs:Class', 'rdfs:Property', 'owl:restriction', 'CreativeWork'
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
                        domain.get('@id') 
                        if isinstance(domain, dict) 
                        else domain
                    )
                    if domain_id == class_id:
                        prop_name = (
                            prop_id.split(':')[-1] 
                            if ':' in prop_id 
                            else prop_id
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
                            'rdfs:comment', 
                            prop_def.get('rdfs:label', '')
                        )
                        
                        component = (
                            'StringEditQuantity' 
                            if quantity_type == str 
                            else 'NumberEditQuantity'
                        )
                        
                        quantities[prop_name] = Quantity(
                            type=quantity_type,
                            description=prop_description,
                            a_eln={'component': component}
                        )

        # Create the dynamic class
        dynamic_class = type(
            clean_name,
            (MSection,),
            {
                '__module__': __name__,
                'm_def': Section(description=description),
                **quantities
            }
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
            'StringEditQuantity' 
            if quantity_type == str 
            else 'NumberEditQuantity'
        )
        
        return Quantity(
            type=quantity_type,
            description=prop_description,
            a_eln={'component': component}
        )

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger: 'BoundLogger',
        child_archives: dict[str, 'EntryArchive'] = None,
    ) -> None:
        """
        Parse an RO-Crate metadata file.
        
        This method:
        1. Loads the JSON-LD file
        2. Extracts schema definitions
        3. Creates dynamic NOMAD sections
        4. Populates the archive with data
        """
        logger.info(f'ROCrateParser.parse called for: {mainfile}') if logger else None

        # Check if this archive has already been processed by this parser
        if (hasattr(archive, 'data') and archive.data and 
            hasattr(archive.data, 'raw_data') and archive.data.raw_data):
            if logger:
                logger.warning(
                    f'Archive already processed by RO-Crate parser, '
                    f'skipping: {mainfile}'
                )
            return

        try:
            # Load the RO-Crate JSON-LD file
            with open(mainfile, encoding='utf-8') as f:
                ro_crate_data = json.load(f)
            
            # Extract the graph
            graph = ro_crate_data.get('@graph', [])
            if not graph:
                if logger:
                    logger.warning('No @graph found in RO-Crate file')
                # Create minimal data section even for invalid files
                if not archive.data:
                    archive.data = ROCrateData()
                archive.data.rdfs_classes_count = 0
                archive.data.rdfs_properties_count = 0
                archive.data.data_instances_count = 0
                archive.data.crate_context = str(ro_crate_data.get('@context', ''))
                archive.data.raw_data = json.dumps(ro_crate_data, indent=2)
                return

            # Extract schema definitions
            self._extract_schema_definitions(graph)
            if logger:
                logger.info(
                    f'Found {len(self._rdfs_classes)} RDFS classes and '
                    f'{len(self._rdfs_properties)} properties'
                )

            # Create the RO-Crate data section
            if not archive.data:
                archive.data = ROCrateData()
            
            # Populate basic metadata
            archive.data.crate_context = str(ro_crate_data.get('@context', ''))
            archive.data.rdfs_classes_count = len(self._rdfs_classes)
            archive.data.rdfs_properties_count = len(self._rdfs_properties)
            archive.data.data_instances_count = len(self._data_instances)
            archive.data.raw_data = json.dumps(ro_crate_data, indent=2)

            # Set workflow information
            archive.workflow2 = Workflow(
                name='RO-Crate Processing',
                workflow_type='data_management'
            )
            
            # Add debugging info to help with upload issues
            if logger:
                logger.info(
                    f'Archive populated: data={archive.data is not None}, '
                    f'workflow2={archive.workflow2 is not None}'
                )
            
            # Log the parsing summary
            if logger:
                logger.info(
                    f'Successfully processed RO-Crate with {len(self._data_instances)} '
                    f'data instances from {len(graph)} graph entities'
                )

        except json.JSONDecodeError as e:
            if logger:
                logger.error(f'Invalid JSON in RO-Crate file: {e}')
            raise
        except Exception as e:
            if logger:
                logger.error('Error parsing RO-Crate file', exc_info=e)
            raise
