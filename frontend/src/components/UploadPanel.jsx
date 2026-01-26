import React, {useState} from 'react'
import axios from 'axios'

export default function UploadPanel(){
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)

  const onUpload = async () =>{
    if(!file) {setStatus('⚠️ Please select a file first'); return}
    
    console.log('📤 Starting upload for:', file.name, 'Size:', file.size, 'bytes')
    setUploading(true)
    setProgress(0)
    const fd = new FormData()
    fd.append('file', file)
    fd.append('title', file.name)
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(prev => prev < 90 ? prev + 10 : prev)
    }, 200)
    
    try{
      console.log('📡 Sending POST request to http://localhost:8000/upload_pdf')
      const res = await axios.post('http://localhost:8000/upload_pdf', fd, {headers: {'Content-Type': 'multipart/form-data'}})
      clearInterval(progressInterval)
      setProgress(100)
      console.log('✅ Upload successful:', res.data)
      setStatus(`✅ Ingested ${res.data.ingested_chunks} chunks successfully! (${res.data.total_vectors_in_index} total vectors in index)`)
      setTimeout(() => {
        setFile(null)
        setProgress(0)
      }, 5000)  // Show success message longer
    }catch(e){
      clearInterval(progressInterval)
      setProgress(0)
      console.error('❌ Upload failed:', e)
      console.error('Error response:', e.response?.data)
      setStatus(`❌ Upload failed: ${e.response?.data?.detail || e.message}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="bg-white/95 dark:bg-slate-900/90 backdrop-blur-xl border border-white/50 dark:border-emerald-500/20 shadow-2xl dark:shadow-emerald-500/10 rounded-2xl p-6 hover:shadow-3xl dark:hover:shadow-emerald-500/20 transition-all duration-300 min-h-[500px] max-h-[800px] overflow-y-auto flex flex-col">
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl blur-md opacity-50"></div>
          <div className="relative w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center text-white shadow-lg transform hover:rotate-12 transition-transform duration-300">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-800 dark:text-gray-100">Upload Documents</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">Add surgical guidelines & training materials</p>
        </div>
      </div>

      <div className="space-y-4 flex-1 flex flex-col">
        {/* File Drop Zone */}
        <div className={`relative border-3 border-dashed rounded-xl p-8 transition-all duration-300 flex-1 flex items-center justify-center ${
          file ? 'border-emerald-400 bg-emerald-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
        }`}>
          <input 
            type="file" 
            accept="application/pdf" 
            onChange={e => {
              setFile(e.target.files[0])
              setStatus('')
              setProgress(0)
            }} 
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            disabled={uploading}
          />
          
          <div className="text-center pointer-events-none">
            {file ? (
              <>
                <svg className="w-16 h-16 mx-auto mb-3 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
                </svg>
                <p className="text-lg font-semibold text-gray-800">{file.name}</p>
                <p className="text-sm text-gray-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </>
            ) : (
              <>
                <svg className="w-16 h-16 mx-auto mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-lg font-semibold text-gray-700">Drop PDF here or click to browse</p>
                <p className="text-sm text-gray-500 mt-1">Surgical guidelines, protocols, case studies</p>
              </>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {uploading && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm text-gray-600">
              <span>Processing...</span>
              <span>{progress}%</span>
            </div>
            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-600 transition-all duration-300 rounded-full"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Upload Button */}
        <button 
          onClick={onUpload}
          disabled={!file || uploading}
          className={`w-full py-4 rounded-xl font-semibold text-white shadow-lg transition-all duration-300 transform ${
            !file || uploading
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 hover:scale-105 hover:shadow-xl'
          }`}
        >
          {uploading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing Document...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              Upload & Process PDF
            </span>
          )}
        </button>

        {/* Status Message */}
        {status && (
          <div className={`p-4 rounded-xl text-sm font-medium ${
            status.startsWith('✅') 
              ? 'bg-emerald-50 text-emerald-800 border-2 border-emerald-200' 
              : status.startsWith('⚠️')
              ? 'bg-amber-50 text-amber-800 border-2 border-amber-200'
              : 'bg-red-50 text-red-800 border-2 border-red-200'
          }`}>
            {status}
          </div>
        )}
      </div>
    </div>
  )
}
