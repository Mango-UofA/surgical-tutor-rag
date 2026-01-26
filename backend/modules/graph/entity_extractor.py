"""
Medical Entity Extractor
Uses ScispaCy and custom patterns to extract medical entities from surgical texts.
Identifies procedures, anatomy, instruments, complications, and techniques.
"""

import spacy
from spacy.matcher import PhraseMatcher
from typing import Dict, List, Set, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class MedicalEntityExtractor:
    """
    Extracts medical entities from surgical procedure text using:
    1. ScispaCy NER model (biomedical named entity recognition)
    2. Custom dictionaries for surgical domain
    3. Pattern matching for specific medical terms
    """
    
    def __init__(self, model_name: str = "en_core_sci_md"):
        """
        Initialize the medical entity extractor.
        
        Args:
            model_name: ScispaCy model name (en_core_sci_sm, en_core_sci_md, en_core_sci_lg)
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded ScispaCy model: {model_name}")
        except OSError:
            logger.error(f"ScispaCy model '{model_name}' not found. Run: pip install {model_name}")
            raise
        
        # Initialize phrase matcher for custom terms
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Load custom medical dictionaries
        self._load_surgical_dictionaries()
        self._add_custom_patterns()
    
    def _load_surgical_dictionaries(self):
        """Load curated lists of surgical terms."""
        
        # Common surgical procedures
        self.procedures = {
            'appendectomy', 'cholecystectomy', 'colectomy', 'gastrectomy',
            'mastectomy', 'hysterectomy', 'prostatectomy', 'nephrectomy',
            'splenectomy', 'thyroidectomy', 'laparoscopy', 'arthroscopy',
            'craniotomy', 'thoracotomy', 'laparotomy', 'cesarean section',
            'hernia repair', 'bypass surgery', 'angioplasty', 'amputation',
            'biopsy', 'debridement', 'excision', 'resection', 'anastomosis',
            'tracheostomy', 'colostomy', 'ileostomy', 'catheterization'
        }
        
        # Anatomical structures commonly involved in surgery
        self.anatomy = {
            'appendix', 'gallbladder', 'colon', 'stomach', 'intestine',
            'liver', 'pancreas', 'spleen', 'kidney', 'bladder', 'uterus',
            'prostate', 'breast', 'thyroid', 'heart', 'lung', 'brain',
            'spine', 'bone', 'muscle', 'tendon', 'ligament', 'cartilage',
            'artery', 'vein', 'nerve', 'skin', 'fascia', 'peritoneum',
            'pleura', 'pericardium', 'esophagus', 'trachea', 'bronchus',
            'duodenum', 'jejunum', 'ileum', 'cecum', 'rectum', 'anus'
        }
        
        # Surgical instruments
        self.instruments = {
            'scalpel', 'forceps', 'scissors', 'retractor', 'clamp', 'needle',
            'suture', 'stapler', 'cautery', 'electrocautery', 'laser',
            'laparoscope', 'endoscope', 'trocar', 'dilator', 'probe',
            'curette', 'drain', 'catheter', 'speculum', 'syringe',
            'aspirator', 'irrigator', 'ultrasound', 'microscope', 'drill',
            'saw', 'chisel', 'hammer', 'tourniquet', 'compress'
        }
        
        # Common complications
        self.complications = {
            'bleeding', 'hemorrhage', 'infection', 'sepsis', 'abscess',
            'perforation', 'leak', 'fistula', 'stenosis', 'obstruction',
            'ileus', 'adhesion', 'hernia', 'dehiscence', 'necrosis',
            'thrombosis', 'embolism', 'stroke', 'infarction', 'ischemia',
            'pneumonia', 'atelectasis', 'edema', 'hematoma', 'seroma',
            'pain', 'nausea', 'vomiting', 'fever', 'shock', 'death'
        }
        
        # Surgical techniques and approaches
        self.techniques = {
            'laparoscopic', 'open', 'minimally invasive', 'robotic',
            'endoscopic', 'percutaneous', 'transabdominal', 'transthoracic',
            'anterior', 'posterior', 'lateral', 'medial', 'proximal', 'distal',
            'radical', 'partial', 'total', 'complete', 'incomplete',
            'primary', 'secondary', 'elective', 'emergency', 'urgent'
        }
        
        # Medications commonly used in surgery
        self.medications = {
            'antibiotic', 'antibiotics', 'anesthesia', 'anesthetic',
            'analgesic', 'painkiller', 'opioid', 'morphine', 'fentanyl',
            'anticoagulant', 'heparin', 'warfarin', 'aspirin',
            'steroid', 'corticosteroid', 'insulin', 'saline',
            'epinephrine', 'atropine', 'propofol', 'midazolam',
            'cefazolin', 'metronidazole', 'gentamicin', 'vancomycin'
        }
    
    def _add_custom_patterns(self):
        """Add custom phrase patterns to the matcher."""
        
        # Add patterns for each entity type
        pattern_dict = {
            'PROCEDURE': self.procedures,
            'ANATOMY': self.anatomy,
            'INSTRUMENT': self.instruments,
            'COMPLICATION': self.complications,
            'TECHNIQUE': self.techniques,
            'MEDICATION': self.medications
        }
        
        for label, terms in pattern_dict.items():
            patterns = [self.nlp.make_doc(text) for text in terms]
            self.matcher.add(label, patterns)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract all medical entities from text.
        
        Args:
            text: Input medical text
        
        Returns:
            Dictionary with entity types as keys and lists of entity names as values
        """
        doc = self.nlp(text.lower())
        
        entities = {
            'procedures': set(),
            'anatomy': set(),
            'instruments': set(),
            'complications': set(),
            'techniques': set(),
            'medications': set()
        }
        
        # Extract using ScispaCy NER
        for ent in doc.ents:
            entity_text = ent.text.strip()
            
            # Map ScispaCy labels to our categories
            if ent.label_ in ['PROCEDURE', 'TREATMENT']:
                entities['procedures'].add(entity_text)
            elif ent.label_ in ['ANATOMY', 'ORGAN', 'TISSUE']:
                entities['anatomy'].add(entity_text)
            elif ent.label_ in ['DEVICE', 'EQUIPMENT']:
                entities['instruments'].add(entity_text)
            elif ent.label_ in ['DISEASE', 'SYMPTOM', 'ADVERSE_EVENT']:
                entities['complications'].add(entity_text)
            elif ent.label_ in ['MEDICATION', 'DRUG', 'CHEMICAL']:
                entities['medications'].add(entity_text)
        
        # Extract using custom phrase matcher
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span_text = doc[start:end].text
            
            if label == 'PROCEDURE':
                entities['procedures'].add(span_text)
            elif label == 'ANATOMY':
                entities['anatomy'].add(span_text)
            elif label == 'INSTRUMENT':
                entities['instruments'].add(span_text)
            elif label == 'COMPLICATION':
                entities['complications'].add(span_text)
            elif label == 'TECHNIQUE':
                entities['techniques'].add(span_text)
            elif label == 'MEDICATION':
                entities['medications'].add(span_text)
        
        # Convert sets to sorted lists
        result = {key: sorted(list(value)) for key, value in entities.items()}
        
        logger.info(f"Extracted {sum(len(v) for v in result.values())} entities from text")
        return result
    
    def extract_procedure_specific_entities(self, text: str, procedure: str) -> Dict[str, List[str]]:
        """
        Extract entities specifically related to a given procedure.
        
        Args:
            text: Input text
            procedure: Procedure name to focus on
        
        Returns:
            Filtered entities related to the procedure
        """
        # Extract all entities
        all_entities = self.extract_entities(text)
        
        # Filter entities that appear in context with the procedure
        doc = self.nlp(text.lower())
        procedure_doc = self.nlp(procedure.lower())
        
        # Find sentences containing the procedure
        procedure_sentences = []
        for sent in doc.sents:
            if procedure.lower() in sent.text.lower():
                procedure_sentences.append(sent.text)
        
        # Re-extract entities from procedure-specific sentences
        if procedure_sentences:
            context_text = " ".join(procedure_sentences)
            return self.extract_entities(context_text)
        
        return all_entities
    
    def identify_main_procedures(self, text: str, top_n: int = 3) -> List[Tuple[str, int]]:
        """
        Identify the main procedures discussed in the text.
        
        Args:
            text: Input text
            top_n: Number of top procedures to return
        
        Returns:
            List of (procedure, frequency) tuples
        """
        entities = self.extract_entities(text)
        procedures = entities['procedures']
        
        # Count occurrences
        doc = self.nlp(text.lower())
        procedure_counts = {}
        
        for proc in procedures:
            count = text.lower().count(proc)
            if count > 0:
                procedure_counts[proc] = count
        
        # Sort by frequency
        sorted_procedures = sorted(
            procedure_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return sorted_procedures[:top_n]
    
    def extract_relationships(self, text: str) -> List[Dict[str, str]]:
        """
        Extract relationships between entities using dependency parsing.
        
        Args:
            text: Input text
        
        Returns:
            List of relationship dictionaries
        """
        doc = self.nlp(text)
        relationships = []
        
        # Extract entities first
        entities = self.extract_entities(text)
        
        # Look for common relationship patterns
        # Example: "procedure requires instrument"
        # Example: "procedure may cause complication"
        
        for sent in doc.sents:
            # Find verbs that indicate relationships
            for token in sent:
                if token.pos_ == "VERB":
                    # Get subject and object
                    subjects = [child for child in token.children if child.dep_ in ['nsubj', 'nsubjpass']]
                    objects = [child for child in token.children if child.dep_ in ['dobj', 'pobj']]
                    
                    for subj in subjects:
                        for obj in objects:
                            relationships.append({
                                'subject': subj.text,
                                'verb': token.text,
                                'object': obj.text,
                                'sentence': sent.text
                            })
        
        return relationships
    
    def get_entity_context(self, text: str, entity: str, window: int = 50) -> List[str]:
        """
        Get context snippets around mentions of an entity.
        
        Args:
            text: Input text
            entity: Entity to find
            window: Number of characters around entity
        
        Returns:
            List of context snippets
        """
        contexts = []
        entity_lower = entity.lower()
        text_lower = text.lower()
        
        start = 0
        while True:
            pos = text_lower.find(entity_lower, start)
            if pos == -1:
                break
            
            # Extract context window
            context_start = max(0, pos - window)
            context_end = min(len(text), pos + len(entity) + window)
            context = text[context_start:context_end]
            
            contexts.append(context.strip())
            start = pos + 1
        
        return contexts
