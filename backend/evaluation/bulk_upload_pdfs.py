"""
Bulk upload PDFs from a directory to expand the knowledge base
Addresses professor feedback: Expand corpus from 417 chunks to 800-1000 chunks
"""
import requests
import os
from pathlib import Path
import time
import json


class BulkPDFUploader:
    """Upload multiple PDFs to the backend to expand the vector database"""
    
    def __init__(self, pdf_directory: str, backend_url: str = "http://localhost:8000"):
        self.pdf_directory = Path(pdf_directory)
        self.backend_url = backend_url
        self.upload_endpoint = f"{backend_url}/upload_pdf"
        
        print("=" * 80)
        print("BULK PDF UPLOAD TO EXPAND KNOWLEDGE BASE")
        print("=" * 80)
        print(f"Source directory: {self.pdf_directory}")
        print(f"Backend URL: {self.backend_url}")
        print("=" * 80)
    
    def check_backend_health(self) -> bool:
        """Check if backend server is running"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is running")
                return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Backend server not reachable: {e}")
            print(f"\nPlease ensure the backend server is running:")
            print(f"  cd backend")
            print(f"  python start_server.py")
            return False
        return False
    
    def get_current_stats(self) -> dict:
        """Get current FAISS index statistics"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            data = response.json()
            return {
                'total_vectors': data.get('faiss_index_size', 0),
                'graph_nodes': data.get('neo4j_node_count', 0),
                'graph_relationships': data.get('neo4j_relationship_count', 0)
            }
        except Exception as e:
            print(f"⚠️  Could not get current stats: {e}")
            return {'total_vectors': 0, 'graph_nodes': 0, 'graph_relationships': 0}
    
    def find_pdfs(self) -> list:
        """Find all PDF files in the directory"""
        if not self.pdf_directory.exists():
            print(f"❌ Directory not found: {self.pdf_directory}")
            return []
        
        pdfs = list(self.pdf_directory.glob("*.pdf"))
        print(f"\n📁 Found {len(pdfs)} PDF files:")
        for i, pdf in enumerate(pdfs, 1):
            size_mb = pdf.stat().st_size / (1024 * 1024)
            print(f"  {i}. {pdf.name} ({size_mb:.2f} MB)")
        
        return pdfs
    
    def upload_single_pdf(self, pdf_path: Path, index: int, total: int) -> dict:
        """Upload a single PDF file"""
        print(f"\n{'=' * 80}")
        print(f"Uploading [{index}/{total}]: {pdf_path.name}")
        print(f"File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
        print(f"{'=' * 80}")
        
        try:
            # Prepare the file for upload
            print(f"📂 Reading file from disk...")
            with open(pdf_path, 'rb') as f:
                file_content = f.read()
                print(f"✅ File loaded into memory ({len(file_content)} bytes)")
                
                files = {'file': (pdf_path.name, file_content, 'application/pdf')}
                data = {'title': pdf_path.stem}  # Use filename without extension as title
                
                print(f"📤 Sending HTTP POST request to {self.upload_endpoint}...")
                print(f"⏳ This may take 5-15 minutes depending on file size...")
                print(f"   Processing stages:")
                print(f"   1. Extract text from PDF (10-30 sec)")
                print(f"   2. Chunk text into segments (5 sec)")
                print(f"   3. Generate BioClinicalBERT embeddings (2-10 min) ⏰ SLOW")
                print(f"   4. Build Neo4j knowledge graph (1-2 min)")
                print(f"   5. Update FAISS index (10 sec)")
                print(f"\n🔄 Waiting for backend response...")
                
                start_time = time.time()
                last_log_time = start_time
                
                response = requests.post(
                    self.upload_endpoint,
                    files=files,
                    data=data,
                    timeout=900  # 15 minute timeout for large files (embedding generation can be slow)
                )
                
                elapsed = time.time() - start_time
                print(f"\n✅ Response received after {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"\n{'🎉' * 40}")
                    print(f"✅ Upload SUCCESSFUL for {pdf_path.name}")
                    print(f"{'🎉' * 40}")
                    print(f"📊 Processing Statistics:")
                    print(f"   ├─ Chunks created: {result.get('ingested_chunks', 0)}")
                    print(f"   ├─ Entities extracted: {result.get('entities_extracted', 0)}")
                    print(f"   ├─ Graph nodes created: {result.get('graph_nodes_created', 0)}")
                    print(f"   ├─ Graph relationships: {result.get('graph_relationships_created', 0)}")
                    print(f"   └─ Total vectors in index: {result.get('total_vectors_in_index', 0)}")
                    print(f"\n⏱️  Processing time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
                    print(f"{'=' * 80}\n")
                    
                    return {
                        'success': True,
                        'filename': pdf_path.name,
                        'chunks': result.get('ingested_chunks', 0),
                        'entities': result.get('entities_extracted', 0),
                        'nodes': result.get('graph_nodes_created', 0),
                        'relationships': result.get('graph_relationships_created', 0),
                        'total_vectors': result.get('total_vectors_in_index', 0),
                        'time': elapsed
                    }
                else:
                    print(f"\n{'❌' * 40}")
                    print(f"❌ Upload FAILED for {pdf_path.name}")
                    print(f"{'❌' * 40}")
                    print(f"HTTP Status Code: {response.status_code}")
                    print(f"Error Details:")
                    print(f"{response.text[:500]}")
                    print(f"{'=' * 80}\n")
                    return {
                        'success': False,
                        'filename': pdf_path.name,
                        'error': f"HTTP {response.status_code}: {response.text[:200]}"
                    }
        
        except Exception as e:
            print(f"\n{'❌' * 40}")
            print(f"❌ EXCEPTION during upload of {pdf_path.name}")
            print(f"{'❌' * 40}")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {str(e)[:500]}")
            print(f"{'=' * 80}\n")
            return {
                'success': False,
                'filename': pdf_path.name,
                'error': f"{type(e).__name__}: {str(e)[:200]}"
            }
    
    def upload_all(self) -> dict:
        """Upload all PDFs and return summary statistics"""
        # Check backend is running
        if not self.check_backend_health():
            return {'error': 'Backend server not running'}
        
        # Get initial stats
        initial_stats = self.get_current_stats()
        print(f"\n📊 Initial statistics:")
        print(f"   Vectors: {initial_stats['total_vectors']}")
        print(f"   Graph nodes: {initial_stats['graph_nodes']}")
        print(f"   Graph relationships: {initial_stats['graph_relationships']}")
        
        # Find PDFs
        pdfs = self.find_pdfs()
        if not pdfs:
            return {'error': 'No PDF files found'}
        
        # Upload each PDF
        results = []
        total_chunks = 0
        total_entities = 0
        total_nodes = 0
        total_relationships = 0
        successful_uploads = 0
        failed_uploads = 0
        
        print(f"\n{'🚀' * 40}")
        print(f"STARTING BULK UPLOAD OF {len(pdfs)} PDFs")
        print(f"{'🚀' * 40}")
        print(f"\n💡 TIP: Watch the backend terminal (uvicorn) for detailed processing logs")
        print(f"   You'll see: PDF extraction → Chunking → Embedding → Graph building")
        print(f"\n⏳ Expected time: {len(pdfs) * 5}-{len(pdfs) * 15} minutes total")
        print(f"   (~5-15 min per PDF depending on size)\n")
        
        for i, pdf_path in enumerate(pdfs, 1):
            print(f"\n{'►' * 40}")
            print(f"📋 Progress: {i}/{len(pdfs)} PDFs ({i/len(pdfs)*100:.1f}% complete)")
            print(f"✅ Successful so far: {successful_uploads}")
            print(f"❌ Failed so far: {failed_uploads}")
            print(f"📊 Total chunks ingested: {total_chunks}")
            print(f"{'►' * 40}")
            
            result = self.upload_single_pdf(pdf_path, i, len(pdfs))
            results.append(result)
            
            if result['success']:
                successful_uploads += 1
                total_chunks += result['chunks']
                total_entities += result['entities']
                total_nodes += result['nodes']
                total_relationships += result['relationships']
                print(f"✅ Running total: {total_chunks} chunks, {total_entities} entities")
            else:
                failed_uploads += 1
                print(f"❌ Upload failed, continuing with next file...")
            
            # Brief pause between uploads to avoid overwhelming the server
            if i < len(pdfs):
                print(f"\n⏸️  Pausing 2 seconds before next upload...")
                time.sleep(2)
        
        # Get final stats
        final_stats = self.get_current_stats()
        
        # Print summary
        print(f"\n{'🏁' * 40}")
        print(f"{'🏁' * 40}")
        print("BULK UPLOAD COMPLETE - FINAL SUMMARY")
        print(f"{'🏁' * 40}")
        print(f"{'🏁' * 40}")
        print(f"\n📈 Upload Results:")
        print(f"   ✅ Successful uploads: {successful_uploads}/{len(pdfs)}")
        print(f"   ❌ Failed uploads: {failed_uploads}/{len(pdfs)}")
        print(f"   Success rate: {successful_uploads/len(pdfs)*100:.1f}%")
        
        print(f"\n📊 Content Statistics:")
        print(f"   📄 Total chunks ingested: {total_chunks}")
        print(f"   🧬 Total entities extracted: {total_entities}")
        print(f"   🔗 Total graph nodes created: {total_nodes}")
        print(f"   🔗 Total graph relationships created: {total_relationships}")
        
        print(f"\n📈 Knowledge Base Growth:")
        vectors_gained = final_stats['total_vectors'] - initial_stats['total_vectors']
        nodes_gained = final_stats['graph_nodes'] - initial_stats['graph_nodes']
        rels_gained = final_stats['graph_relationships'] - initial_stats['graph_relationships']
        
        print(f"   Vectors: {initial_stats['total_vectors']} → {final_stats['total_vectors']} (Δ +{vectors_gained})")
        print(f"   Graph nodes: {initial_stats['graph_nodes']} → {final_stats['graph_nodes']} (Δ +{nodes_gained})")
        print(f"   Graph relationships: {initial_stats['graph_relationships']} → {final_stats['graph_relationships']} (Δ +{rels_gained})")
        
        print(f"\n🎯 Target Assessment:")
        print(f"   Current vectors: {final_stats['total_vectors']}")
        print(f"   Target: 800-1,000 chunks")
        if final_stats['total_vectors'] >= 800:
            print(f"   Status: ✅ TARGET ACHIEVED!")
        elif final_stats['total_vectors'] >= 600:
            print(f"   Status: ⚠️ PARTIAL ({final_stats['total_vectors']/800*100:.0f}% of minimum target)")
        else:
            print(f"   Status: ❌ BELOW TARGET ({final_stats['total_vectors']/800*100:.0f}% of minimum target)")
        
        print(f"\n📋 Failed Uploads:")
        if failed_uploads == 0:
            print(f"   ✅ None - all uploads successful!")
        else:
            for r in results:
                if not r['success']:
                    print(f"   ❌ {r['filename']}: {r.get('error', 'Unknown error')[:100]}")
        
        print(f"\n{'=' * 80}")
        print(f"{'=' * 80}")
        
        # Save summary to file
        summary = {
            'upload_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source_directory': str(self.pdf_directory),
            'total_pdfs': len(pdfs),
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads,
            'total_chunks_ingested': total_chunks,
            'total_entities_extracted': total_entities,
            'total_nodes_created': total_nodes,
            'total_relationships_created': total_relationships,
            'initial_stats': initial_stats,
            'final_stats': final_stats,
            'target_achieved': final_stats['total_vectors'] >= 800,
            'results': results
        }
        
        output_file = 'results/bulk_upload_summary.json'
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Summary saved to: {output_file}")
        
        return summary


def main():
    """Main execution"""
    # PDF directory from user's request
    pdf_directory = r"C:\Users\smang\Downloads\new training docs"
    
    uploader = BulkPDFUploader(pdf_directory)
    summary = uploader.upload_all()
    
    if 'error' in summary:
        print(f"\n❌ Upload process failed: {summary['error']}")
        return
    
    print(f"\n✅ Bulk upload complete!")
    print(f"\n📋 Next steps:")
    print(f"   1. Re-run evaluation on expanded test set")
    print(f"   2. Update paper with new corpus statistics")
    print(f"   3. Verify retrieval performance on larger knowledge base")


if __name__ == '__main__':
    main()
