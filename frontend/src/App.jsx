import React, {useState} from 'react'
import { useTheme } from './ThemeContext'
import ChatPanel from './components/ChatPanel'
import UploadPanel from './components/UploadPanel'
import ImageUploadPanel from './components/ImageUploadPanel'
import VisualQAPanel from './components/VisualQAPanel'
import LevelSelector from './components/LevelSelector'
import QuizPanel from './components/QuizPanel'

export default function App(){
  const { theme, toggleTheme } = useTheme()
  const [level, setLevel] = useState('Novice')
  const [activeTab, setActiveTab] = useState('chat') // 'chat' or 'multimodal'
  
  return (
    <div className="min-h-screen p-6 relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-950 dark:via-indigo-950 dark:to-purple-950 transition-colors duration-500">
      {/* Enhanced Animated Background Elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-96 h-96 bg-gradient-to-br from-blue-400/30 to-cyan-400/30 dark:from-cyan-500/20 dark:to-blue-500/20 rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-3xl opacity-40 dark:opacity-60 animate-blob"></div>
        <div className="absolute top-40 right-10 w-96 h-96 bg-gradient-to-br from-purple-400/30 to-pink-400/30 dark:from-purple-500/20 dark:to-fuchsia-500/20 rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-3xl opacity-40 dark:opacity-60 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-gradient-to-br from-indigo-400/30 to-blue-400/30 dark:from-indigo-500/20 dark:to-cyan-500/20 rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-3xl opacity-40 dark:opacity-60 animate-blob animation-delay-4000"></div>
        <div className="absolute top-1/2 right-1/3 w-72 h-72 bg-gradient-to-br from-cyan-300/30 to-teal-400/30 dark:from-teal-500/20 dark:to-emerald-500/20 rounded-full mix-blend-multiply dark:mix-blend-lighten filter blur-3xl opacity-30 dark:opacity-50 animate-blob animation-delay-6000"></div>
      </div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Theme Toggle Button */}
        <div className="absolute top-0 right-0 animate-scale-in">
          <button
            onClick={toggleTheme}
            className="p-4 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-110 border-2 border-gray-200 dark:border-cyan-500/30 group"
            aria-label="Toggle theme"
          >
            {theme === 'light' ? (
              <svg className="w-7 h-7 text-indigo-600 group-hover:text-purple-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            ) : (
              <svg className="w-7 h-7 text-cyan-400 group-hover:text-cyan-300 group-hover:rotate-90 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            )}
          </button>
        </div>

        {/* Enhanced Hero Header */}
        <div className="text-center mb-12 animate-fade-in">
          {/* Floating Badge */}
          <div className="inline-flex items-center gap-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-blue-500 dark:via-indigo-500 dark:to-purple-500 text-white px-8 py-4 rounded-full mb-6 shadow-2xl hover:shadow-blue-500/50 dark:shadow-blue-500/30 transition-all duration-500 hover:scale-105 group">
            <div className="relative">
              <div className="absolute inset-0 bg-white dark:bg-blue-200 rounded-full blur-md opacity-50 group-hover:opacity-75 transition-opacity"></div>
              <svg className="w-9 h-9 relative z-10 group-hover:rotate-12 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span className="text-base font-bold tracking-widest uppercase">AI-Powered Education</span>
          </div>
          
          {/* Main Title with Gradient Animation */}
          <h1 className="text-7xl md:text-8xl font-black mb-6 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-blue-400 dark:via-indigo-400 dark:to-purple-400 bg-clip-text text-transparent animate-gradient bg-300% drop-shadow-lg leading-tight pb-5">
            Surgical Tutor AI
          </h1>
          
          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-gray-700 dark:text-gray-300 max-w-3xl mx-auto mb-6 font-light leading-relaxed">
            Advanced multimodal AI system for surgical education
          </p>
          
          {/* Tech Stack Pills */}
          <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
            <div className="px-5 py-2.5 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-2 border-blue-300 dark:border-cyan-500/50 rounded-full text-sm font-bold text-blue-700 dark:text-cyan-300 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300">
              🤖 GPT-4o
            </div>
            <div className="px-5 py-2.5 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-2 border-indigo-300 dark:border-indigo-500/50 rounded-full text-sm font-bold text-indigo-700 dark:text-indigo-300 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300">
              🧬 BioClinicalBERT
            </div>
            <div className="px-5 py-2.5 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-2 border-purple-300 dark:border-purple-500/50 rounded-full text-sm font-bold text-purple-700 dark:text-purple-300 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300">
              🔍 FAISS + Neo4j
            </div>
            <div className="px-5 py-2.5 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm border-2 border-pink-300 dark:border-fuchsia-500/50 rounded-full text-sm font-bold text-pink-700 dark:text-fuchsia-300 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300">
              👁️ BiomedCLIP
            </div>
          </div>
          
          {/* Warning Banner */}
          <div className="max-w-3xl mx-auto">
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-orange-400 dark:from-amber-600 dark:to-orange-600 rounded-2xl blur-md opacity-40 group-hover:opacity-60 transition-opacity"></div>
              <div className="relative flex items-center justify-center gap-3 text-sm bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/30 border-2 border-amber-300 dark:border-amber-600 rounded-2xl px-6 py-4 shadow-xl backdrop-blur-sm">
                <div className="flex-shrink-0 p-2 bg-amber-100 dark:bg-amber-800/50 rounded-lg">
                  <svg className="w-6 h-6 text-amber-600 dark:text-amber-400 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="text-left">
                  <span className="font-bold text-amber-800 dark:text-amber-300 text-base">Educational Use Only</span>
                  <span className="text-gray-700 dark:text-gray-400 mx-2">•</span>
                  <span className="text-gray-700 dark:text-gray-400">Not intended for clinical decision-making</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Mode Tabs */}
        <div className="mb-10 animate-slide-up animation-delay-200">
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-10 py-5 font-bold text-lg rounded-2xl shadow-xl transition-all duration-300 transform hover:scale-105 ${
                activeTab === 'chat'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-cyan-600 dark:to-blue-600 text-white shadow-blue-500/50 dark:shadow-cyan-500/50 scale-105'
                  : 'bg-white/90 dark:bg-slate-800/90 text-gray-700 dark:text-slate-200 hover:bg-white dark:hover:bg-slate-700/90 hover:shadow-2xl border-2 border-transparent dark:border-slate-700'
              }`}
            >
              <span className="flex items-center gap-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                Text Mode
              </span>
            </button>
            <button
              onClick={() => setActiveTab('multimodal')}
              className={`px-10 py-5 font-bold text-lg rounded-2xl shadow-xl transition-all duration-300 transform hover:scale-105 relative ${
                activeTab === 'multimodal'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 dark:from-fuchsia-600 dark:to-purple-600 text-white shadow-purple-500/50 dark:shadow-fuchsia-500/50 scale-105'
                  : 'bg-white/90 dark:bg-slate-800/90 text-gray-700 dark:text-slate-200 hover:bg-white dark:hover:bg-slate-700/90 hover:shadow-2xl border-2 border-transparent dark:border-slate-700'
              }`}
            >
              <span className="flex items-center gap-3">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                Multimodal Mode
              </span>
            </button>
          </div>
        </div>

        {/* Content based on active tab */}
        {activeTab === 'chat' ? (
          <>
            {/* Level Selector with Animation */}
            <div className="mb-10 animate-slide-up animation-delay-300">
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
          </>
        ) : (
          <>
            {/* Multimodal Mode */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div className="animate-slide-left animation-delay-400">
                <ImageUploadPanel />
              </div>
              <div className="animate-slide-right animation-delay-600">
                <VisualQAPanel />
              </div>
            </div>
          </>
        )}

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
