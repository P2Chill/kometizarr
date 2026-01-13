import { useState, useEffect } from 'react'

function Dashboard({ onStartProcessing, onLibrarySelect }) {
  const [libraries, setLibraries] = useState([])
  const [selectedLibrary, setSelectedLibrary] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [position, setPosition] = useState('northwest')  // Keep for backward compat display
  const [badgePositions, setBadgePositions] = useState(() => {
    // Load from localStorage or set smart defaults (4 corners)
    const saved = localStorage.getItem('kometizarr_badge_positions')
    return saved ? JSON.parse(saved) : {
      tmdb: { x: 2, y: 2 },           // Top-left
      imdb: { x: 70, y: 2 },          // Top-right (70% across to fit ~12% badge + margin)
      rt_critic: { x: 2, y: 78 },      // Bottom-left (78% down to fit ~20% badge + margin)
      rt_audience: { x: 70, y: 78 }    // Bottom-right
    }
  })
  const [activeDragBadge, setActiveDragBadge] = useState(null)  // Which badge is being dragged
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
      individual_badge_size: 12,  // Individual badge size (% of poster width)
      font_size_multiplier: 1.0,  // Multiplier for font sizes
      rating_color: '#FFD700',    // Gold color (default)
      background_opacity: 128     // 0-255, default 128 (50%)
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

  const handlePosterDrag = (e, badgeSource) => {
    if (!activeDragBadge && !badgeSource) return  // Not dragging

    const source = badgeSource || activeDragBadge
    if (!source || !ratingSources[source]) return  // Badge not enabled

    const rect = e.currentTarget.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const clickY = e.clientY - rect.top

    // Calculate position as percentage of poster dimensions (0-100)
    // Individual badges are small (~12% of poster width)
    const badgeWidthPercent = 12
    const badgeHeightPercent = 17  // 1.4x aspect ratio

    // Center badge on cursor
    let xPercent = (clickX / rect.width) * 100 - (badgeWidthPercent / 2)
    let yPercent = (clickY / rect.height) * 100 - (badgeHeightPercent / 2)

    // Clamp to edges (2% minimum margin, 100% - badge size maximum)
    xPercent = Math.max(2, Math.min(xPercent, 100 - badgeWidthPercent - 2))
    yPercent = Math.max(2, Math.min(yPercent, 100 - badgeHeightPercent - 2))

    const newPosition = { x: Math.round(xPercent), y: Math.round(yPercent) }

    // Update only this badge's position
    const updated = { ...badgePositions, [source]: newPosition }
    setBadgePositions(updated)
    localStorage.setItem('kometizarr_badge_positions', JSON.stringify(updated))
  }

  const handleBadgeMouseDown = (e, badgeSource) => {
    e.stopPropagation()  // Prevent poster click
    setActiveDragBadge(badgeSource)
    // Don't move on initial click - only move when dragging (mousemove)
  }

  const handlePosterMouseMove = (e) => {
    if (activeDragBadge) {
      handlePosterDrag(e)
    }
  }

  const handleMouseUp = () => {
    setActiveDragBadge(null)
  }

  const startProcessing = async () => {
    if (!selectedLibrary) return

    // Filter badge_positions to only include enabled sources
    const enabledBadgePositions = {}
    Object.keys(ratingSources).forEach(source => {
      if (ratingSources[source] && badgePositions[source]) {
        enabledBadgePositions[source] = badgePositions[source]
      }
    })

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_name: selectedLibrary.name,
          position,  // Legacy, kept for backward compat
          badge_positions: enabledBadgePositions,  // New: individual badge positions
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
          {/* Position & Styling - Side by Side Layout */}
          <div>
            <label className="block text-sm font-medium mb-2">Badge Positions & Styling</label>
            <div className="bg-gray-900 rounded-lg p-4">
              <div className="flex items-start gap-6">
                {/* LEFT: Draggable Poster Preview */}
                <div className="flex-shrink-0">
                  <svg
                    viewBox="0 0 120 168"
                    className="w-48 h-auto select-none"
                    onMouseMove={handlePosterMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                  >
                    {/* Poster Background */}
                    <rect x="0" y="0" width="120" height="168" fill="#1f2937" stroke="#4b5563" strokeWidth="2" rx="3" />

                    {/* Individual Badges - dynamically sized and styled */}
                    {(() => {
                      // Calculate badge dimensions based on style settings
                      const badgeSizePercent = badgeStyle.individual_badge_size || 12
                      const badgeWidth = (badgeSizePercent / 100) * 120  // Scale to SVG viewBox
                      const badgeHeight = badgeWidth * 1.4  // 1.4 aspect ratio
                      const fontSize = (badgeWidth / 14) * 8  // Scale font with badge size
                      const opacity = (badgeStyle.background_opacity || 128) / 255

                      return (
                        <>
                          {ratingSources.tmdb && badgePositions.tmdb && (
                            <g
                              className="cursor-move"
                              onMouseDown={(e) => handleBadgeMouseDown(e, 'tmdb')}
                            >
                              <rect
                                x={(badgePositions.tmdb.x / 100) * 120}
                                y={(badgePositions.tmdb.y / 100) * 168}
                                width={badgeWidth}
                                height={badgeHeight}
                                fill="#000"
                                fillOpacity={opacity}
                                rx="2"
                              />
                              <text
                                x={(badgePositions.tmdb.x / 100) * 120 + badgeWidth / 2}
                                y={(badgePositions.tmdb.y / 100) * 168 + badgeHeight / 2}
                                fontSize={fontSize}
                                fill={badgeStyle.rating_color || '#FFD700'}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fontWeight="bold"
                                className="pointer-events-none select-none"
                              >
                                T
                              </text>
                            </g>
                          )}

                          {ratingSources.imdb && badgePositions.imdb && (
                            <g
                              className="cursor-move"
                              onMouseDown={(e) => handleBadgeMouseDown(e, 'imdb')}
                            >
                              <rect
                                x={(badgePositions.imdb.x / 100) * 120}
                                y={(badgePositions.imdb.y / 100) * 168}
                                width={badgeWidth}
                                height={badgeHeight}
                                fill="#000"
                                fillOpacity={opacity}
                                rx="2"
                              />
                              <text
                                x={(badgePositions.imdb.x / 100) * 120 + badgeWidth / 2}
                                y={(badgePositions.imdb.y / 100) * 168 + badgeHeight / 2}
                                fontSize={fontSize}
                                fill={badgeStyle.rating_color || '#FFD700'}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fontWeight="bold"
                                className="pointer-events-none select-none"
                              >
                                I
                              </text>
                            </g>
                          )}

                          {ratingSources.rt_critic && badgePositions.rt_critic && (
                            <g
                              className="cursor-move"
                              onMouseDown={(e) => handleBadgeMouseDown(e, 'rt_critic')}
                            >
                              <rect
                                x={(badgePositions.rt_critic.x / 100) * 120}
                                y={(badgePositions.rt_critic.y / 100) * 168}
                                width={badgeWidth}
                                height={badgeHeight}
                                fill="#000"
                                fillOpacity={opacity}
                                rx="2"
                              />
                              <text
                                x={(badgePositions.rt_critic.x / 100) * 120 + badgeWidth / 2}
                                y={(badgePositions.rt_critic.y / 100) * 168 + badgeHeight / 2}
                                fontSize={fontSize}
                                fill={badgeStyle.rating_color || '#FFD700'}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fontWeight="bold"
                                className="pointer-events-none select-none"
                              >
                                C
                              </text>
                            </g>
                          )}

                          {ratingSources.rt_audience && badgePositions.rt_audience && (
                            <g
                              className="cursor-move"
                              onMouseDown={(e) => handleBadgeMouseDown(e, 'rt_audience')}
                            >
                              <rect
                                x={(badgePositions.rt_audience.x / 100) * 120}
                                y={(badgePositions.rt_audience.y / 100) * 168}
                                width={badgeWidth}
                                height={badgeHeight}
                                fill="#000"
                                fillOpacity={opacity}
                                rx="2"
                              />
                              <text
                                x={(badgePositions.rt_audience.x / 100) * 120 + badgeWidth / 2}
                                y={(badgePositions.rt_audience.y / 100) * 168 + badgeHeight / 2}
                                fontSize={fontSize}
                                fill={badgeStyle.rating_color || '#FFD700'}
                                textAnchor="middle"
                                dominantBaseline="middle"
                                fontWeight="bold"
                                className="pointer-events-none select-none"
                              >
                                A
                              </text>
                            </g>
                          )}
                        </>
                      )
                    })()}
                  </svg>
                  <p className="text-xs text-gray-500 mt-2">
                    💡 Drag badges to position
                  </p>
                </div>

                {/* RIGHT: Styling Controls */}
                <div className="flex-1 space-y-3">
                  {/* Badge Size */}
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">
                      Badge Size: {badgeStyle.individual_badge_size}%
                    </label>
                    <input
                      type="range"
                      min="8"
                      max="20"
                      step="1"
                      value={badgeStyle.individual_badge_size}
                      onChange={(e) => updateBadgeStyle('individual_badge_size', parseInt(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                  </div>

                  {/* Font Size */}
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">
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
                    <label className="text-xs text-gray-400 block mb-1">
                      Rating Color
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={badgeStyle.rating_color}
                        onChange={(e) => updateBadgeStyle('rating_color', e.target.value)}
                        className="w-10 h-8 rounded border border-gray-700 bg-gray-800 cursor-pointer"
                      />
                      <span className="text-xs text-gray-400 font-mono">{badgeStyle.rating_color}</span>
                    </div>
                  </div>

                  {/* Background Opacity */}
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">
                      Background: {Math.round((badgeStyle.background_opacity / 255) * 100)}%
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
                        individual_badge_size: 12,
                        font_size_multiplier: 1.0,
                        rating_color: '#FFD700',
                        background_opacity: 128
                      }
                      setBadgeStyle(defaults)
                      localStorage.setItem('kometizarr_badge_style', JSON.stringify(defaults))
                    }}
                    className="w-full text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded border border-gray-700 transition"
                  >
                    ↺ Reset Styling
                  </button>
                </div>
              </div>
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
