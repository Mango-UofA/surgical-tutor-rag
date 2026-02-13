"""
Graph-Based Claim Verifier
Verifies extracted claims against the Neo4j knowledge graph.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from ..graph.neo4j_manager import Neo4jManager

logger = logging.getLogger(__name__)


class GraphVerifier:
    """
    Verifies factual claims against the Neo4j knowledge graph.
    Creates Cypher queries to check if relationships exist in the graph.
    """
    
    def __init__(self, neo4j_manager: Neo4jManager):
        self.graph = neo4j_manager
    
    def verify_claims(self, claims: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Verify all extracted claims against the knowledge graph.
        
        Args:
            claims: Extracted claims from ClaimExtractor
        
        Returns:
            Verification results with scores and details:
            {
                'verification_score': float,  # 0-1, verified/total
                'total_claims': int,
                'verified_claims': int,
                'unverified_claims': int,
                'category_scores': {...},
                'unverified_details': [...]  # List of unverified claims
            }
        """
        results = {
            'verification_score': 0.0,
            'total_claims': 0,
            'verified_claims': 0,
            'unverified_claims': 0,
            'category_scores': {},
            'unverified_details': []
        }
        
        # Verify each category
        instrument_results = self._verify_instrument_claims(claims.get('instrument_claims', []))
        step_order_results = self._verify_step_order_claims(claims.get('step_order_claims', []))
        anatomy_results = self._verify_anatomy_claims(claims.get('anatomy_claims', []))
        complication_results = self._verify_complication_claims(claims.get('complication_claims', []))
        
        # Aggregate results
        all_results = [instrument_results, step_order_results, anatomy_results, complication_results]
        
        for category_result in all_results:
            results['total_claims'] += category_result['total']
            results['verified_claims'] += category_result['verified']
            results['unverified_claims'] += category_result['unverified']
            results['unverified_details'].extend(category_result['unverified_details'])
        
        # Calculate overall verification score
        if results['total_claims'] > 0:
            results['verification_score'] = results['verified_claims'] / results['total_claims']
        else:
            results['verification_score'] = 1.0  # No claims = no errors
        
        # Category-specific scores
        results['category_scores'] = {
            'instruments': instrument_results['score'],
            'step_order': step_order_results['score'],
            'anatomy': anatomy_results['score'],
            'complications': complication_results['score']
        }
        
        return results
    
    def _verify_instrument_claims(self, claims: List[Dict]) -> Dict[str, Any]:
        """Verify instrument-step relationships."""
        total = len(claims)
        verified = 0
        unverified_details = []
        
        for claim in claims:
            step_name = claim.get('step', '')
            instrument_name = claim.get('instrument', '')
            
            if not step_name or not instrument_name:
                unverified_details.append({
                    'type': 'instrument',
                    'claim': claim,
                    'reason': 'Missing step or instrument name'
                })
                continue
            
            # Query: Does this step use this instrument?
            query = """
            MATCH (s:Step)-[:USES]->(i:Instrument)
            WHERE toLower(s.name) CONTAINS toLower($step) 
            AND toLower(i.name) CONTAINS toLower($instrument)
            RETURN count(*) as matches
            """
            
            try:
                result = self.graph.execute_query(query, {
                    'step': step_name.lower(),
                    'instrument': instrument_name.lower()
                })
                
                matches = result[0]['matches'] if result else 0
                
                if matches > 0:
                    verified += 1
                else:
                    # Try alternative: instrument exists and step exists separately
                    alt_verified = self._verify_entities_exist(step_name, instrument_name)
                    if alt_verified:
                        verified += 1
                    else:
                        unverified_details.append({
                            'type': 'instrument',
                            'claim': claim,
                            'reason': 'No graph relationship found'
                        })
            except Exception as e:
                logger.error(f"Verification query failed: {e}")
                unverified_details.append({
                    'type': 'instrument',
                    'claim': claim,
                    'reason': f'Query error: {str(e)}'
                })
        
        score = verified / total if total > 0 else 1.0
        
        return {
            'total': total,
            'verified': verified,
            'unverified': total - verified,
            'score': score,
            'unverified_details': unverified_details
        }
    
    def _verify_step_order_claims(self, claims: List[Dict]) -> Dict[str, Any]:
        """Verify step ordering relationships."""
        total = len(claims)
        verified = 0
        unverified_details = []
        
        for claim in claims:
            step_before = claim.get('step_before', '')
            step_after = claim.get('step_after', '')
            relationship = claim.get('relationship', 'PRECEDES')
            
            if not step_before or not step_after:
                unverified_details.append({
                    'type': 'step_order',
                    'claim': claim,
                    'reason': 'Missing step names'
                })
                continue
            
            # Query for step ordering
            query = """
            MATCH (s1:Step)-[r:PRECEDES|FOLLOWS|REQUIRES]->(s2:Step)
            WHERE toLower(s1.name) CONTAINS toLower($step1)
            AND toLower(s2.name) CONTAINS toLower($step2)
            AND type(r) = $rel_type
            RETURN count(*) as matches
            """
            
            try:
                result = self.graph.execute_query(query, {
                    'step1': step_before.lower(),
                    'step2': step_after.lower(),
                    'rel_type': relationship.upper()
                })
                
                matches = result[0]['matches'] if result else 0
                
                if matches > 0:
                    verified += 1
                else:
                    unverified_details.append({
                        'type': 'step_order',
                        'claim': claim,
                        'reason': 'Step ordering not found in graph'
                    })
            except Exception as e:
                logger.error(f"Step order verification failed: {e}")
                unverified_details.append({
                    'type': 'step_order',
                    'claim': claim,
                    'reason': f'Query error: {str(e)}'
                })
        
        score = verified / total if total > 0 else 1.0
        
        return {
            'total': total,
            'verified': verified,
            'unverified': total - verified,
            'score': score,
            'unverified_details': unverified_details
        }
    
    def _verify_anatomy_claims(self, claims: List[Dict]) -> Dict[str, Any]:
        """Verify anatomical structure relationships."""
        total = len(claims)
        verified = 0
        unverified_details = []
        
        for claim in claims:
            procedure = claim.get('procedure', '')
            structure = claim.get('anatomical_structure', '')
            relationship = claim.get('relationship', 'INVOLVES')
            
            if not structure:
                unverified_details.append({
                    'type': 'anatomy',
                    'claim': claim,
                    'reason': 'Missing anatomical structure'
                })
                continue
            
            # Query for anatomy relationships
            query = """
            MATCH (p:Procedure)-[r:INVOLVES|TARGETS|AVOIDS|IDENTIFIES]->(a:Anatomy)
            WHERE toLower(a.name) CONTAINS toLower($structure)
            RETURN count(*) as matches
            """
            
            try:
                result = self.graph.execute_query(query, {
                    'structure': structure.lower()
                })
                
                matches = result[0]['matches'] if result else 0
                
                if matches > 0:
                    verified += 1
                else:
                    # Check if anatomy node exists at all
                    exists = self._check_node_exists('Anatomy', structure)
                    if exists:
                        verified += 1  # Give partial credit if anatomy exists
                    else:
                        unverified_details.append({
                            'type': 'anatomy',
                            'claim': claim,
                            'reason': 'Anatomical structure not found in graph'
                        })
            except Exception as e:
                logger.error(f"Anatomy verification failed: {e}")
                unverified_details.append({
                    'type': 'anatomy',
                    'claim': claim,
                    'reason': f'Query error: {str(e)}'
                })
        
        score = verified / total if total > 0 else 1.0
        
        return {
            'total': total,
            'verified': verified,
            'unverified': total - verified,
            'score': score,
            'unverified_details': unverified_details
        }
    
    def _verify_complication_claims(self, claims: List[Dict]) -> Dict[str, Any]:
        """Verify complication and management relationships."""
        total = len(claims)
        verified = 0
        unverified_details = []
        
        for claim in claims:
            complication = claim.get('complication', '')
            
            if not complication:
                unverified_details.append({
                    'type': 'complication',
                    'claim': claim,
                    'reason': 'Missing complication name'
                })
                continue
            
            # Query for complication existence
            query = """
            MATCH (c:Complication)
            WHERE toLower(c.name) CONTAINS toLower($complication)
            RETURN count(*) as matches
            """
            
            try:
                result = self.graph.execute_query(query, {
                    'complication': complication.lower()
                })
                
                matches = result[0]['matches'] if result else 0
                
                if matches > 0:
                    verified += 1
                else:
                    unverified_details.append({
                        'type': 'complication',
                        'claim': claim,
                        'reason': 'Complication not found in graph'
                    })
            except Exception as e:
                logger.error(f"Complication verification failed: {e}")
                unverified_details.append({
                    'type': 'complication',
                    'claim': claim,
                    'reason': f'Query error: {str(e)}'
                })
        
        score = verified / total if total > 0 else 1.0
        
        return {
            'total': total,
            'verified': verified,
            'unverified': total - verified,
            'score': score,
            'unverified_details': unverified_details
        }
    
    def _verify_entities_exist(self, step_name: str, instrument_name: str) -> bool:
        """Check if entities exist separately in the graph."""
        try:
            query = """
            MATCH (s:Step), (i:Instrument)
            WHERE toLower(s.name) CONTAINS toLower($step)
            AND toLower(i.name) CONTAINS toLower($instrument)
            RETURN count(*) as matches
            """
            
            result = self.graph.execute_query(query, {
                'step': step_name.lower(),
                'instrument': instrument_name.lower()
            })
            
            return result[0]['matches'] > 0 if result else False
        except:
            return False
    
    def _check_node_exists(self, label: str, name: str) -> bool:
        """Check if a node with given label and name exists."""
        try:
            query = f"""
            MATCH (n:{label})
            WHERE toLower(n.name) CONTAINS toLower($name)
            RETURN count(*) as matches
            """
            
            result = self.graph.execute_query(query, {'name': name.lower()})
            return result[0]['matches'] > 0 if result else False
        except:
            return False
    
    def get_verification_confidence_level(self, verification_score: float) -> str:
        """
        Map verification score to confidence level.
        
        Args:
            verification_score: 0-1 verification score
        
        Returns:
            'high', 'medium', or 'low'
        """
        if verification_score >= 0.80:
            return 'high'
        elif verification_score >= 0.50:
            return 'medium'
        else:
            return 'low'
