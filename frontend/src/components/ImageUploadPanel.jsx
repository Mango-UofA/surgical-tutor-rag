import React, { useState } from 'react'

export default function ImageUploadPanel() {
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [procedure, setProcedure] = useState('')
  const [isDragging, setIsDragging] = useState(false)

  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      processFile(file)
    }
  }

  const processFile = (file) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file')
      return
    }
    setSelectedImage(file)
    const reader = new FileReader()
    reader.onloadend = () => {
      setImagePreview(reader.result)
    }
    reader.readAsDataURL(file)
    setResult(null)
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      processFile(files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedImage) return

    setUploading(true)
    const formData = new FormData()
    formData.append('file', selectedImage)
    if (procedure) formData.append('procedure', procedure)

    try {
      const res = await fetch('http://localhost:8000/upload_image', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      console.error('Upload failed:', error)
      setResult({ status: 'error', message: error.message })
    } finally {
      setUploading(false)
    }
  }

  const clearImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    setResult(null)
    setProcedure('')
  }

  return (
    <div className="bg-gradient-to-br from-white via-purple-50/30 to-pink-50/30 dark:from-slate-900/90 dark:via-fuchsia-950/30 dark:to-purple-950/30 backdrop-blur-xl border-2 border-purple-200/50 dark:border-fuchsia-500/20 rounded-3xl p-8 shadow-2xl hover:shadow-purple-500/30 dark:shadow-fuchsia-500/10 dark:hover:shadow-fuchsia-500/20 transition-all duration-500">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl blur-lg opacity-50"></div>
          <div className="relative p-4 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
        <div className="flex-1">
          <h2 className="text-4xl font-black bg-gradient-to-r from-purple-600 via-pink-600 to-purple-600 dark:from-purple-400 dark:via-pink-400 dark:to-purple-400 bg-clip-text text-transparent mb-1">
            Image Analysis
          </h2>
          <p className="text-gray-600 dark:text-gray-400 text-base font-medium">AI-powered surgical image understanding</p>
        </div>
      </div>

      {/* Upload Area */}
      {!imagePreview ? (
        <div
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative overflow-hidden rounded-3xl transition-all duration-300 min-h-[500px] flex items-center justify-center cursor-pointer group ${
            isDragging
              ? 'bg-gradient-to-br from-purple-500/20 via-pink-500/20 to-purple-500/20 dark:from-purple-500/30 dark:via-pink-500/30 dark:to-purple-500/30 scale-[1.02]'
              : 'bg-gradient-to-br from-white/50 via-purple-50/80 to-pink-50/50 dark:from-slate-800/50 dark:via-purple-900/30 dark:to-pink-900/30 hover:from-purple-50/90 hover:via-pink-50/90 hover:to-purple-50/90 dark:hover:from-purple-900/40 dark:hover:via-pink-900/40 dark:hover:to-purple-900/40'
          }`}
        >
          {/* Animated Border */}
          <div className={`absolute inset-0 rounded-3xl transition-all duration-300 ${
            isDragging 
              ? 'border-4 border-purple-500 dark:border-pink-500 animate-pulse' 
              : 'border-2 border-purple-200/50 dark:border-purple-500/30 group-hover:border-purple-300 dark:group-hover:border-purple-400/50'
          }`}></div>
          
          {/* Spotlight Effect */}
          <div className="absolute inset-0 bg-gradient-to-br from-purple-400/0 via-pink-400/5 to-purple-400/0 dark:from-purple-400/0 dark:via-pink-400/10 dark:to-purple-400/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

          <label className="relative w-full h-full flex items-center justify-center cursor-pointer">
            <div className="text-center space-y-6">
              {/* Icon */}
              <div className="relative mx-auto">
                <div className={`w-32 h-32 mx-auto bg-gradient-to-br from-purple-100 via-pink-100 to-purple-100 dark:from-purple-900/50 dark:via-pink-900/50 dark:to-purple-900/50 rounded-3xl flex items-center justify-center transition-all duration-500 ${
                  isDragging ? 'scale-110 rotate-6 shadow-2xl shadow-purple-500/50' : 'group-hover:scale-105 group-hover:-rotate-3'
                }`}>
                  <svg className="w-16 h-16 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                {/* Floating Elements */}
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-pink-400 dark:bg-pink-500 rounded-full opacity-60 group-hover:scale-125 transition-transform duration-300"></div>
                <div className="absolute -bottom-2 -left-2 w-6 h-6 bg-purple-400 dark:bg-purple-500 rounded-full opacity-60 group-hover:scale-125 transition-transform duration-300 animation-delay-200"></div>
              </div>

              {/* Text */}
              <div className="space-y-3">
                <h3 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-purple-600 dark:from-purple-400 dark:via-pink-400 dark:to-purple-400 bg-clip-text text-transparent">
                  {isDragging ? '✨ Drop it here!' : 'Upload Surgical Image'}
                </h3>
                <p className="text-lg text-gray-600 dark:text-gray-300 font-medium">
                  {isDragging ? 'Release to upload' : 'Click or drag & drop'}
                </p>
                <div className="flex items-center justify-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span>JPG, PNG • Max 10MB</span>
                </div>
              </div>
            </div>
            <input
              type="file"
              className="hidden"
              accept="image/*"
              onChange={handleImageSelect}
            />
          </label>
        </div>
      ) : (
        <div className="space-y-4 min-h-[500px] flex flex-col">
          {/* Image Preview */}
          <div className="relative group flex-1">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative border-2 border-purple-200 rounded-2xl overflow-hidden shadow-xl h-full">
              <img
                src={imagePreview}
                alt="Preview"
                className="w-full h-full object-contain bg-gray-900"
              />
            </div>
            <button
              onClick={clearImage}
              className="absolute top-4 right-4 p-2 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg hover:scale-110 transition-all duration-300"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Procedure Input */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Procedure (Optional)
            </label>
            <input
              type="text"
              value={procedure}
              onChange={(e) => setProcedure(e.target.value)}
              placeholder="e.g., Laparoscopic Appendectomy"
              className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-purple-500 focus:ring-4 focus:ring-purple-200 transition-all duration-300"
            />
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold rounded-xl shadow-lg hover:shadow-purple-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </span>
            ) : (
              'Analyze Image'
            )}
          </button>
        </div>
      )}

      {/* Results */}
      {result && result.status === 'success' && (
        <div className="mt-6 p-6 bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl shadow-xl animate-fade-in">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-green-500 rounded-lg">
              <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-green-900">Analysis Complete!</h3>
          </div>

          {/* Image Quality */}
          <div className="mb-4 p-4 bg-white rounded-xl">
            <p className="text-sm font-semibold text-gray-700 mb-2">Image Quality Score</p>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-green-500 to-emerald-500 rounded-full transition-all duration-1000"
                  style={{ width: `${Math.min(result.quality.quality_score, 100)}%` }}
                ></div>
              </div>
              <span className="font-bold text-green-700">{result.quality.quality_score.toFixed(1)}%</span>
            </div>
          </div>

          {/* Detected Phase */}
          {result.detected_phase && (
            <div className="mb-4 p-4 bg-white rounded-xl">
              <p className="text-sm font-semibold text-gray-700 mb-2">🎯 Surgical Phase</p>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-indigo-700">{result.detected_phase.phase}</span>
                <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-semibold">
                  {(result.detected_phase.confidence * 100).toFixed(1)}% confident
                </span>
              </div>
            </div>
          )}

          {/* Detected Instruments */}
          {result.detected_instruments && result.detected_instruments.length > 0 && (
            <div className="p-4 bg-white rounded-xl">
              <p className="text-sm font-semibold text-gray-700 mb-3">🔧 Detected Instruments</p>
              <div className="space-y-2">
                {result.detected_instruments.map((inst, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-gray-800 capitalize">{inst.category}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                          style={{ width: `${inst.probability * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-semibold text-gray-600 w-12 text-right">
                        {(inst.probability * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {result && result.status === 'error' && (
        <div className="mt-6 p-4 bg-red-50 border-2 border-red-200 rounded-2xl">
          <p className="text-red-700 font-semibold">Error: {result.message}</p>
        </div>
      )}
    </div>
  )
}
