"""
Expert Validation Interface
Tool for surgical experts to validate QA pairs and measure inter-annotator agreement
"""

import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import statistics


class ExpertValidator:
    """Manage expert validation of QA pairs"""
    
    def __init__(self, validation_dir: str = "evaluation/test_data/validation"):
        """
        Initialize expert validator
        
        Args:
            validation_dir: Directory to store validation results
        """
        self.validation_dir = Path(validation_dir)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
    
    def create_validation_task(
        self,
        qa_pairs: List[Dict],
        task_id: str,
        expert_id: str,
        instructions: Optional[str] = None
    ) -> str:
        """
        Create validation task for an expert
        
        Args:
            qa_pairs: QA pairs to validate
            task_id: Unique task identifier
            expert_id: Expert identifier
            instructions: Optional custom instructions
            
        Returns:
            Path to validation file
        """
        default_instructions = """
VALIDATION INSTRUCTIONS:

For each question-answer pair, please evaluate:

1. CORRECTNESS (0-5):
   - 5: Completely accurate, no errors
   - 4: Mostly accurate, minor issues
   - 3: Partially accurate, some errors
   - 2: Mostly inaccurate
   - 1: Completely inaccurate
   - 0: Cannot assess

2. RELEVANCE (0-5):
   - 5: Highly relevant to surgical education
   - 4: Relevant
   - 3: Somewhat relevant
   - 2: Marginally relevant
   - 1: Not relevant
   - 0: Cannot assess

3. DIFFICULTY (1-3):
   - 1: Novice (medical student)
   - 2: Intermediate (surgical resident)
   - 3: Advanced (attending surgeon)

4. CLARITY (0-5):
   - 5: Very clear and well-formulated
   - 4: Clear
   - 3: Adequate
   - 2: Somewhat unclear
   - 1: Very unclear
   - 0: Cannot assess

5. SUGGESTED CORRECTIONS:
   - If correctness < 4, please provide corrected answer
   - If clarity < 3, please suggest improved question

6. ACCEPT/REJECT:
   - Accept: Include in final dataset (correctness >= 4, relevance >= 3)
   - Reject: Exclude from dataset
"""

        task = {
            'task_id': task_id,
            'expert_id': expert_id,
            'created_at': datetime.now().isoformat(),
            'instructions': instructions or default_instructions,
            'total_items': len(qa_pairs),
            'qa_pairs': [
                {
                    'item_id': i,
                    'question': qa['question'],
                    'answer': qa['answer'],
                    'chunk_id': qa.get('chunk_id'),
                    'supporting_sentences': qa.get('supporting_sentences', []),
                    'validation': {
                        'correctness': None,
                        'relevance': None,
                        'difficulty': None,
                        'clarity': None,
                        'corrected_answer': '',
                        'improved_question': '',
                        'comments': '',
                        'accept': None
                    }
                }
                for i, qa in enumerate(qa_pairs)
            ]
        }
        
        output_path = self.validation_dir / f"task_{task_id}_{expert_id}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=2, ensure_ascii=False)
        
        print(f"Validation task created: {output_path}")
        print(f"Expert: {expert_id}")
        print(f"Items to validate: {len(qa_pairs)}")
        
        return str(output_path)
    
    def load_validation_results(self, filepath: str) -> Dict:
        """Load completed validation results"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def calculate_inter_annotator_agreement(
        self,
        validation_results: List[Dict],
        metric: str = 'correctness'
    ) -> Dict:
        """
        Calculate inter-annotator agreement metrics
        
        Args:
            validation_results: List of validation result dicts from multiple experts
            metric: Which validation metric to compare ('correctness', 'relevance', etc.)
            
        Returns:
            Agreement statistics
        """
        # Extract ratings per item
        item_ratings = {}
        
        for result in validation_results:
            expert_id = result['expert_id']
            for qa in result['qa_pairs']:
                item_id = qa['item_id']
                rating = qa['validation'].get(metric)
                
                if rating is not None:
                    if item_id not in item_ratings:
                        item_ratings[item_id] = {}
                    item_ratings[item_id][expert_id] = rating
        
        # Calculate agreement metrics
        agreements = []
        exact_matches = 0
        total_comparisons = 0
        
        for item_id, ratings in item_ratings.items():
            if len(ratings) < 2:
                continue
            
            rating_values = list(ratings.values())
            
            # Pairwise agreement
            for i in range(len(rating_values)):
                for j in range(i + 1, len(rating_values)):
                    total_comparisons += 1
                    diff = abs(rating_values[i] - rating_values[j])
                    
                    if diff == 0:
                        exact_matches += 1
                        agreements.append(1.0)
                    elif diff <= 1:
                        agreements.append(0.5)  # Close agreement
                    else:
                        agreements.append(0.0)
        
        if total_comparisons == 0:
            return {
                'error': 'Insufficient data for agreement calculation'
            }
        
        # Calculate Cohen's Kappa (simplified for multiple raters)
        observed_agreement = sum(agreements) / len(agreements)
        
        # Calculate Fleiss' Kappa for multiple raters
        kappa = self._calculate_fleiss_kappa(item_ratings)
        
        return {
            'metric': metric,
            'num_items': len(item_ratings),
            'num_comparisons': total_comparisons,
            'exact_match_rate': exact_matches / total_comparisons,
            'agreement_score': observed_agreement,
            'fleiss_kappa': kappa,
            'interpretation': self._interpret_kappa(kappa)
        }
    
    def _calculate_fleiss_kappa(self, item_ratings: Dict[int, Dict[str, int]]) -> float:
        """Calculate Fleiss' Kappa for multiple raters"""
        items = []
        for ratings in item_ratings.values():
            items.append(list(ratings.values()))
        
        if not items:
            return 0.0
        
        n = len(items)  # Number of items
        k = len(items[0])  # Number of raters
        
        # Count ratings per category
        all_ratings = []
        for item in items:
            all_ratings.extend(item)
        
        categories = set(all_ratings)
        
        # Calculate P_i (proportion of agreement for each item)
        P_i_values = []
        for item in items:
            rating_counts = {cat: item.count(cat) for cat in categories}
            sum_squared = sum(count ** 2 for count in rating_counts.values())
            P_i = (sum_squared - k) / (k * (k - 1))
            P_i_values.append(P_i)
        
        P_bar = sum(P_i_values) / n  # Mean agreement
        
        # Calculate P_e (expected agreement by chance)
        p_j_values = []
        for cat in categories:
            count = sum(1 for item in items for rating in item if rating == cat)
            p_j = count / (n * k)
            p_j_values.append(p_j ** 2)
        
        P_e = sum(p_j_values)
        
        # Fleiss' Kappa
        if P_e == 1.0:
            return 1.0
        
        kappa = (P_bar - P_e) / (1 - P_e)
        return kappa
    
    def _interpret_kappa(self, kappa: float) -> str:
        """Interpret Kappa value"""
        if kappa < 0:
            return "Poor (less than chance)"
        elif kappa < 0.20:
            return "Slight agreement"
        elif kappa < 0.40:
            return "Fair agreement"
        elif kappa < 0.60:
            return "Moderate agreement"
        elif kappa < 0.80:
            return "Substantial agreement"
        else:
            return "Almost perfect agreement"
    
    def generate_validation_report(
        self,
        validation_results: List[Dict],
        output_file: Optional[str] = None
    ) -> Dict:
        """
        Generate comprehensive validation report
        
        Args:
            validation_results: List of validation results from experts
            output_file: Optional file to save report
            
        Returns:
            Report dictionary
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'num_experts': len(validation_results),
            'total_items_validated': 0,
            'agreement_metrics': {},
            'quality_statistics': {},
            'accepted_items': [],
            'rejected_items': []
        }
        
        # Calculate agreement for each metric
        for metric in ['correctness', 'relevance', 'difficulty', 'clarity']:
            agreement = self.calculate_inter_annotator_agreement(
                validation_results,
                metric
            )
            report['agreement_metrics'][metric] = agreement
        
        # Aggregate quality scores
        all_ratings = {
            'correctness': [],
            'relevance': [],
            'difficulty': [],
            'clarity': []
        }
        
        acceptance_votes = {}
        
        for result in validation_results:
            for qa in result['qa_pairs']:
                item_id = qa['item_id']
                validation = qa['validation']
                
                for metric in all_ratings.keys():
                    if validation.get(metric) is not None:
                        all_ratings[metric].append(validation[metric])
                
                # Track acceptance votes
                if item_id not in acceptance_votes:
                    acceptance_votes[item_id] = {'accept': 0, 'reject': 0, 'question': qa['question']}
                
                if validation.get('accept') is True:
                    acceptance_votes[item_id]['accept'] += 1
                elif validation.get('accept') is False:
                    acceptance_votes[item_id]['reject'] += 1
        
        # Calculate statistics
        for metric, values in all_ratings.items():
            if values:
                report['quality_statistics'][metric] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                    'min': min(values),
                    'max': max(values)
                }
        
        # Determine accepted/rejected items (majority vote)
        for item_id, votes in acceptance_votes.items():
            total_votes = votes['accept'] + votes['reject']
            if total_votes == 0:
                continue
            
            acceptance_rate = votes['accept'] / total_votes
            
            if acceptance_rate >= 0.5:
                report['accepted_items'].append(item_id)
            else:
                report['rejected_items'].append(item_id)
        
        report['total_items_validated'] = len(acceptance_votes)
        report['acceptance_rate'] = len(report['accepted_items']) / len(acceptance_votes) if acceptance_votes else 0
        
        # Save report
        if output_file:
            output_path = self.validation_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"Validation report saved: {output_path}")
        
        return report


if __name__ == "__main__":
    # Example usage
    validator = ExpertValidator()
    
    # Create validation tasks for 2 experts
    example_qa = [
        {
            'question': 'What are complications of central line insertion?',
            'answer': 'Complications include pneumothorax, arterial puncture, and infection.',
            'chunk_id': 'doc_1'
        }
    ]
    
    # Expert 1 task
    validator.create_validation_task(
        qa_pairs=example_qa,
        task_id='surgical_qa_001',
        expert_id='surgeon_a'
    )
    
    # Expert 2 task
    validator.create_validation_task(
        qa_pairs=example_qa,
        task_id='surgical_qa_001',
        expert_id='surgeon_b'
    )
    
    print("\nValidation tasks created. Experts can now fill in the JSON files.")
