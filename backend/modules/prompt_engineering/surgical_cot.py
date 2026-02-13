"""
Procedural Chain-of-Thought Prompting
Specialized prompting for surgical procedures that enforces procedural logic.
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SurgicalCoTPrompter:
    """
    Creates Chain-of-Thought prompts specifically for surgical procedures.
    
    Forces the model to:
    1. Identify the procedure and current phase
    2. List prerequisite steps
    3. Identify relevant anatomy from context
    4. Determine correct instruments
    5. Generate answer maintaining step-order consistency
    """
    
    def __init__(self):
        self.procedure_phases = [
            "pre-operative setup",
            "patient positioning",
            "access and exposure",
            "dissection",
            "resection/repair",
            "reconstruction",
            "closure",
            "post-operative care"
        ]
    
    def build_surgical_cot_prompt(self, 
                                 query: str, 
                                 contexts: List[Dict[str, Any]], 
                                 level: str = "Novice") -> str:
        """
        Build a surgical Chain-of-Thought prompt.
        
        Args:
            query: Original user query
            contexts: Retrieved context chunks
            level: Educational level (Novice/Intermediate/Advanced)
        
        Returns:
            Complete CoT prompt string
        """
        # Extract context text
        context_texts = "\n\n".join([
            c.get("metadata", {}).get("text", "") 
            for c in contexts
        ])
        
        # Build the CoT prompt
        prompt = f"""You are an expert surgical educator. You MUST follow this Chain-of-Thought reasoning process before answering.

EDUCATIONAL LEVEL: {level}

AVAILABLE CONTEXT FROM SURGICAL GUIDELINES:
{context_texts}

USER QUESTION:
{query}

===== CHAIN-OF-THOUGHT REASONING PROCESS =====

Step 1: PROCEDURE IDENTIFICATION
- What surgical procedure is being asked about?
- What phase of the procedure is relevant? ({', '.join(self.procedure_phases[:4])}, etc.)

Step 2: PREREQUISITE ANALYSIS
- What steps must be completed BEFORE the current step?
- What setup or positioning is required?
- Are there any contraindications to address?

Step 3: ANATOMICAL CONTEXT
- What anatomical structures are involved?
- What are the key anatomical landmarks?
- What structures must be identified or avoided?

Step 4: INSTRUMENT SELECTION
- What instruments are appropriate for this phase?
- Why are these instruments chosen? (tissue handling, visualization, etc.)

Step 5: PROCEDURAL LOGIC CHECK
- Does the step order make logical sense?
- Are all prerequisites satisfied?
- Are safety considerations addressed?

Step 6: GENERATE ANSWER
Based on the reasoning above and the provided context, generate a clear, accurate answer.

===== REQUIREMENTS =====
1. Base your answer ONLY on the provided context - do NOT add information not present in the context
2. Cite context sources when making specific claims
3. Maintain correct procedural step ordering
4. Include relevant anatomical details when available
5. Specify instruments with their PURPOSE when mentioned
6. Flag any safety considerations
7. Keep language appropriate for {level} level
8. If the context doesn't contain sufficient information, state this clearly

===== YOUR ANSWER =====
"""
        
        return prompt
    
    def build_step_ordering_cot_prompt(self,
                                      query: str,
                                      contexts: List[Dict[str, Any]],
                                      level: str = "Novice") -> str:
        """
        Build a CoT prompt specifically for step-ordering questions.
        
        Args:
            query: User query about procedure steps
            contexts: Retrieved contexts
            level: Educational level
        
        Returns:
            CoT prompt focused on step ordering
        """
        context_texts = "\n\n".join([
            c.get("metadata", {}).get("text", "") 
            for c in contexts
        ])
        
        prompt = f"""You are explaining surgical procedure steps to a {level} learner.

CONTEXT FROM GUIDELINES:
{context_texts}

QUESTION:
{query}

REASONING PROCESS:

1. IDENTIFY THE PROCEDURE and its standard phases

2. LIST STEPS IN ORDER:
   For each step, identify:
   - Step name/description
   - Which phase it belongs to
   - What must happen BEFORE this step
   - What happens AFTER this step

3. VERIFY LOGICAL FLOW:
   - Does each step follow logically from the previous?
   - Are anatomical relationships preserved?
   - Are safety steps in correct positions?

4. GENERATE STEP-BY-STEP ANSWER:
   Present steps in order with:
   - Clear numbering
   - Brief rationale
   - Key anatomical landmarks
   - Safety notes where relevant

Base your answer strictly on the provided context. If step ordering is not clear from context, state this.

YOUR ANSWER:
"""
        
        return prompt
    
    def build_instrument_cot_prompt(self,
                                   query: str,
                                   contexts: List[Dict[str, Any]],
                                   level: str = "Novice") -> str:
        """
        Build a CoT prompt specifically for instrument-related questions.
        
        Args:
            query: User query about instruments
            contexts: Retrieved contexts
            level: Educational level
        
        Returns:
            CoT prompt focused on instruments
        """
        context_texts = "\n\n".join([
            c.get("metadata", {}).get("text", "") 
            for c in contexts
        ])
        
        prompt = f"""You are explaining surgical instruments to a {level} learner.

CONTEXT FROM GUIDELINES:
{context_texts}

QUESTION:
{query}

REASONING PROCESS:

1. IDENTIFY THE PROCEDURE PHASE:
   - What phase of surgery is this? (dissection, resection, closure, etc.)
   - What tissue handling is required?

2. LIST INSTRUMENTS WITH PURPOSE:
   For each instrument mentioned in context:
   - Instrument name
   - Specific purpose in THIS procedure
   - When in the procedure it's used
   - Why this instrument vs alternatives

3. VERIFY APPROPRIATENESS:
   - Does the instrument match the tissue type?
   - Is it appropriate for the surgical approach?
   - Are there safety considerations?

4. GENERATE ANSWER:
   List instruments with clear explanations of usage.

Base your answer strictly on instruments mentioned in the provided context.

YOUR ANSWER:
"""
        
        return prompt
    
    def build_complication_cot_prompt(self,
                                     query: str,
                                     contexts: List[Dict[str, Any]],
                                     level: str = "Novice") -> str:
        """
        Build a CoT prompt for complication management questions.
        
        Args:
            query: User query about complications
            contexts: Retrieved contexts
            level: Educational level
        
        Returns:
            CoT prompt focused on complications
        """
        context_texts = "\n\n".join([
            c.get("metadata", {}).get("text", "") 
            for c in contexts
        ])
        
        prompt = f"""You are teaching complication management to a {level} learner.

CONTEXT FROM GUIDELINES:
{context_texts}

QUESTION:
{query}

REASONING PROCESS:

1. IDENTIFY THE COMPLICATION:
   - What is the specific complication?
   - When in the procedure does it occur?

2. RECOGNITION:
   - How is it identified?
   - What are the warning signs?

3. IMMEDIATE MANAGEMENT:
   - What are the immediate steps?
   - What is the priority sequence?

4. DEFINITIVE MANAGEMENT:
   - What is the long-term solution?
   - When is specialist consultation needed?

5. PREVENTION:
   - How can this complication be avoided?
   - What are the risk factors?

Base your answer on the provided context. For emergency situations, emphasize the need for expert supervision.

YOUR ANSWER:
"""
        
        return prompt
    
    def select_appropriate_prompt_type(self, query: str) -> str:
        """
        Determine which CoT prompt type is most appropriate for the query.
        
        Args:
            query: User query
        
        Returns:
            Prompt type: 'general', 'steps', 'instruments', or 'complications'
        """
        query_lower = query.lower()
        
        # Check for step-ordering queries
        step_indicators = ['steps', 'sequence', 'order', 'procedure', 'how to perform']
        if any(indicator in query_lower for indicator in step_indicators):
            return 'steps'
        
        # Check for instrument queries
        instrument_indicators = ['instrument', 'tool', 'equipment', 'what do you use']
        if any(indicator in query_lower for indicator in instrument_indicators):
            return 'instruments'
        
        # Check for complication queries
        complication_indicators = ['complication', 'manage', 'problem', 'injury', 'bleeding', 'perforation']
        if any(indicator in query_lower for indicator in complication_indicators):
            return 'complications'
        
        # Default to general surgical CoT
        return 'general'
    
    def build_adaptive_cot_prompt(self,
                                 query: str,
                                 contexts: List[Dict[str, Any]],
                                 level: str = "Novice") -> str:
        """
        Automatically select and build the most appropriate CoT prompt.
        
        Args:
            query: User query
            contexts: Retrieved contexts
            level: Educational level
        
        Returns:
            Appropriate CoT prompt
        """
        prompt_type = self.select_appropriate_prompt_type(query)
        
        logger.info(f"Selected CoT prompt type: {prompt_type}")
        
        if prompt_type == 'steps':
            return self.build_step_ordering_cot_prompt(query, contexts, level)
        elif prompt_type == 'instruments':
            return self.build_instrument_cot_prompt(query, contexts, level)
        elif prompt_type == 'complications':
            return self.build_complication_cot_prompt(query, contexts, level)
        else:
            return self.build_surgical_cot_prompt(query, contexts, level)
