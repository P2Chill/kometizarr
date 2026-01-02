import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import ProcessingProgress from './components/ProcessingProgress'

function App() {
  const [processing, setProcessing] = useState(false)
  const [progressData, setProgressData] = useState(null)

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-white">
            🎬 Kometizarr
          </h1>
          <p className="text-gray-400 mt-1">
            Beautiful multi-source rating overlays for Plex
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {processing ? (
          <ProcessingProgress
            onComplete={() => setProcessing(false)}
            progressData={progressData}
            setProgressData={setProgressData}
          />
        ) : (
          <Dashboard onStartProcessing={() => setProcessing(true)} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-gray-500 text-sm">
          Kometizarr v1.0.0 | Better than Kometa ✨
        </div>
      </footer>
    </div>
  )
}

export default App
