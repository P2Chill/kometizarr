import { useState, useEffect } from 'react'

function Dashboard({ onStartProcessing, onLibrarySelect }) {
  const [libraries, setLibraries] = useState([])
  const [selectedLibrary, setSelectedLibrary] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [position, setPosition] = useState('northwest')
  const [force, setForce] = useState(false)
  const [ratingSources, setRatingSources] = useState(() => {
    // Load from localStorage or default to all enabled
    const saved = localStorage.getItem('kometizarr_rating_sources')
    return saved ? JSON.parse(saved) : {
      tmdb: true,
      imdb: true,
      rt_critic: true,
      rt_audience: true
    }
  })
  const [badgeStyle, setBadgeStyle] = useState(() => {
    // Load from localStorage or use defaults
    const saved = localStorage.getItem('kometizarr_badge_style')
    return saved ? JSON.parse(saved) : {
      badge_width_percent: 35,  // Percentage of poster width
      font_size_multiplier: 1.0, // Multiplier for font sizes
      rating_color: '#FFD700',   // Gold color (default)
      background_opacity: 128    // 0-255, default 128 (50%)
    }
  })

  useEffect(() => {
    fetchLibraries()
  }, [])

  useEffect(() => {
    if (selectedLibrary) {
      fetchStats(selectedLibrary.name)
      if (onLibrarySelect) {
        onLibrarySelect(selectedLibrary)
      }
    }
  }, [selectedLibrary])

  const fetchLibraries = async () => {
    try {
      const res = await fetch('/api/libraries')
      const data = await res.json()
      if (data.libraries) {
        setLibraries(data.libraries)
        if (data.libraries.length > 0) {
          setSelectedLibrary(data.libraries[0])
        }
      }
    } catch (error) {
      console.error('Failed to fetch libraries:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async (libraryName) => {
    try {
      const res = await fetch(`/api/library/${libraryName}/stats`)
      const data = await res.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  const toggleRatingSource = (source) => {
    const updated = { ...ratingSources, [source]: !ratingSources[source] }
    setRatingSources(updated)
    localStorage.setItem('kometizarr_rating_sources', JSON.stringify(updated))
  }

  const updateBadgeStyle = (key, value) => {
    const updated = { ...badgeStyle, [key]: value }
    setBadgeStyle(updated)
    localStorage.setItem('kometizarr_badge_style', JSON.stringify(updated))
  }

  const startProcessing = async () => {
    if (!selectedLibrary) return

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_name: selectedLibrary.name,
          position,
          force,
          rating_sources: ratingSources,
          badge_style: badgeStyle,  // Include badge styling options
        }),
      })

      const data = await res.json()
      if (data.status === 'started') {
        onStartProcessing()
      }
    } catch (error) {
      console.error('Failed to start processing:', error)
    }
  }

  const restoreOriginals = async () => {
    if (!selectedLibrary) return

    if (!confirm(`Restore all original posters in ${selectedLibrary.name}? This will remove all overlays.`)) {
      return
    }

    try {
      const res = await fetch('/api/restore', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_name: selectedLibrary.name,
        }),
      })

      const data = await res.json()
      if (data.status === 'started') {
        onStartProcessing() // Use same callback to show progress view
      } else if (data.error) {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Failed to restore originals:', error)
      alert('Failed to restore originals')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading libraries...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Library Selection */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Select Library</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {libraries.map((lib) => (
            <button
              key={lib.name}
              onClick={() => setSelectedLibrary(lib)}
              className={`p-4 rounded-lg border-2 transition ${
                selectedLibrary?.name === lib.name
                  ? 'border-blue-500 bg-blue-900/20'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="text-left">
                <div className="font-semibold">{lib.name}</div>
                <div className="text-sm text-gray-400 mt-1">
                  {lib.type === 'movie' ? '🎬' : '📺'} {lib.count} items
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Library Stats */}
      {stats && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Library Statistics</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-900 rounded-lg p-4">
              <div className="text-gray-400 text-sm">Total Items</div>
              <div className="text-3xl font-bold mt-1">{stats.total_items}</div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4">
              <div className="text-gray-400 text-sm">With Backups</div>
              <div className="text-3xl font-bold mt-1 text-green-400">
                {stats.processed_items}
              </div>
            </div>
            <div className="bg-gray-900 rounded-lg p-4">
              <div className="text-gray-400 text-sm">Backup Coverage</div>
              <div className="text-3xl font-bold mt-1 text-blue-400">
                {stats.success_rate}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Processing Options */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Processing Options</h2>
        <div className="space-y-4">
          {/* Position - Visual Selector */}
          <div>
            <label className="block text-sm font-medium mb-2">Badge Position</label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { value: 'northwest', label: 'Top Left', badge: { x: '10', y: '10' } },
                { value: 'northeast', label: 'Top Right', badge: { x: '110', y: '10' } },
                { value: 'southwest', label: 'Bottom Left', badge: { x: '10', y: '130' } },
                { value: 'southeast', label: 'Bottom Right', badge: { x: '110', y: '130' } }
              ].map(({ value, label, badge }) => (
                <button
                  key={value}
                  onClick={() => setPosition(value)}
                  className={`relative p-3 rounded-lg border-2 transition ${
                    position === value
                      ? 'border-blue-500 bg-blue-900/30'
                      : 'border-gray-700 hover:border-gray-600 bg-gray-900'
                  }`}
                >
                  {/* Poster Preview SVG */}
                  <svg viewBox="0 0 200 280" className="w-full h-auto mb-2">
                    {/* Poster Background */}
                    <rect x="0" y="0" width="200" height="280" fill="#1f2937" stroke="#4b5563" strokeWidth="2" rx="4" />

                    {/* Grid lines for visual interest */}
                    <line x1="0" y1="93" x2="200" y2="93" stroke="#374151" strokeWidth="1" opacity="0.3" />
                    <line x1="0" y1="186" x2="200" y2="186" stroke="#374151" strokeWidth="1" opacity="0.3" />

                    {/* Badge Rectangle */}
                    <rect
                      x={badge.x}
                      y={badge.y}
                      width="80"
                      height="60"
                      fill="#3b82f6"
                      fillOpacity="0.8"
                      rx="4"
                    />

                    {/* Badge Icon (simplified rating display) */}
                    <circle cx={parseInt(badge.x) + 15} cy={parseInt(badge.y) + 20} r="8" fill="#fbbf24" />
                    <text
                      x={parseInt(badge.x) + 35}
                      y={parseInt(badge.y) + 25}
                      fill="white"
                      fontSize="14"
                      fontWeight="bold"
                    >
                      8.5
                    </text>

                    <circle cx={parseInt(badge.x) + 15} cy={parseInt(badge.y) + 43} r="8" fill="#f59e0b" />
                    <text
                      x={parseInt(badge.x) + 35}
                      y={parseInt(badge.y) + 48}
                      fill="white"
                      fontSize="14"
                      fontWeight="bold"
                    >
                      7.9
                    </text>
                  </svg>

                  {/* Label */}
                  <div className="text-sm text-center font-medium">{label}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Force */}
          <div className="flex items-center">
            <input
              type="checkbox"
              checked={force}
              onChange={(e) => setForce(e.target.checked)}
              className="mr-3"
              id="force-checkbox"
            />
            <label htmlFor="force-checkbox" className="text-sm">
              Force reprocess (use when updating ratings or changing which sources to display)
            </label>
          </div>
          {force && (
            <div className="mt-2 p-3 bg-blue-900/20 border border-blue-700/50 rounded text-sm text-blue-300">
              ℹ️ Uses original posters from backup to apply fresh overlays with updated ratings. Original backups are never overwritten.
            </div>
          )}

          {/* Rating Sources */}
          <div>
            <label className="block text-sm font-medium mb-2">Rating Sources to Display</label>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={ratingSources.tmdb}
                  onChange={() => toggleRatingSource('tmdb')}
                  className="mr-2"
                  id="tmdb-checkbox"
                />
                <label htmlFor="tmdb-checkbox" className="text-sm">
                  🎬 TMDB (0-10 scale)
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={ratingSources.imdb}
                  onChange={() => toggleRatingSource('imdb')}
                  className="mr-2"
                  id="imdb-checkbox"
                />
                <label htmlFor="imdb-checkbox" className="text-sm">
                  ⭐ IMDb (0-10 scale)
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={ratingSources.rt_critic}
                  onChange={() => toggleRatingSource('rt_critic')}
                  className="mr-2"
                  id="rt-critic-checkbox"
                />
                <label htmlFor="rt-critic-checkbox" className="text-sm">
                  🍅 RT Critic (0-100%)
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={ratingSources.rt_audience}
                  onChange={() => toggleRatingSource('rt_audience')}
                  className="mr-2"
                  id="rt-audience-checkbox"
                />
                <label htmlFor="rt-audience-checkbox" className="text-sm">
                  🍿 RT Audience (0-100%)
                </label>
              </div>
            </div>
            {!Object.values(ratingSources).some(v => v) && (
              <div className="mt-2 p-3 bg-red-900/20 border border-red-700/50 rounded text-sm text-red-300">
                ⚠️ At least one rating source must be selected
              </div>
            )}
          </div>

          {/* Badge Styling Options */}
          <div>
            <label className="block text-sm font-medium mb-3">Badge Styling (Optional)</label>
            <div className="space-y-4 bg-gray-900 rounded-lg p-4">
              {/* Badge Size */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">
                  Badge Size: {badgeStyle.badge_width_percent}% of poster width
                </label>
                <input
                  type="range"
                  min="20"
                  max="50"
                  step="1"
                  value={badgeStyle.badge_width_percent}
                  onChange={(e) => updateBadgeStyle('badge_width_percent', parseInt(e.target.value))}
                  className="w-full accent-blue-500"
                />
              </div>

              {/* Font Size */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">
                  Font Size: {badgeStyle.font_size_multiplier.toFixed(1)}x
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  value={badgeStyle.font_size_multiplier}
                  onChange={(e) => updateBadgeStyle('font_size_multiplier', parseFloat(e.target.value))}
                  className="w-full accent-blue-500"
                />
              </div>

              {/* Rating Color */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">
                  Rating Text Color
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    value={badgeStyle.rating_color}
                    onChange={(e) => updateBadgeStyle('rating_color', e.target.value)}
                    className="w-12 h-10 rounded border border-gray-700 bg-gray-800 cursor-pointer"
                  />
                  <span className="text-sm text-gray-300 font-mono">{badgeStyle.rating_color}</span>
                  <button
                    onClick={() => updateBadgeStyle('rating_color', '#FFD700')}
                    className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700"
                  >
                    Reset to Gold
                  </button>
                </div>
              </div>

              {/* Background Opacity */}
              <div>
                <label className="text-xs text-gray-400 block mb-2">
                  Background Opacity: {Math.round((badgeStyle.background_opacity / 255) * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="255"
                  step="5"
                  value={badgeStyle.background_opacity}
                  onChange={(e) => updateBadgeStyle('background_opacity', parseInt(e.target.value))}
                  className="w-full accent-blue-500"
                />
              </div>

              {/* Reset Button */}
              <button
                onClick={() => {
                  const defaults = {
                    badge_width_percent: 35,
                    font_size_multiplier: 1.0,
                    rating_color: '#FFD700',
                    background_opacity: 128
                  }
                  setBadgeStyle(defaults)
                  localStorage.setItem('kometizarr_badge_style', JSON.stringify(defaults))
                }}
                className="w-full text-xs px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 transition"
              >
                ↺ Reset All to Defaults
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={restoreOriginals}
              disabled={!selectedLibrary}
              className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition"
            >
              🔄 Restore {selectedLibrary?.name}
            </button>
            <button
              onClick={startProcessing}
              disabled={!selectedLibrary}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition"
            >
              ▶️ Process {selectedLibrary?.name}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
