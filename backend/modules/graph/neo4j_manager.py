"""
Neo4j Knowledge Graph Manager
Handles connection, node/relationship creation, and graph queries
for medical surgical knowledge graph.
"""

from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Neo4jManager:
    """
    Manages Neo4j graph database operations for surgical knowledge graph.
    
    Node Types:
    - Procedure: Surgical procedures (e.g., "Appendectomy", "Cholecystectomy")
    - Anatomy: Anatomical structures (e.g., "Appendix", "Gallbladder")
    - Instrument: Surgical instruments (e.g., "Scalpel", "Laparoscope")
    - Complication: Potential complications (e.g., "Bleeding", "Infection")
    - Technique: Surgical techniques (e.g., "Laparoscopic", "Open")
    - Medication: Medications used (e.g., "Antibiotics", "Anesthesia")
    
    Relationship Types:
    - INVOLVES: Procedure -> Anatomy
    - REQUIRES: Procedure -> Instrument
    - MAY_CAUSE: Procedure -> Complication
    - USES_TECHNIQUE: Procedure -> Technique
    - REQUIRES_MEDICATION: Procedure -> Medication
    - PREVENTS: Medication -> Complication
    - CONTRAINDICATED_WITH: Procedure -> Procedure
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j database URI (e.g., "bolt://localhost:7687")
            user: Database username
            password: Database password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connectivity()
        self._create_indexes()
    
    def _verify_connectivity(self):
        """Verify database connection is working."""
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for faster lookups."""
        indexes = [
            "CREATE INDEX procedure_name IF NOT EXISTS FOR (p:Procedure) ON (p.name)",
            "CREATE INDEX anatomy_name IF NOT EXISTS FOR (a:Anatomy) ON (a.name)",
            "CREATE INDEX instrument_name IF NOT EXISTS FOR (i:Instrument) ON (i.name)",
            "CREATE INDEX complication_name IF NOT EXISTS FOR (c:Complication) ON (c.name)",
            "CREATE INDEX technique_name IF NOT EXISTS FOR (t:Technique) ON (t.name)",
            "CREATE INDEX medication_name IF NOT EXISTS FOR (m:Medication) ON (m.name)"
        ]
        
        with self.driver.session() as session:
            for index_query in indexes:
                try:
                    session.run(index_query)
                except Exception as e:
                    logger.warning(f"Index creation warning: {e}")
        
        logger.info("Graph indexes created/verified")
    
    def create_procedure_node(self, name: str, description: str = "", 
                             metadata: Dict[str, Any] = None) -> str:
        """
        Create or merge a Procedure node.
        
        Args:
            name: Procedure name
            description: Procedure description
            metadata: Additional metadata (ignored for now to avoid Neo4j type issues)
        
        Returns:
            Node ID
        """
        with self.driver.session() as session:
            result = session.run("""
                MERGE (p:Procedure {name: $name})
                ON CREATE SET 
                    p.description = $description,
                    p.created_at = datetime()
                ON MATCH SET
                    p.description = CASE WHEN $description <> '' THEN $description ELSE p.description END,
                    p.updated_at = datetime()
                RETURN elementId(p) as id
            """, name=name, description=description)
            
            record = result.single()
            return record["id"] if record else None
    
    def create_entity_node(self, entity_type: str, name: str, 
                          properties: Dict[str, Any] = None) -> str:
        """
        Create or merge an entity node of any type.
        
        Args:
            entity_type: Node label (Anatomy, Instrument, Complication, etc.)
            name: Entity name
            properties: Additional properties (ignored for now to avoid Neo4j type issues)
        
        Returns:
            Node ID
        """
        with self.driver.session() as session:
            result = session.run(f"""
                MERGE (e:{entity_type} {{name: $name}})
                ON CREATE SET 
                    e.created_at = datetime()
                ON MATCH SET
                    e.updated_at = datetime()
                RETURN elementId(e) as id
            """, name=name)
            
            record = result.single()
            return record["id"] if record else None
    
    def create_relationship(self, from_node: str, to_node: str, 
                          relationship_type: str, 
                          from_label: str, to_label: str,
                          properties: Dict[str, Any] = None) -> bool:
        """
        Create a relationship between two nodes.
        
        Args:
            from_node: Source node name
            to_node: Target node name
            relationship_type: Type of relationship
            from_label: Label of source node
            to_label: Label of target node
            properties: Relationship properties (ignored for now to avoid Neo4j type issues)
        
        Returns:
            Success status
        """
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (from:{from_label} {{name: $from_node}})
                MATCH (to:{to_label} {{name: $to_node}})
                MERGE (from)-[r:{relationship_type}]->(to)
                ON CREATE SET 
                    r.created_at = datetime()
                RETURN r
            """, from_node=from_node, to_node=to_node)
            
            return result.single() is not None
    
    def add_procedure_with_entities(self, procedure: str, entities: Dict[str, List[str]]):
        """
        Add a complete procedure with all its related entities.
        
        Args:
            procedure: Procedure name
            entities: Dictionary with entity types as keys and lists of entity names
                     Example: {
                         'anatomy': ['Appendix', 'Cecum'],
                         'instruments': ['Scalpel', 'Forceps'],
                         'complications': ['Bleeding', 'Infection'],
                         'techniques': ['Laparoscopic'],
                         'medications': ['Antibiotics']
                     }
        """
        # Create procedure node
        self.create_procedure_node(procedure)
        
        # Define relationship mappings
        relationship_map = {
            'anatomy': ('INVOLVES', 'Anatomy'),
            'instruments': ('REQUIRES', 'Instrument'),
            'complications': ('MAY_CAUSE', 'Complication'),
            'techniques': ('USES_TECHNIQUE', 'Technique'),
            'medications': ('REQUIRES_MEDICATION', 'Medication')
        }
        
        # Create entities and relationships
        for entity_type, entity_list in entities.items():
            if entity_type in relationship_map:
                rel_type, node_label = relationship_map[entity_type]
                
                for entity_name in entity_list:
                    # Create entity node
                    self.create_entity_node(node_label, entity_name)
                    
                    # Create relationship
                    self.create_relationship(
                        procedure, entity_name,
                        rel_type, 'Procedure', node_label
                    )
        
        logger.info(f"Added procedure '{procedure}' with {sum(len(v) for v in entities.values())} related entities")
    
    def find_related_procedures(self, procedure: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Find procedures related through shared entities.
        
        Args:
            procedure: Source procedure name
            max_depth: Maximum traversal depth
        
        Returns:
            List of related procedures with relationship details
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (p1:Procedure {name: $procedure})-[*1..""" + str(max_depth) + """]->(p2:Procedure)
                WHERE p1 <> p2
                RETURN DISTINCT p2.name as procedure, 
                       length(path) as distance,
                       [rel in relationships(path) | type(rel)] as relationship_types
                ORDER BY distance
                LIMIT 10
            """, procedure=procedure)
            
            return [dict(record) for record in result]
    
    def get_procedure_context(self, procedure: str) -> Dict[str, Any]:
        """
        Get comprehensive context for a procedure including all related entities.
        
        Args:
            procedure: Procedure name
        
        Returns:
            Dictionary with all related entities organized by type
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Procedure {name: $procedure})
                OPTIONAL MATCH (p)-[:INVOLVES]->(a:Anatomy)
                OPTIONAL MATCH (p)-[:REQUIRES]->(i:Instrument)
                OPTIONAL MATCH (p)-[:MAY_CAUSE]->(c:Complication)
                OPTIONAL MATCH (p)-[:USES_TECHNIQUE]->(t:Technique)
                OPTIONAL MATCH (p)-[:REQUIRES_MEDICATION]->(m:Medication)
                RETURN 
                    p.name as procedure,
                    p.description as description,
                    collect(DISTINCT a.name) as anatomy,
                    collect(DISTINCT i.name) as instruments,
                    collect(DISTINCT c.name) as complications,
                    collect(DISTINCT t.name) as techniques,
                    collect(DISTINCT m.name) as medications
            """, procedure=procedure)
            
            record = result.single()
            if record:
                return {
                    'procedure': record['procedure'],
                    'description': record['description'],
                    'anatomy': [a for a in record['anatomy'] if a],
                    'instruments': [i for i in record['instruments'] if i],
                    'complications': [c for c in record['complications'] if c],
                    'techniques': [t for t in record['techniques'] if t],
                    'medications': [m for m in record['medications'] if m]
                }
            return {}
    
    def find_shortest_path(self, start_entity: str, end_entity: str, 
                          start_label: str, end_label: str) -> Optional[List[str]]:
        """
        Find shortest path between two entities in the graph.
        
        Args:
            start_entity: Starting entity name
            end_entity: Target entity name
            start_label: Label of start node
            end_label: Label of end node
        
        Returns:
            List of node names in the path, or None if no path exists
        """
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH path = shortestPath(
                    (start:{start_label} {{name: $start}})-[*]-(end:{end_label} {{name: $end}})
                )
                RETURN [node in nodes(path) | node.name] as path
            """, start=start_entity, end=end_entity)
            
            record = result.single()
            return record['path'] if record else None
    
    def get_graph_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the knowledge graph.
        
        Returns:
            Dictionary with node and relationship counts
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
            """)
            
            node_counts = {record['label']: record['count'] for record in result}
            
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(*) as count
            """)
            
            rel_counts = {record['rel_type']: record['count'] for record in result}
            
            return {
                'nodes': node_counts,
                'relationships': rel_counts,
                'total_nodes': sum(node_counts.values()),
                'total_relationships': sum(rel_counts.values())
            }
    
    def clear_graph(self):
        """Clear all nodes and relationships. USE WITH CAUTION!"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.warning("Graph database cleared")
    
    def close(self):
        """Close the database connection."""
        self.driver.close()
        logger.info("Neo4j connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
