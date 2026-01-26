import React, { useState } from 'react'

export default function VisualQAPanel() {
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [answer, setAnswer] = useState(null)
  const [isDragging, setIsDragging] = useState(false)

  const sampleQuestions = [
    "What instruments are visible in this image?",
    "What surgical phase is shown?",
    "What anatomical structures are visible?",
    "What type of procedure is this?",
    "What complications might occur in this step?"
  ]

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
    setAnswer(null)
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

  const askQuestion = async () => {
    if (!selectedImage || !question) return

    setAsking(true)
    const formData = new FormData()
    formData.append('file', selectedImage)
    formData.append('question', question)

    try {
      const res = await fetch('http://localhost:8000/visual_qa', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      setAnswer(data)
    } catch (error) {
      console.error('VQA failed:', error)
      setAnswer({ answer: 'Error: ' + error.message, confidence: 0 })
    } finally {
      setAsking(false)
    }
  }

  const clearAll = () => {
    setSelectedImage(null)
    setImagePreview(null)
    setQuestion('')
    setAnswer(null)
  }

  return (
    <div className="bg-gradient-to-br from-white via-indigo-50/30 to-blue-50/30 dark:from-slate-900/90 dark:via-indigo-950/30 dark:to-cyan-950/30 backdrop-blur-xl border-2 border-indigo-200/50 dark:border-indigo-500/20 rounded-3xl p-8 shadow-2xl hover:shadow-indigo-500/30 dark:shadow-indigo-500/10 dark:hover:shadow-indigo-500/20 transition-all duration-500">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-2xl blur-lg opacity-50"></div>
          <div className="relative p-4 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-2xl shadow-lg">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
        <div className="flex-1">
          <h2 className="text-4xl font-black bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-600 dark:from-indigo-400 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-1">
            Visual QA
          </h2>
          <p className="text-gray-600 dark:text-gray-400 text-base font-medium">Ask questions about surgical images</p>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Image Upload */}
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-3 flex items-center gap-2">
            <span className="flex items-center justify-center w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-blue-500 text-white text-sm font-bold">1</span>
            Upload Image
          </h3>
          {!imagePreview ? (
            <div
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`relative overflow-hidden rounded-2xl transition-all duration-300 min-h-[400px] flex items-center justify-center cursor-pointer group ${
                isDragging
                  ? 'bg-gradient-to-br from-indigo-500/20 via-blue-500/20 to-indigo-500/20 dark:from-indigo-500/30 dark:via-blue-500/30 dark:to-indigo-500/30 scale-[1.02]'
                  : 'bg-gradient-to-br from-white/50 via-indigo-50/80 to-blue-50/50 dark:from-slate-800/50 dark:via-indigo-900/30 dark:to-blue-900/30 hover:from-indigo-50/90 hover:via-blue-50/90 hover:to-indigo-50/90 dark:hover:from-indigo-900/40 dark:hover:via-blue-900/40 dark:hover:to-indigo-900/40'
              }`}
            >
              {/* Animated Border */}
              <div className={`absolute inset-0 rounded-2xl transition-all duration-300 ${
                isDragging 
                  ? 'border-4 border-indigo-500 dark:border-blue-400 animate-pulse' 
                  : 'border-2 border-indigo-200/50 dark:border-indigo-500/30 group-hover:border-indigo-300 dark:group-hover:border-indigo-400/50'
              }`}></div>
              
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-400/0 via-blue-400/5 to-indigo-400/0 dark:from-indigo-400/0 dark:via-blue-400/10 dark:to-indigo-400/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>

              <label className="relative w-full h-full flex items-center justify-center cursor-pointer">
                <div className="text-center space-y-4">
                  <div className="relative mx-auto">
                    <div className={`w-24 h-24 mx-auto bg-gradient-to-br from-indigo-100 via-blue-100 to-indigo-100 dark:from-indigo-900/50 dark:via-blue-900/50 dark:to-indigo-900/50 rounded-2xl flex items-center justify-center transition-all duration-500 ${
                      isDragging ? 'scale-110 rotate-6 shadow-xl shadow-indigo-500/50' : 'group-hover:scale-105'
                    }`}>
                      <svg className="w-12 h-12 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="absolute -top-1 -right-1 w-6 h-6 bg-blue-400 dark:bg-blue-500 rounded-full opacity-60 group-hover:scale-125 transition-transform duration-300"></div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-xl font-bold bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-600 dark:from-indigo-400 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
                      {isDragging ? '✨ Drop it!' : 'Upload Image'}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {isDragging ? 'Release to upload' : 'Click or drag & drop'}
                    </p>
                    <div className="flex items-center justify-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
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
            <div className="relative group min-h-[400px] flex items-center justify-center">
              <div className="border-2 border-indigo-200 rounded-2xl overflow-hidden shadow-lg w-full">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-full h-[400px] object-contain bg-gray-900"
                />
              </div>
              <button
                onClick={clearAll}
                className="absolute top-3 right-3 p-2 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-lg hover:scale-110 transition-all duration-300"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Right: Question */}
        <div className="space-y-4 flex flex-col min-h-[400px]">
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-3">2. Ask Question</h3>

          {/* Question Input */}
          <div className="flex-1 flex flex-col">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What would you like to know about this image?"
              rows={6}
              className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-200 transition-all duration-300 resize-none flex-1"
            />
          </div>

          {/* Sample Questions */}
          <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">💡 Sample Questions:</p>
            <div className="space-y-2">
              {sampleQuestions.slice(0, 3).map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuestion(q)}
                  className="block w-full text-left px-4 py-2.5 text-sm bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg transition-all duration-200 hover:scale-[1.02] hover:shadow-md"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Ask Button */}
          <button
            onClick={askQuestion}
            disabled={!selectedImage || !question || asking}
            className="w-full py-4 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold rounded-xl shadow-lg hover:shadow-indigo-500/50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {asking ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Analyzing...
              </span>
            ) : (
              'Get Answer'
            )}
          </button>
        </div>
      </div>

      {/* Answer Section */}
      {answer && (
        <div className="mt-6 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-2xl shadow-xl animate-fade-in">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 p-3 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xl font-bold text-blue-900">Answer</h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Confidence:</span>
                  <div className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
                    {(answer.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
              <div className="p-4 bg-white rounded-xl">
                <p className="text-gray-800 leading-relaxed whitespace-pre-line">{answer.answer}</p>
              </div>
              {answer.method && (
                <p className="text-xs text-gray-500 mt-3">Method: {answer.method}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
