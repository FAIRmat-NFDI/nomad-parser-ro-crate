"""
Shared utilities for RO-Crate parsing across different parsers and profiles.
This module provides common functionality that can be reused by:
- nomad-parser-ro-crate (general RO-Crate parsing)
- nomad-external-eln-integrations (interoperability profile)
- Future RO-Crate profile parsers
"""

import json
from typing import Any, Dict, List, Optional


def is_ro_crate_content(data: Dict[str, Any]) -> bool:
    """
    Validate if JSON data represents valid RO-Crate content.
    
    Args:
        data: Parsed JSON data
        
    Returns:
        True if data appears to be valid RO-Crate
    """
    # Check for required RO-Crate structure
    if not isinstance(data, dict):
        return False
        
    # Must have @context
    context = data.get('@context')
    if not context:
        return False
        
    # Must have @graph
    graph = data.get('@graph')
    if not isinstance(graph, list) or not graph:
        return False
        
    # Check for RO-Crate context
    if isinstance(context, list):
        has_ro_crate_context = any(
            'ro/crate' in str(ctx) for ctx in context
        )
    else:
        has_ro_crate_context = 'ro/crate' in str(context)
        
    if not has_ro_crate_context:
        return False
        
    # Should have root dataset
    has_root = any(
        item.get('@id') == './' and 'Dataset' in str(item.get('@type', []))
        for item in graph
    )
    
    return has_root


def extract_rdfs_classes(graph: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Extract RDFS class definitions from RO-Crate graph.
    
    Args:
        graph: RO-Crate @graph array
        
    Returns:
        Dictionary mapping class IDs to class definitions
    """
    rdfs_classes = {}
    
    for entity in graph:
        entity_type = entity.get('@type', [])
        if isinstance(entity_type, str):
            entity_type = [entity_type]
            
        if 'rdfs:Class' in entity_type:
            class_id = entity.get('@id')
            if class_id:
                rdfs_classes[class_id] = entity
                
    return rdfs_classes


def extract_rdfs_properties(graph: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Extract RDFS property definitions from RO-Crate graph.
    
    Args:
        graph: RO-Crate @graph array
        
    Returns:
        Dictionary mapping property IDs to property definitions
    """
    rdfs_properties = {}
    
    for entity in graph:
        entity_type = entity.get('@type', [])
        if isinstance(entity_type, str):
            entity_type = [entity_type]
            
        if 'rdf:Property' in entity_type:
            prop_id = entity.get('@id')
            if prop_id:
                rdfs_properties[prop_id] = entity
                
    return rdfs_properties


def extract_data_instances(graph: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Extract data instances (non-schema entities) from RO-Crate graph.
    
    Args:
        graph: RO-Crate @graph array
        
    Returns:
        Dictionary mapping instance IDs to instance data
    """
    data_instances = {}
    schema_types = {'rdfs:Class', 'rdf:Property'}
    
    for entity in graph:
        entity_type = entity.get('@type', [])
        if isinstance(entity_type, str):
            entity_type = [entity_type]
            
        # Skip schema definitions
        if not any(st in entity_type for st in schema_types):
            instance_id = entity.get('@id')
            if instance_id:
                data_instances[instance_id] = entity
                
    return data_instances


def sanitize_property_name(prop_name: str) -> str:
    """
    Sanitize property name for use as Python identifier.
    
    Args:
        prop_name: Original property name
        
    Returns:
        Sanitized name safe for Python use
    """
    # Remove prefixes
    if ':' in prop_name:
        prop_name = prop_name.split(':', 1)[1]
        
    # Replace invalid characters
    import re
    prop_name = re.sub(r'[^a-zA-Z0-9_]', '_', prop_name)
    
    # Ensure it starts with a letter or underscore
    if prop_name and prop_name[0].isdigit():
        prop_name = f'_{prop_name}'
        
    return prop_name or 'unknown_property'


def get_python_type_from_xsd(xsd_type: str) -> type:
    """
    Map XSD types to Python types.
    
    Args:
        xsd_type: XSD type string
        
    Returns:
        Corresponding Python type
    """
    if 'string' in xsd_type:
        return str
    elif 'int' in xsd_type:
        return int
    elif 'float' in xsd_type or 'double' in xsd_type:
        return float
    elif 'dateTime' in xsd_type:
        return str  # Could be datetime.datetime in future
    elif 'boolean' in xsd_type:
        return bool
    else:
        return str