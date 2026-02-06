"""
Setup Validation Script
Checks if the evaluation environment is properly configured
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def check_environment():
    """Validate the evaluation setup"""
    print("="*70)
    print("EVALUATION SETUP VALIDATION")
    print("="*70)
    
    issues = []
    warnings = []
    success = []
    
    # 1. Check Python version
    print("\n📋 Checking Python version...")
    if sys.version_info >= (3, 8):
        success.append(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} (OK)")
    else:
        issues.append(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} (Need 3.8+)")
    
    # 2. Check required packages
    print("📦 Checking required packages...")
    required = {
        'numpy': 'Core numerical operations',
        'pandas': 'Data handling',
        'transformers': 'BioClinicalBERT',
        'faiss': 'Vector search',
    }
    
    optional = {
        'sentence_transformers': 'Semantic similarity',
        'matplotlib': 'Visualization',
        'seaborn': 'Statistical plots',
    }
    
    for package, purpose in required.items():
        try:
            if package == 'faiss':
                __import__('faiss')
            else:
                __import__(package)
            success.append(f"✅ {package} - {purpose}")
        except ImportError:
            issues.append(f"❌ {package} - {purpose} (install: pip install {package if package != 'faiss' else 'faiss-cpu'})")
    
    for package, purpose in optional.items():
        try:
            __import__(package.replace('-', '_'))
            success.append(f"✅ {package} - {purpose}")
        except ImportError:
            warnings.append(f"⚠️  {package} - {purpose} (optional)")
    
    # 3. Check file structure
    print("📁 Checking file structure...")
    required_files = [
        ('config.json', 'Configuration file'),
        ('generate_quick_metrics.py', 'Quick metrics generator'),
        ('run_production_eval.py', 'Production evaluation'),
        ('FINAL_METRICS_SUMMARY.md', 'Main documentation'),
        ('metrics/retrieval_metrics.py', 'Retrieval metrics module'),
        ('metrics/qa_metrics.py', 'QA metrics module'),
    ]
    
    for filename, description in required_files:
        if Path(filename).exists():
            success.append(f"✅ {filename} - {description}")
        else:
            issues.append(f"❌ {filename} - {description} (missing)")
    
    # 4. Check FAISS index
    print("🔍 Checking FAISS index...")
    faiss_path = Path('../faiss_index.index')
    faiss_meta = Path('../faiss_index.index.meta.npy')
    
    if faiss_path.exists() and faiss_meta.exists():
        success.append(f"✅ FAISS index found at {faiss_path}")
    else:
        warnings.append(f"⚠️  FAISS index not found at {faiss_path} (some evaluations will fail)")
    
    # 5. Check API key
    print("🔑 Checking API credentials...")
    import os
    if os.getenv('OPENROUTER_API_KEY'):
        success.append("✅ OPENROUTER_API_KEY found (answer generation enabled)")
    else:
        warnings.append("⚠️  OPENROUTER_API_KEY not set (answer generation will be skipped)")
    
    # 6. Check results directory
    print("📊 Checking results directory...")
    results_dir = Path('results')
    if results_dir.exists():
        result_files = list(results_dir.glob('*.json'))
        if result_files:
            latest = max(result_files, key=lambda p: p.stat().st_mtime)
            success.append(f"✅ Results directory exists ({len(result_files)} results, latest: {latest.name})")
        else:
            success.append("✅ Results directory exists (empty)")
    else:
        warnings.append("⚠️  Results directory missing (will be created)")
    
    # Print results
    print("\n" + "="*70)
    print("VALIDATION RESULTS")
    print("="*70)
    
    if success:
        print(f"\n✅ SUCCESS ({len(success)} items)")
        for item in success:
            print(f"  {item}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)} items)")
        for item in warnings:
            print(f"  {item}")
    
    if issues:
        print(f"\n❌ ISSUES ({len(issues)} items)")
        for item in issues:
            print(f"  {item}")
    
    # Summary
    print("\n" + "="*70)
    if not issues:
        if not warnings:
            print("🎉 PERFECT! Your evaluation environment is fully set up.")
            print("\n📝 Next steps:")
            print("  1. Run: python generate_quick_metrics.py")
            print("  2. Check: results/quick_metrics_*.json")
            print("  3. Read: FINAL_METRICS_SUMMARY.md")
        else:
            print("✅ GOOD! Your evaluation environment is ready.")
            print("   Some optional features are unavailable (see warnings above)")
            print("\n📝 Next steps:")
            print("  1. Run: python generate_quick_metrics.py")
            print("  2. Optionally install missing packages for full features")
    else:
        print("❌ SETUP INCOMPLETE - Please fix the issues above")
        print("\n📝 Quick fixes:")
        print("  • Install missing packages: pip install -r requirements.txt")
        print("  • Check file paths and directory structure")
        print("  • Read: FINAL_METRICS_SUMMARY.md for detailed setup")
    
    print("="*70 + "\n")
    
    return len(issues) == 0


if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
