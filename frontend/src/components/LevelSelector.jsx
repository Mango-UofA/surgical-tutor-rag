import React from 'react'

export default function LevelSelector({level, setLevel}){
  const levels = [
    { name: 'Novice', icon: '🌱', color: 'from-emerald-500 to-teal-600', description: 'Foundation concepts' },
    { name: 'Intermediate', icon: '📚', color: 'from-blue-500 to-indigo-600', description: 'Detailed procedures' },
    { name: 'Advanced', icon: '🎓', color: 'from-purple-500 to-pink-600', description: 'Complex techniques' }
  ]
  
  return (
    <div className="bg-white/95 dark:bg-slate-900/90 backdrop-blur-xl border border-white/50 dark:border-indigo-500/20 shadow-2xl dark:shadow-indigo-500/10 rounded-2xl p-6 hover:shadow-3xl dark:hover:shadow-indigo-500/20 transition-all duration-300">
      <div className="flex items-center gap-3 mb-6">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-indigo-600 dark:from-blue-400 dark:to-indigo-500 rounded-xl blur-md opacity-50"></div>
          <div className="relative w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 dark:from-blue-400 dark:to-indigo-500 rounded-xl flex items-center justify-center shadow-lg transform hover:rotate-12 transition-transform duration-300">
            <span className="text-2xl">📊</span>
          </div>
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-800 dark:text-gray-100">Learning Level</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">Select your expertise level</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {levels.map(l => (
          <button
            key={l.name}
            className={`relative group overflow-hidden p-6 rounded-xl transition-all duration-300 transform hover:scale-105 ${
              l.name === level 
                ? `bg-gradient-to-br ${l.color} text-white shadow-2xl ring-4 ring-offset-2 dark:ring-offset-slate-950 ring-blue-300 dark:ring-cyan-500/50` 
                : 'bg-white dark:bg-slate-800/90 border-2 border-gray-200 dark:border-slate-600 text-gray-700 dark:text-slate-200 hover:border-blue-400 dark:hover:border-cyan-500 hover:shadow-xl'
            }`}
            onClick={() => setLevel(l.name)}
          >
            {/* Shine effect on hover */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
            
            <div className="relative flex flex-col items-center gap-3">
              <div className={`text-5xl transform transition-transform duration-300 ${l.name === level ? 'scale-110' : 'group-hover:scale-110'}`}>
                {l.icon}
              </div>
              <span className="font-bold text-xl">{l.name}</span>
              <span className={`text-sm font-medium ${l.name === level ? 'text-white/90' : 'text-gray-600'}`}>
                {l.description}
              </span>
            </div>
            
            {l.name === level && (
              <div className="absolute top-3 right-3 animate-bounce">
                <div className="relative">
                  <div className="absolute inset-0 bg-white rounded-full blur-sm"></div>
                  <svg className="relative w-7 h-7 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
