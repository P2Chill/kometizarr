import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import Collections from './components/Collections'
import ProcessingProgress from './components/ProcessingProgress'

function App() {
  const [processing, setProcessing] = useState(false)
  const [progressData, setProgressData] = useState(null)
  const [activeTab, setActiveTab] = useState('overlays')
  const [selectedLibrary, setSelectedLibrary] = useState(null)

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
          <>
            {/* Tabs */}
            <div className="mb-6 border-b border-gray-700">
              <nav className="flex space-x-8">
                <button
                  onClick={() => setActiveTab('overlays')}
                  className={`py-4 px-2 border-b-2 font-medium text-sm transition ${
                    activeTab === 'overlays'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  ⭐ Rating Overlays
                </button>
                <button
                  onClick={() => setActiveTab('collections')}
                  className={`py-4 px-2 border-b-2 font-medium text-sm transition ${
                    activeTab === 'collections'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  📚 Collections
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            {activeTab === 'overlays' ? (
              <Dashboard
                onStartProcessing={() => setProcessing(true)}
                onLibrarySelect={setSelectedLibrary}
              />
            ) : (
              <Collections selectedLibrary={selectedLibrary} />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 border-t border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-gray-500 text-sm">
          Kometizarr v1.0.0 ✨
        </div>
      </footer>
    </div>
  )
}

export default App
