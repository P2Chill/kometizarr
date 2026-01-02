import { useState, useEffect, useRef } from 'react'

function ProcessingProgress({ onComplete, progressData, setProgressData }) {
  const [ws, setWs] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/progress`
    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket connected')
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setProgressData(data)

      // Auto-complete when processing finishes
      if (data.is_processing === false && data.progress > 0) {
        setTimeout(() => {
          onComplete()
        }, 2000) // Show final stats for 2 seconds
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket disconnected')
    }

    wsRef.current = websocket
    setWs(websocket)

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  if (!progressData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Connecting...</div>
      </div>
    )
  }

  const progressPercent = progressData.total > 0
    ? Math.round((progressData.progress / progressData.total) * 100)
    : 0

  const successRate = progressData.progress > 0
    ? Math.round((progressData.success / progressData.progress) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">
            Processing {progressData.current_library}
          </h2>
          {progressData.is_processing && (
            <span className="flex items-center text-blue-400">
              <span className="animate-pulse mr-2">●</span>
              Processing...
            </span>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-400">
              {progressData.progress} / {progressData.total} items
            </span>
            <span className="font-semibold">{progressPercent}%</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-4 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Current Item */}
        {progressData.current_item && (
          <div className="text-sm text-gray-400">
            Current: <span className="text-white">{progressData.current_item}</span>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Success */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="text-gray-400 text-sm mb-1">✅ Success</div>
          <div className="text-3xl font-bold text-green-400">
            {progressData.success}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {successRate}% success rate
          </div>
        </div>

        {/* Failed */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="text-gray-400 text-sm mb-1">❌ Failed</div>
          <div className="text-3xl font-bold text-red-400">
            {progressData.failed}
          </div>
        </div>

        {/* Skipped */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="text-gray-400 text-sm mb-1">⏭️ Skipped</div>
          <div className="text-3xl font-bold text-yellow-400">
            {progressData.skipped}
          </div>
        </div>

        {/* Remaining */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="text-gray-400 text-sm mb-1">📊 Remaining</div>
          <div className="text-3xl font-bold text-blue-400">
            {progressData.total - progressData.progress}
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-4">
        <div className="flex items-start">
          <div className="text-blue-400 mr-3">ℹ️</div>
          <div>
            <div className="font-semibold text-blue-300 mb-1">Processing in progress</div>
            <div className="text-sm text-gray-400">
              Multi-source rating overlays are being applied to your Plex library.
              This page will update in real-time as items are processed.
            </div>
          </div>
        </div>
      </div>

      {/* Completion Message */}
      {!progressData.is_processing && progressData.progress > 0 && (
        <div className="bg-green-900/20 border border-green-700/50 rounded-lg p-6 text-center">
          <div className="text-4xl mb-3">🎉</div>
          <div className="text-2xl font-bold text-green-400 mb-2">
            Processing Complete!
          </div>
          <div className="text-gray-400">
            Successfully processed {progressData.success} out of {progressData.total} items
          </div>
        </div>
      )}
    </div>
  )
}

export default ProcessingProgress
