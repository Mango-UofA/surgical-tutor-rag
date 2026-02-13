"""
Source Attribution and Traceability
Tracks and cites sources for all claims in generated answers.
"""

from typing import List, Dict, Any, Optional, Set
import re
import logging

logger = logging.getLogger(__name__)


class SourceAttributor:
    """
    Adds inline source citations to generated answers and prevents citation hallucination.
    
    Features:
    1. Tags retrieved chunks with source IDs
    2. Instructs LLM to cite sources inline
    3. Post-processes to verify cited sources exist
    4. Adds graph relationship citations
    """
    
    def __init__(self):
        self.source_id_pattern = re.compile(r'\[([A-Z0-9\-_]+(?::[A-Z0-9\-_]+)?)\]')
    
    def prepare_contexts_with_source_ids(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add source IDs to context chunks for citation.
        
        Args:
            contexts: Retrieved context chunks
        
        Returns:
            Contexts with added source_id field
        """
        attributed_contexts = []
        
        for idx, context in enumerate(contexts):
            context_copy = context.copy()
            metadata = context_copy.get('metadata', {})
            
            # Generate source ID from document name and chunk index
            doc_name = metadata.get('source', 'Unknown')
            # Create short identifier
            doc_id = self._create_doc_id(doc_name)
            chunk_id = metadata.get('id', idx)
            
            source_id = f"{doc_id}-{chunk_id}"
            
            context_copy['source_id'] = source_id
            context_copy['metadata']['source_id'] = source_id
            
            attributed_contexts.append(context_copy)
        
        return attributed_contexts
    
    def build_prompt_with_citations(self, 
                                    query: str,
                                    contexts: List[Dict[str, Any]],
                                    level: str = "Novice",
                                    base_prompt: str = "") -> str:
        """
        Build prompt that instructs model to cite sources.
        
        Args:
            query: User query
            contexts: Contexts with source IDs
            level: Educational level
            base_prompt: Base prompt to extend (optional)
        
        Returns:
            Prompt with citation instructions
        """
        # Build context with source IDs
        context_sections = []
        for ctx in contexts:
            source_id = ctx.get('source_id', 'UNKNOWN')
            text = ctx.get('metadata', {}).get('text', '')
            context_sections.append(f"[{source_id}]\n{text}\n")
        
        context_text = "\n".join(context_sections)
        
        if base_prompt:
            # Extend existing prompt with citation instructions
            prompt = base_prompt
        else:
            # Create new prompt
            prompt = f"""You are an educational surgical tutor. Do NOT provide clinical advice.
Educational Level: {level}

CONTEXT WITH SOURCE IDs:
{context_text}

USER QUESTION:
{query}

"""
        
        # Add citation instructions
        prompt += """
CITATION REQUIREMENTS:
1. You MUST cite sources inline using the format [SOURCE-ID] after each factual claim
2. Only cite source IDs that appear in the context above
3. If a claim comes from multiple sources, cite all relevant IDs: [SOURCE1][SOURCE2]
4. Do NOT invent or hallucinate source IDs
5. If information is not in the provided context, explicitly state this

Example:
"The first step is to create the pneumoperitoneum [ACS-LC-1]. A Veress needle is inserted at the umbilicus [SAGES-2.1][ACS-LC-1]."

Generate your answer with proper inline citations:
"""
        
        return prompt
    
    def add_graph_citations(self, 
                           answer: str,
                           graph_relationships: List[Dict[str, Any]]) -> str:
        """
        Add citations for facts derived from graph relationships.
        
        Args:
            answer: Generated answer
            graph_relationships: List of graph relationships used
        
        Returns:
            Answer with graph citations added
        """
        if not graph_relationships:
            return answer
        
        # Append graph sources at end
        graph_citations = "\n\nKnowledge Graph Sources:\n"
        for rel in graph_relationships:
            rel_type = rel.get('relationship_type', 'RELATED')
            source = rel.get('source_node', '')
            target = rel.get('target_node', '')
            graph_citations += f"  • {source} {rel_type} {target}\n"
        
        return answer + graph_citations
    
    def verify_citations(self, answer: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify that all cited source IDs exist in the retrieved contexts.
        Detects citation hallucination.
        
        Args:
            answer: Generated answer with citations
            contexts: Retrieved contexts with source IDs
        
        Returns:
            Dictionary with verification results:
            {
                'valid_citations': List[str],
                'invalid_citations': List[str],
                'uncited_sources': List[str],
                'citation_accuracy': float,
                'hallucination_detected': bool
            }
        """
        # Extract all source IDs from contexts
        valid_source_ids = {ctx.get('source_id', '') for ctx in contexts if ctx.get('source_id')}
        
        # Extract all cited source IDs from answer
        cited_ids = set(self.source_id_pattern.findall(answer))
        
        # Find valid and invalid citations
        valid_citations = cited_ids.intersection(valid_source_ids)
        invalid_citations = cited_ids - valid_source_ids
        
        # Find sources that were provided but not cited
        uncited_sources = valid_source_ids - cited_ids
        
        # Calculate accuracy
        total_cited = len(cited_ids)
        citation_accuracy = len(valid_citations) / total_cited if total_cited > 0 else 1.0
        
        # Detect hallucination
        hallucination_detected = len(invalid_citations) > 0
        
        result = {
            'valid_citations': sorted(list(valid_citations)),
            'invalid_citations': sorted(list(invalid_citations)),
            'uncited_sources': sorted(list(uncited_sources)),
            'citation_accuracy': citation_accuracy,
            'hallucination_detected': hallucination_detected,
            'total_citations': total_cited,
            'valid_sources_available': len(valid_source_ids)
        }
        
        if hallucination_detected:
            logger.warning(f"Citation hallucination detected! Invalid citations: {invalid_citations}")
        
        return result
    
    def remove_invalid_citations(self, answer: str, verification: Dict[str, Any]) -> str:
        """
        Remove hallucinated citations from answer.
        
        Args:
            answer: Answer with citations
            verification: Result from verify_citations()
        
        Returns:
            Answer with invalid citations removed
        """
        if not verification.get('hallucination_detected'):
            return answer
        
        cleaned = answer
        for invalid_id in verification['invalid_citations']:
            # Remove the invalid citation
            cleaned = cleaned.replace(f"[{invalid_id}]", "[SOURCE-NOT-FOUND]")
        
        return cleaned
    
    def format_source_list(self, contexts: List[Dict[str, Any]]) -> str:
        """
        Generate a formatted list of sources for appendix.
        
        Args:
            contexts: Contexts with source IDs
        
        Returns:
            Formatted source list
        """
        sources_text = "\n\nSOURCES:\n"
        
        for ctx in contexts:
            source_id = ctx.get('source_id', 'UNKNOWN')
            metadata = ctx.get('metadata', {})
            doc_name = metadata.get('source', 'Unknown Document')
            title = metadata.get('title', '')
            
            if title and title != doc_name:
                sources_text += f"[{source_id}] {title} (from {doc_name})\n"
            else:
                sources_text += f"[{source_id}] {doc_name}\n"
        
        return sources_text
    
    def create_traceability_report(self, 
                                   query: str,
                                   answer: str,
                                   contexts: List[Dict[str, Any]],
                                   verification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive traceability report.
        
        Args:
            query: Original query
            answer: Generated answer
            contexts: Retrieved contexts
            verification: Citation verification results
        
        Returns:
            Traceability report
        """
        report = {
            'query': query,
            'sources_retrieved': len(contexts),
            'sources_cited': len(verification['valid_citations']),
            'citation_accuracy': verification['citation_accuracy'],
            'hallucination_detected': verification['hallucination_detected'],
            'source_details': []
        }
        
        # Add details for each source
        for ctx in contexts:
            source_id = ctx.get('source_id', '')
            was_cited = source_id in verification['valid_citations']
            
            report['source_details'].append({
                'source_id': source_id,
                'document': ctx.get('metadata', {}).get('source', ''),
                'cited': was_cited,
                'retrieval_score': ctx.get('score', 0.0)
            })
        
        return report
    
    def _create_doc_id(self, doc_name: str) -> str:
        """
        Create short document identifier from name.
        
        Args:
            doc_name: Full document name
        
        Returns:
            Short ID (e.g., "ACS-LC" from "ACS_Laparoscopic_Cholecystectomy.pdf")
        """
        # Remove extension
        doc_name = doc_name.replace('.pdf', '').replace('.txt', '')
        
        # Split on separators
        parts = re.split(r'[_\-\s]+', doc_name)
        
        # Take first letters of first 2-3 words
        if len(parts) >= 2:
            doc_id = ''.join([p[0].upper() for p in parts[:min(3, len(parts))]])
        else:
            doc_id = doc_name[:3].upper()
        
        return doc_id
