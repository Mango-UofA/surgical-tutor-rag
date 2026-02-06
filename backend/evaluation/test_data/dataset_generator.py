"""
Test Dataset Preparation
Generate QA pairs from documents with train/test split
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import random
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import aiohttp
import asyncio
from pathlib import Path


class QADatasetGenerator:
    """Generate QA pairs from surgical documents"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o",
        output_dir: str = "evaluation/test_data"
    ):
        """
        Initialize QA dataset generator
        
        Args:
            api_key: OpenRouter API key
            model: LLM model for QA generation
            output_dir: Directory to save generated datasets
        """
        self.api_key = api_key
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_qa_from_chunk(
        self,
        chunk_text: str,
        chunk_id: str,
        num_questions: int = 3,
        difficulty: str = "mixed"
    ) -> List[Dict]:
        """
        Generate QA pairs from a text chunk using LLM
        
        Args:
            chunk_text: Document chunk text
            chunk_id: Unique chunk identifier
            num_questions: Number of questions to generate
            difficulty: Question difficulty ('easy', 'medium', 'hard', 'mixed')
            
        Returns:
            List of QA pairs
        """
        difficulty_prompt = {
            'easy': 'Generate factual recall questions (e.g., "What is...", "List the...").',
            'medium': 'Generate comprehension questions requiring understanding (e.g., "Why does...", "How does...").',
            'hard': 'Generate analytical questions requiring reasoning (e.g., "Compare...", "What would happen if...").',
            'mixed': 'Generate a mix of easy, medium, and hard questions.'
        }
        
        prompt = f"""You are generating question-answer pairs for a surgical education system.

CONTEXT:
{chunk_text}

TASK:
Generate {num_questions} high-quality medical questions that can be answered using ONLY the information in the context above.

REQUIREMENTS:
1. {difficulty_prompt[difficulty]}
2. Questions should be specific and answerable from the context
3. Answers should be concise but complete (1-3 sentences)
4. Include the relevant document chunk reference
5. Mark which specific sentences support the answer

FORMAT YOUR RESPONSE AS JSON:
{{
  "questions": [
    {{
      "question": "What are the main complications of...?",
      "answer": "The main complications include...",
      "difficulty": "medium",
      "supporting_sentences": ["sentence from context that supports this answer"],
      "answer_type": "factual|procedural|analytical"
    }}
  ]
}}

RESPOND WITH ONLY THE JSON, NO ADDITIONAL TEXT."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                }
            ) as resp:
                result = await resp.json()
                
                # Check for API errors
                if 'error' in result:
                    print(f"API Error: {result['error']}")
                    return []
                
                # Check for expected response structure
                if 'choices' not in result:
                    print(f"Unexpected API response format: {result}")
                    return []
                
                response_text = result['choices'][0]['message']['content']
                
                try:
                    qa_data = json.loads(response_text)
                    
                    # Add metadata
                    for qa in qa_data['questions']:
                        qa['chunk_id'] = chunk_id
                        qa['chunk_text'] = chunk_text
                        qa['generated_at'] = datetime.now().isoformat()
                    
                    return qa_data['questions']
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON from LLM response: {response_text}")
                    return []
                except KeyError as e:
                    print(f"Missing expected key in response: {e}")
                    print(f"Response data: {qa_data}")
                    return []
    
    async def generate_dataset_from_documents(
        self,
        documents: List[Dict],
        questions_per_chunk: int = 3,
        max_chunks: Optional[int] = None
    ) -> List[Dict]:
        """
        Generate complete QA dataset from document collection
        
        Args:
            documents: List of dicts with 'id', 'text' keys
            questions_per_chunk: Questions to generate per chunk
            max_chunks: Maximum chunks to process (for testing)
            
        Returns:
            List of QA pairs with metadata
        """
        all_qa_pairs = []
        
        chunks_to_process = documents[:max_chunks] if max_chunks else documents
        
        for i, doc in enumerate(chunks_to_process):
            print(f"Processing chunk {i+1}/{len(chunks_to_process)}: {doc['id']}")
            
            qa_pairs = await self.generate_qa_from_chunk(
                chunk_text=doc['text'],
                chunk_id=doc['id'],
                num_questions=questions_per_chunk
            )
            
            all_qa_pairs.extend(qa_pairs)
            
            # Add small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        return all_qa_pairs
    
    def create_train_test_split(
        self,
        qa_pairs: List[Dict],
        test_ratio: float = 0.2,
        stratify_by: Optional[str] = None,
        random_seed: int = 42
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Split QA pairs into train and test sets
        
        Args:
            qa_pairs: List of QA pairs
            test_ratio: Fraction for test set (0-1)
            stratify_by: Field to stratify split (e.g., 'difficulty')
            random_seed: Random seed for reproducibility
            
        Returns:
            Tuple of (train_set, test_set)
        """
        random.seed(random_seed)
        
        if stratify_by:
            # Stratified split
            groups = {}
            for qa in qa_pairs:
                key = qa.get(stratify_by, 'unknown')
                if key not in groups:
                    groups[key] = []
                groups[key].append(qa)
            
            train_set, test_set = [], []
            for group_qa in groups.values():
                random.shuffle(group_qa)
                split_idx = int(len(group_qa) * (1 - test_ratio))
                train_set.extend(group_qa[:split_idx])
                test_set.extend(group_qa[split_idx:])
        else:
            # Random split
            shuffled = qa_pairs.copy()
            random.shuffle(shuffled)
            split_idx = int(len(shuffled) * (1 - test_ratio))
            train_set = shuffled[:split_idx]
            test_set = shuffled[split_idx:]
        
        return train_set, test_set
    
    def save_dataset(
        self,
        dataset: List[Dict],
        filename: str,
        include_metadata: bool = True
    ):
        """
        Save dataset to JSON file
        
        Args:
            dataset: QA pairs to save
            filename: Output filename
            include_metadata: Whether to include generation metadata
        """
        output_path = self.output_dir / filename
        
        data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'num_examples': len(dataset),
            'qa_pairs': dataset
        }
        
        if include_metadata and len(dataset) > 0:
            # Add statistics (handle both QA format and retrieval format)
            difficulties = {}
            answer_types = {}
            
            # Check if this is a retrieval test set or QA pairs
            is_retrieval_set = 'query' in dataset[0]
            
            if not is_retrieval_set:
                for qa in dataset:
                    diff = qa.get('difficulty', 'unknown')
                    atype = qa.get('answer_type', 'unknown')
                    difficulties[diff] = difficulties.get(diff, 0) + 1
                    answer_types[atype] = answer_types.get(atype, 0) + 1
                
                data['statistics'] = {
                    'difficulty_distribution': difficulties,
                    'answer_type_distribution': answer_types,
                    'avg_question_length': sum(len(qa['question']) for qa in dataset) / len(dataset),
                    'avg_answer_length': sum(len(qa['answer']) for qa in dataset) / len(dataset)
                }
            else:
                # Retrieval test set statistics
                data['statistics'] = {
                    'avg_query_length': sum(len(qa['query']) for qa in dataset) / len(dataset),
                    'avg_relevant_docs': sum(len(qa['relevant_doc_ids']) for qa in dataset) / len(dataset),
                    'avg_distractor_docs': sum(len(qa.get('distractor_doc_ids', [])) for qa in dataset) / len(dataset)
                }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Dataset saved to {output_path}")
        print(f"Total examples: {len(dataset)}")
    
    def load_dataset(self, filename: str) -> List[Dict]:
        """Load dataset from JSON file"""
        input_path = self.output_dir / filename
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data['qa_pairs']
    
    def create_retrieval_test_set(
        self,
        qa_pairs: List[Dict],
        all_chunk_ids: List[str],
        num_distractors: int = 10
    ) -> List[Dict]:
        """
        Create retrieval test set with relevant and distractor documents
        
        Args:
            qa_pairs: QA pairs with chunk_id
            all_chunk_ids: All available chunk IDs
            num_distractors: Number of distractor chunks per query
            
        Returns:
            List of retrieval test examples
        """
        retrieval_test = []
        
        for qa in qa_pairs:
            relevant_id = qa['chunk_id']
            
            # Sample distractor chunks
            distractors = [cid for cid in all_chunk_ids if cid != relevant_id]
            sampled_distractors = random.sample(
                distractors,
                min(num_distractors, len(distractors))
            )
            
            retrieval_test.append({
                'query': qa['question'],
                'relevant_doc_ids': [relevant_id],
                'distractor_doc_ids': sampled_distractors,
                'ground_truth_answer': qa['answer']
            })
        
        return retrieval_test


async def main():
    """Example usage"""
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY environment variable not set!")
        print("Please set it with: export OPENROUTER_API_KEY='your-key-here'")
        print("Or on Windows: set OPENROUTER_API_KEY=your-key-here")
        return
    
    # Example documents
    documents = [
        {
            'id': 'wses_guideline_p5',
            'text': 'Central venous catheter insertion carries risks including pneumothorax (1-3%), arterial puncture (0.5-1%), and catheter-related bloodstream infection. Ultrasound guidance reduces complications by 50%.'
        },
        {
            'id': 'appendectomy_proc_p12',
            'text': 'Laparoscopic appendectomy is performed through 3 ports. The mesoappendix is divided using energy device, and the appendix base is secured with endoloop or stapler. Typical operating time is 30-45 minutes.'
        }
    ]
    
    # Initialize generator
    generator = QADatasetGenerator(
        api_key=api_key,
        output_dir="test_data"
    )
    
    # Generate QA pairs
    qa_pairs = await generator.generate_dataset_from_documents(
        documents,
        questions_per_chunk=3
    )
    
    # Create train/test split
    train_set, test_set = generator.create_train_test_split(
        qa_pairs,
        test_ratio=0.2,
        stratify_by='difficulty'
    )
    
    # Save datasets
    generator.save_dataset(train_set, 'train_qa_pairs.json')
    generator.save_dataset(test_set, 'test_qa_pairs.json')
    
    # Create retrieval test set
    all_chunk_ids = [doc['id'] for doc in documents]
    retrieval_test = generator.create_retrieval_test_set(
        test_set,
        all_chunk_ids,
        num_distractors=10
    )
    generator.save_dataset(retrieval_test, 'retrieval_test_set.json')
    
    print(f"\nGenerated {len(qa_pairs)} QA pairs")
    print(f"Train set: {len(train_set)}")
    print(f"Test set: {len(test_set)}")


if __name__ == "__main__":
    asyncio.run(main())
