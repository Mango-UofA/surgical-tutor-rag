"""
Publication-Ready Report Generator
Creates comprehensive evaluation reports with statistical analysis and visualizations
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class ReportGenerator:
    """Generate publication-ready evaluation reports"""
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def load_latest_results(self) -> Dict:
        """Load the most recent evaluation results"""
        json_files = list(self.results_dir.glob("evaluation_results_*.json"))
        
        if not json_files:
            print("No evaluation results found!")
            return {}
        
        # Get most recent file
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            results = json.load(f)
        
        print(f"Loaded results from: {latest_file}")
        return results
    
    def calculate_confidence_intervals(self, scores: List[float], confidence: float = 0.95) -> tuple:
        """
        Calculate confidence intervals using bootstrap
        
        Args:
            scores: List of scores
            confidence: Confidence level (default 0.95 for 95% CI)
            
        Returns:
            (mean, lower_bound, upper_bound)
        """
        if not scores:
            return 0.0, 0.0, 0.0
        
        scores = np.array(scores)
        mean = np.mean(scores)
        
        # Bootstrap for confidence interval
        n_bootstrap = 1000
        bootstrap_means = []
        
        for _ in range(n_bootstrap):
            sample = np.random.choice(scores, size=len(scores), replace=True)
            bootstrap_means.append(np.mean(sample))
        
        alpha = 1 - confidence
        lower = np.percentile(bootstrap_means, alpha/2 * 100)
        upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
        
        return mean, lower, upper
    
    def generate_latex_table(self, results: Dict) -> str:
        """Generate LaTeX table for publication"""
        latex = "\\begin{table}[h]\n"
        latex += "\\centering\n"
        latex += "\\caption{RAG System Evaluation Results}\n"
        latex += "\\label{tab:evaluation}\n"
        latex += "\\begin{tabular}{lc}\n"
        latex += "\\hline\n"
        latex += "Metric & Score \\\\\n"
        latex += "\\hline\n"
        
        # Retrieval metrics
        if 'retrieval_metrics' in results:
            latex += "\\multicolumn{2}{c}{\\textbf{Retrieval Performance}} \\\\\n"
            for metric, value in results['retrieval_metrics'].items():
                if isinstance(value, (int, float)):
                    formatted_metric = metric.replace('_', ' ').title().replace('@', '@')
                    latex += f"{formatted_metric} & {value:.4f} \\\\\n"
        
        # QA metrics
        if 'qa_metrics' in results:
            latex += "\\hline\n"
            latex += "\\multicolumn{2}{c}{\\textbf{Answer Quality}} \\\\\n"
            for metric, value in results['qa_metrics'].items():
                if isinstance(value, (int, float)):
                    formatted_metric = metric.replace('_', ' ').title()
                    latex += f"{formatted_metric} & {value:.4f} \\\\\n"
        
        latex += "\\hline\n"
        latex += "\\end{tabular}\n"
        latex += "\\end{table}\n"
        
        return latex
    
    def generate_markdown_report(self, results: Dict) -> str:
        """Generate comprehensive markdown report"""
        md = "# RAG System Evaluation Report\n\n"
        md += f"**Experiment ID:** {results.get('experiment_id', 'N/A')}  \n"
        md += f"**Generated:** {results.get('timestamp', 'N/A')}  \n\n"
        
        # Dataset statistics
        if 'dataset_stats' in results:
            md += "## Dataset Statistics\n\n"
            md += "| Metric | Value |\n"
            md += "|--------|-------|\n"
            for key, value in results['dataset_stats'].items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    md += f"| {formatted_key} | {value:.2f} |\n"
                else:
                    md += f"| {formatted_key} | {value} |\n"
            md += "\n"
        
        # Retrieval performance
        if 'retrieval_metrics' in results:
            md += "## Retrieval Performance\n\n"
            md += "| Metric | Score |\n"
            md += "|--------|-------|\n"
            for metric, value in results['retrieval_metrics'].items():
                if isinstance(value, (int, float)):
                    formatted_metric = metric.replace('_', ' ').title()
                    md += f"| {formatted_metric} | {value:.4f} |\n"
            md += "\n"
            
            # Add interpretation
            recall_5 = results['retrieval_metrics'].get('recall@5', 0)
            if recall_5 > 0.7:
                md += "✅ **Excellent retrieval performance** - System retrieves relevant documents in top-5 results.\n\n"
            elif recall_5 > 0.5:
                md += "✓ **Good retrieval performance** - System often retrieves relevant documents.\n\n"
            elif recall_5 > 0.3:
                md += "⚠️ **Moderate retrieval performance** - System sometimes retrieves relevant documents.\n\n"
            else:
                md += "❌ **Low retrieval performance** - System struggles to retrieve relevant documents.\n\n"
        
        # QA performance
        if 'qa_metrics' in results:
            md += "## Answer Quality\n\n"
            md += "| Metric | Score |\n"
            md += "|--------|-------|\n"
            for metric, value in results['qa_metrics'].items():
                if isinstance(value, (int, float)):
                    formatted_metric = metric.replace('_', ' ').title()
                    md += f"| {formatted_metric} | {value:.4f} |\n"
            md += "\n"
            
            # Add interpretation
            semantic_sim = results['qa_metrics'].get('semantic_similarity', 0)
            if semantic_sim > 0:
                if semantic_sim > 0.8:
                    md += "✅ **Excellent semantic similarity** - Generated answers closely match reference answers.\n\n"
                elif semantic_sim > 0.6:
                    md += "✓ **Good semantic similarity** - Generated answers convey similar information.\n\n"
                else:
                    md += "⚠️ **Moderate semantic similarity** - Generated answers may paraphrase significantly.\n\n"
        
        # Context relevance
        if 'context_relevance' in results:
            md += "## Context Relevance\n\n"
            md += "| Metric | Score |\n"
            md += "|--------|-------|\n"
            for metric, value in results['context_relevance'].items():
                if isinstance(value, (int, float)):
                    formatted_metric = metric.replace('_', ' ').title()
                    md += f"| {formatted_metric} | {value:.4f} |\n"
            md += "\n"
        
        # Key findings
        md += "## Key Findings\n\n"
        
        findings = []
        
        # Retrieval findings
        if 'retrieval_metrics' in results:
            avg_retrieved = results['retrieval_metrics'].get('avg_retrieved_docs', 0)
            findings.append(f"- System successfully retrieves an average of {avg_retrieved:.1f} documents per query")
            
            recall_1 = results['retrieval_metrics'].get('recall@1', 0)
            recall_5 = results['retrieval_metrics'].get('recall@5', 0)
            recall_10 = results['retrieval_metrics'].get('recall@10', 0)
            
            if recall_1 > 0:
                findings.append(f"- {recall_1*100:.1f}% of queries retrieve the relevant document in the top-1 position")
            if recall_5 > 0:
                findings.append(f"- {recall_5*100:.1f}% of queries retrieve the relevant document in the top-5 positions")
            if recall_10 > 0:
                findings.append(f"- {recall_10*100:.1f}% of queries retrieve the relevant document in the top-10 positions")
        
        # QA findings
        if 'qa_metrics' in results:
            semantic_sim = results['qa_metrics'].get('semantic_similarity', 0)
            if semantic_sim > 0:
                findings.append(f"- Generated answers achieve {semantic_sim*100:.1f}% semantic similarity to reference answers")
            
            equiv_70 = results['qa_metrics'].get('semantic_equivalence_70', 0)
            if equiv_70 > 0:
                findings.append(f"- {equiv_70*100:.1f}% of generated answers are semantically equivalent to references (70% threshold)")
        
        for finding in findings:
            md += finding + "\n"
        
        md += "\n"
        
        # Recommendations
        md += "## Recommendations for Publication\n\n"
        md += "1. **Report retrieval metrics** to demonstrate the system's ability to find relevant information\n"
        md += "2. **Include semantic similarity** scores as they better reflect answer quality than exact match\n"
        md += "3. **Provide example outputs** with qualitative analysis to showcase system capabilities\n"
        md += "4. **Discuss trade-offs** between precision and recall based on your use case\n"
        md += "5. **Compare with baselines** if available to demonstrate improvements\n\n"
        
        return md
    
    def save_publication_report(self, results: Dict):
        """Save comprehensive publication-ready report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save markdown report
        md_report = self.generate_markdown_report(results)
        md_file = self.results_dir / f'publication_report_{timestamp}.md'
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"✅ Markdown report saved: {md_file}")
        
        # Save LaTeX table
        latex_table = self.generate_latex_table(results)
        latex_file = self.results_dir / f'latex_table_{timestamp}.tex'
        with open(latex_file, 'w', encoding='utf-8') as f:
            f.write(latex_table)
        print(f"✅ LaTeX table saved: {latex_file}")
        
        # Save formatted text report
        text_report = md_report.replace('#', '=').replace('|', ' ')
        text_file = self.results_dir / f'formatted_report_{timestamp}.txt'
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)
        print(f"✅ Text report saved: {text_file}")


def main():
    """Generate publication report from latest results"""
    generator = ReportGenerator()
    results = generator.load_latest_results()
    
    if results:
        generator.save_publication_report(results)
        print("\n✅ Publication-ready reports generated successfully!")
    else:
        print("\n❌ No results found. Please run evaluation first.")


if __name__ == "__main__":
    main()
