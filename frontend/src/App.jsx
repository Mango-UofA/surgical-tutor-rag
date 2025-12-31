import React, {useState} from 'react'
import ChatPanel from './components/ChatPanel'
import UploadPanel from './components/UploadPanel'
import LevelSelector from './components/LevelSelector'
import QuizPanel from './components/QuizPanel'

export default function App(){
  const [level, setLevel] = useState('Novice')
  return (
    <div className="min-h-screen p-6 relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Enhanced Animated Background Elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-96 h-96 bg-gradient-to-br from-blue-300 to-cyan-300 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-blob"></div>
        <div className="absolute top-40 right-10 w-96 h-96 bg-gradient-to-br from-purple-300 to-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-gradient-to-br from-indigo-300 to-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-40 animate-blob animation-delay-4000"></div>
        <div className="absolute top-1/2 right-1/3 w-72 h-72 bg-gradient-to-br from-cyan-200 to-teal-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-6000"></div>
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Enhanced Hero Header */}
        <div className="text-center mb-12 animate-fade-in">
          {/* Floating Badge */}
          <div className="inline-flex items-center gap-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white px-8 py-4 rounded-full mb-6 shadow-2xl hover:shadow-blue-500/50 transition-all duration-500 hover:scale-105 group">
            <div className="relative">
              <div className="absolute inset-0 bg-white rounded-full blur-md opacity-50 group-hover:opacity-75 transition-opacity"></div>
              <svg className="w-9 h-9 relative z-10 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <span className="text-base font-bold tracking-widest uppercase">AI-Powered Medical Education</span>
          </div>
          
          {/* Main Title with Gradient Animation */}
          <h1 className="text-7xl md:text-8xl font-black mb-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent animate-gradient bg-300% drop-shadow-lg leading-tight pb-5">
            Surgical Tutor
          </h1>
          
          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-gray-700 max-w-3xl mx-auto mb-6 font-light leading-relaxed">
            Your intelligent assistant for surgical training and education
          </p>
          
          {/* Tech Stack Pills */}
          <div className="flex flex-wrap items-center justify-center gap-3 mb-6">
            <div className="px-4 py-2 bg-white/80 backdrop-blur-sm border border-blue-200 rounded-full text-sm font-semibold text-blue-700 shadow-md hover:shadow-lg hover:scale-105 transition-all duration-300">
              🤖 GPT-4
            </div>
            <div className="px-4 py-2 bg-white/80 backdrop-blur-sm border border-indigo-200 rounded-full text-sm font-semibold text-indigo-700 shadow-md hover:shadow-lg hover:scale-105 transition-all duration-300">
              🧬 BioClinicalBERT
            </div>
            <div className="px-4 py-2 bg-white/80 backdrop-blur-sm border border-purple-200 rounded-full text-sm font-semibold text-purple-700 shadow-md hover:shadow-lg hover:scale-105 transition-all duration-300">
              🔍 FAISS Vector Search
            </div>
          </div>
          
          {/* Warning Banner */}
          <div className="max-w-3xl mx-auto">
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-orange-400 rounded-2xl blur-md opacity-40 group-hover:opacity-60 transition-opacity"></div>
              <div className="relative flex items-center justify-center gap-3 text-sm bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-2xl px-6 py-4 shadow-xl">
                <div className="flex-shrink-0 p-2 bg-amber-100 rounded-lg">
                  <svg className="w-6 h-6 text-amber-600 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="text-left">
                  <span className="font-bold text-amber-800 text-base">Educational Use Only</span>
                  <span className="text-gray-700 mx-2">•</span>
                  <span className="text-gray-700">Not intended for clinical decision-making</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Level Selector with Animation */}
        <div className="mb-10 animate-slide-up animation-delay-200">
          <LevelSelector level={level} setLevel={setLevel} />
        </div>

        {/* Main Content Grid with Staggered Animation */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="animate-slide-left animation-delay-400">
            <UploadPanel />
          </div>
          <div className="animate-slide-right animation-delay-600">
            <ChatPanel level={level} />
          </div>
        </div>

        {/* Quiz Section with Animation */}
        <div className="mt-8 animate-slide-up animation-delay-800">
          <QuizPanel level={level} />
        </div>

        {/* Enhanced Footer */}
        <div className="mt-16 pb-8">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10 rounded-3xl blur-xl"></div>
            <div className="relative bg-white/40 backdrop-blur-xl border border-white/60 rounded-3xl p-8 shadow-2xl">
              <div className="text-center space-y-6">
                {/* Status Indicators */}
                <div className="flex flex-wrap items-center justify-center gap-4">
                  <div className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-emerald-50 to-green-50 border-2 border-emerald-300 rounded-full shadow-lg hover:shadow-emerald-200 transition-all duration-300 hover:scale-105">
                    <div className="relative">
                      <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 w-3 h-3 bg-emerald-500 rounded-full animate-ping"></div>
                    </div>
                    <span className="font-bold text-emerald-700 text-sm">System Online</span>
                  </div>
                  
                  <div className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-full shadow-lg hover:shadow-blue-200 transition-all duration-300 hover:scale-105">
                    <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                    </svg>
                    <span className="font-bold text-blue-700 text-sm">AI Ready</span>
                  </div>

                  <div className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-300 rounded-full shadow-lg hover:shadow-purple-200 transition-all duration-300 hover:scale-105">
                    <svg className="w-4 h-4 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    <span className="font-bold text-purple-700 text-sm">Verified</span>
                  </div>
                </div>

                {/* Footer Text */}
                <div className="space-y-2 text-gray-600">
                  <p className="text-base font-medium">Built with ❤️ for surgical education</p>
                  <p className="text-sm">© 2025 Surgical Tutor RAG • Advancing Medical Learning with AI</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { 
            transform: translate(0, 0) scale(1); 
          }
          33% { 
            transform: translate(30px, -50px) scale(1.15); 
          }
          66% { 
            transform: translate(-20px, 20px) scale(0.9); 
          }
        }
        
        @keyframes gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(40px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideLeft {
          from { opacity: 0; transform: translateX(-40px); }
          to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes slideRight {
          from { opacity: 0; transform: translateX(40px); }
          to { opacity: 1; transform: translateX(0); }
        }
        
        .animate-blob {
          animation: blob 8s infinite ease-in-out;
        }
        
        .animate-gradient {
          background-size: 300% 300%;
          animation: gradient 6s ease infinite;
        }
        
        .animate-fade-in {
          animation: fadeIn 0.8s ease-out;
        }
        
        .animate-slide-up {
          animation: slideUp 0.8s ease-out;
        }
        
        .animate-slide-left {
          animation: slideLeft 0.8s ease-out;
        }
        
        .animate-slide-right {
          animation: slideRight 0.8s ease-out;
        }
        
        .animation-delay-200 {
          animation-delay: 0.2s;
          opacity: 0;
          animation-fill-mode: forwards;
        }
        
        .animation-delay-400 {
          animation-delay: 0.4s;
          opacity: 0;
          animation-fill-mode: forwards;
        }
        
        .animation-delay-600 {
          animation-delay: 0.6s;
          opacity: 0;
          animation-fill-mode: forwards;
        }
        
        .animation-delay-800 {
          animation-delay: 0.8s;
          opacity: 0;
          animation-fill-mode: forwards;
        }
        
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        
        .animation-delay-6000 {
          animation-delay: 6s;
        }
        
        .bg-300\% {
          background-size: 300%;
        }
      `}</style>
    </div>
  )
}
