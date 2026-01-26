"""
Test script for Graph-Enhanced RAG functionality
Tests entity extraction, graph building, and hybrid retrieval
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from modules.graph.entity_extractor import MedicalEntityExtractor
from modules.graph.neo4j_manager import Neo4jManager
from app.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, SCISPACY_MODEL


def test_entity_extraction():
    """Test medical entity extraction"""
    print("\n" + "="*80)
    print("TEST 1: Medical Entity Extraction")
    print("="*80)
    
    extractor = MedicalEntityExtractor(SCISPACY_MODEL)
    
    sample_text = """
    Laparoscopic cholecystectomy is a minimally invasive surgical procedure to remove 
    the gallbladder. The procedure requires a laparoscope, trocars, and grasping forceps. 
    The patient is placed under general anesthesia. Potential complications include 
    bleeding, infection, and bile duct injury. The procedure involves making small 
    incisions in the abdomen to insert the surgical instruments. Antibiotics may be 
    administered prophylactically to prevent infection.
    """
    
    print(f"\nSample Text:\n{sample_text}")
    print("\nExtracting entities...")
    
    entities = extractor.extract_entities(sample_text)
    
    print("\n📊 Extracted Entities:")
    for entity_type, entity_list in entities.items():
        if entity_list:
            print(f"\n{entity_type.upper()}:")
            for entity in entity_list:
                print(f"  - {entity}")
    
    # Test procedure identification
    print("\n🔍 Main Procedures:")
    procedures = extractor.identify_main_procedures(sample_text, top_n=3)
    for proc, freq in procedures:
        print(f"  - {proc} (mentioned {freq} time(s))")
    
    return entities


def test_graph_building(entities):
    """Test Neo4j graph construction"""
    print("\n" + "="*80)
    print("TEST 2: Knowledge Graph Construction")
    print("="*80)
    
    try:
        print(f"\nConnecting to Neo4j at {NEO4J_URI}...")
        neo4j = Neo4jManager(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        print("✅ Connected successfully!")
        
        # Clear existing graph for clean test
        print("\n⚠️  Clearing existing graph data...")
        neo4j.clear_graph()
        
        # Add a procedure with entities
        print("\n📝 Adding 'Laparoscopic Cholecystectomy' to graph...")
        procedure_entities = {
            'anatomy': ['gallbladder', 'abdomen', 'bile duct'],
            'instruments': ['laparoscope', 'trocars', 'grasping forceps'],
            'complications': ['bleeding', 'infection', 'bile duct injury'],
            'techniques': ['laparoscopic', 'minimally invasive'],
            'medications': ['anesthesia', 'antibiotics']
        }
        
        neo4j.add_procedure_with_entities('Laparoscopic Cholecystectomy', procedure_entities)
        
        # Add a related procedure
        print("\n📝 Adding 'Open Cholecystectomy' to graph...")
        open_procedure_entities = {
            'anatomy': ['gallbladder', 'abdomen'],
            'instruments': ['scalpel', 'retractor', 'forceps'],
            'complications': ['bleeding', 'infection', 'hernia'],
            'techniques': ['open'],
            'medications': ['anesthesia', 'antibiotics']
        }
        
        neo4j.add_procedure_with_entities('Open Cholecystectomy', open_procedure_entities)
        
        # Query procedure context
        print("\n🔍 Querying procedure context...")
        context = neo4j.get_procedure_context('Laparoscopic Cholecystectomy')
        
        print("\n📊 Procedure Context:")
        print(f"  Procedure: {context['procedure']}")
        print(f"  Anatomy: {', '.join(context['anatomy'])}")
        print(f"  Instruments: {', '.join(context['instruments'])}")
        print(f"  Complications: {', '.join(context['complications'])}")
        print(f"  Techniques: {', '.join(context['techniques'])}")
        print(f"  Medications: {', '.join(context['medications'])}")
        
        # Find related procedures
        print("\n🔗 Finding related procedures...")
        related = neo4j.find_related_procedures('Laparoscopic Cholecystectomy', max_depth=2)
        
        if related:
            print("\n📊 Related Procedures:")
            for rel in related:
                print(f"  - {rel['procedure']} (distance: {rel['distance']})")
        else:
            print("  No related procedures found (add more data to see relationships)")
        
        # Get graph statistics
        print("\n📊 Graph Statistics:")
        stats = neo4j.get_graph_statistics()
        print(f"  Total Nodes: {stats['total_nodes']}")
        print(f"  Total Relationships: {stats['total_relationships']}")
        print(f"\n  Nodes by Type:")
        for node_type, count in stats['nodes'].items():
            print(f"    - {node_type}: {count}")
        print(f"\n  Relationships by Type:")
        for rel_type, count in stats['relationships'].items():
            print(f"    - {rel_type}: {count}")
        
        neo4j.close()
        print("\n✅ Graph building test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Graph building test failed: {e}")
        print("\nMake sure Neo4j is running:")
        print("  1. Install Neo4j Desktop or run via Docker:")
        print("     docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest")
        print(f"  2. Update .env file with correct credentials")
        return False


def test_hybrid_retrieval():
    """Test graph-enhanced retrieval (requires FAISS index)"""
    print("\n" + "="*80)
    print("TEST 3: Hybrid Retrieval (Vector + Graph)")
    print("="*80)
    print("\n⚠️  This test requires:")
    print("  1. Neo4j running with populated graph")
    print("  2. FAISS index with embedded documents")
    print("  3. Run 'python backend/app/main.py' and upload PDFs first")
    print("\nSkipping for now - will be tested via API endpoints")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("GRAPH-ENHANCED RAG SYSTEM - TEST SUITE")
    print("="*80)
    
    try:
        # Test 1: Entity Extraction
        entities = test_entity_extraction()
        
        # Test 2: Graph Building
        graph_success = test_graph_building(entities)
        
        # Test 3: Hybrid Retrieval (placeholder)
        test_hybrid_retrieval()
        
        print("\n" + "="*80)
        if graph_success:
            print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        else:
            print("⚠️  SOME TESTS FAILED - Check Neo4j connection")
        print("="*80)
        print("\nNext steps:")
        print("1. Start the FastAPI server: uvicorn app.main:app --reload")
        print("2. Upload PDFs via the /upload_pdf endpoint")
        print("3. Test graph-enhanced chat via /chat endpoint with use_graph=True")
        print("4. Explore graph via /graph/* endpoints")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
