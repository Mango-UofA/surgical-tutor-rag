import React, {useState} from 'react'
import axios from 'axios'

export default function ChatPanel({level}){
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const send = async ()=>{
    if(!query) return
    
    console.log('💬 Sending chat message...')
    console.log('Query:', query)
    console.log('Level:', level)
    
    const userMessage = query
    setMessages(prev=>[...prev, {from:'user', text: userMessage}])
    setQuery('')
    setLoading(true)
    
    const fd = new FormData()
    fd.append('query', userMessage)
    fd.append('level', level)
    
    try{
      console.log('📤 Sending request to backend...')
      const startTime = Date.now()
      const res = await axios.post('http://localhost:8000/chat', fd)
      const duration = ((Date.now() - startTime) / 1000).toFixed(2)
      console.log(`✅ Response received in ${duration}s:`, res.data)
      setMessages(prev=>[...prev, {from:'bot', text: res.data.answer, contexts: res.data.contexts}])
    }catch(e){
      console.error('❌ Chat failed:', e)
      setMessages(prev=>[...prev, {from:'bot', text: `Error: ${e.response?.data?.detail || e.message || 'could not reach backend'}`}])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white/90 backdrop-blur-xl border border-white/50 shadow-2xl rounded-2xl p-6 hover:shadow-3xl transition-all duration-300 flex flex-col min-h-[500px]">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl blur-md opacity-50"></div>
          <div className="relative w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center text-white shadow-lg">
            <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-800">AI Assistant</h3>
          <p className="text-sm text-gray-500">Ask questions about surgical procedures</p>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-auto mb-4 bg-gradient-to-b from-slate-50 to-blue-50 p-4 rounded-xl space-y-4 border-2 border-blue-100 flex flex-col">
        {messages.length === 0 && !loading && (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-lg font-medium">Start a conversation</p>
              <p className="text-sm mt-2">Ask me anything about surgical procedures and techniques</p>
            </div>
          </div>
        )}
        
        {messages.map((m,i)=> (
          <div key={i} className={`flex ${m.from==='user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            <div className={`max-w-[85%] ${
              m.from==='user' 
                ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-2xl rounded-tr-md shadow-lg' 
                : 'bg-white text-gray-800 rounded-2xl rounded-tl-md shadow-lg border-2 border-blue-100'
            } p-4`}>
              <div className="whitespace-pre-wrap">{m.text}</div>
              {m.contexts && m.contexts.length > 0 && (
                <details className="mt-3 text-sm">
                  <summary className="cursor-pointer font-semibold hover:text-blue-600 transition-colors flex items-center gap-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                    </svg>
                    View {m.contexts.length} reference{m.contexts.length > 1 ? 's' : ''}
                  </summary>
                  <div className="mt-3 space-y-2">
                    {m.contexts.map((c,idx)=> (
                      <div key={idx} className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                        <div className="flex items-start justify-between mb-1">
                          <span className="font-semibold text-blue-900">{c.metadata?.title || 'Source'}</span>
                          <span className="text-xs px-2 py-1 bg-blue-200 text-blue-800 rounded-full font-medium">
                            {(c.score * 100).toFixed(0)}% match
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 line-clamp-2">{c.metadata?.text}</p>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-white text-gray-800 rounded-2xl rounded-tl-md shadow-lg border-2 border-blue-100 p-4 flex items-center gap-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
              </div>
              <span className="text-sm text-gray-600">AI is thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="relative">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input 
              className="w-full p-4 pr-12 border-2 border-blue-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 transition-all duration-200 bg-white shadow-inner" 
              value={query} 
              onChange={e=>setQuery(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && !loading && send()}
              disabled={loading}
              placeholder="Ask about surgical procedures..."
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </div>
          </div>
          <button 
            onClick={send}
            disabled={loading || !query}
            className={`px-6 py-4 rounded-xl font-semibold text-white shadow-lg transition-all duration-300 transform ${
              loading || !query
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 hover:scale-105 hover:shadow-xl'
            }`}
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
