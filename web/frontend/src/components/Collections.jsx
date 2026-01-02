import { useState, useEffect } from 'react'

function Collections({ selectedLibrary }) {
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [showKeywordModal, setShowKeywordModal] = useState(false)
  const [selectedPresets, setSelectedPresets] = useState([])
  const [customKeywords, setCustomKeywords] = useState('')

  useEffect(() => {
    if (selectedLibrary) {
      fetchCollections()
    }
  }, [selectedLibrary])

  const fetchCollections = async () => {
    if (!selectedLibrary) return

    setLoading(true)
    try {
      const res = await fetch(`/api/collections?library_name=${selectedLibrary.name}`)
      const data = await res.json()
      if (data.collections) {
        setCollections(data.collections)
      }
    } catch (error) {
      console.error('Failed to fetch collections:', error)
    } finally {
      setLoading(false)
    }
  }

  const createDecadeCollections = async () => {
    if (!selectedLibrary) return

    setCreating(true)
    try {
      const decades = [
        { title: '1950s Movies', start: 1950, end: 1959 },
        { title: '1960s Movies', start: 1960, end: 1969 },
        { title: '1970s Movies', start: 1970, end: 1979 },
        { title: '1980s Movies', start: 1980, end: 1989 },
        { title: '1990s Movies', start: 1990, end: 1999 },
        { title: '2000s Movies', start: 2000, end: 2009 },
        { title: '2010s Movies', start: 2010, end: 2019 },
        { title: '2020s Movies', start: 2020, end: 2029 }
      ]

      const res = await fetch('/api/collections/decade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_name: selectedLibrary.name,
          decades
        })
      })

      const data = await res.json()
      if (data.status === 'success') {
        alert(`Created ${data.created} decade collections!`)
        fetchCollections()
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Failed to create decade collections:', error)
      alert('Failed to create decade collections')
    } finally {
      setCreating(false)
    }
  }

  const createStudioCollections = async () => {
    if (!selectedLibrary) return

    setCreating(true)
    try {
      const studios = [
        { title: 'Marvel Cinematic Universe', studios: ['Marvel Studios'] },
        { title: 'DC Universe', studios: ['DC Comics', 'DC Entertainment'] },
        { title: 'Disney Classics', studios: ['Walt Disney Pictures', 'Disney'] },
        { title: 'Pixar', studios: ['Pixar', 'Pixar Animation Studios'] },
        { title: 'Warner Bros', studios: ['Warner Bros.', 'Warner Brothers'] }
      ]

      const res = await fetch('/api/collections/studio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_name: selectedLibrary.name,
          studios
        })
      })

      const data = await res.json()
      if (data.status === 'success') {
        alert(`Created ${data.created} studio collections!`)
        fetchCollections()
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Failed to create studio collections:', error)
      alert('Failed to create studio collections')
    } finally {
      setCreating(false)
    }
  }

  const keywordPresets = [
    { id: 'zombies', title: 'Zombies', keywords: ['zombie', 'zombies', 'undead'] },
    { id: 'time-travel', title: 'Time Travel', keywords: ['time travel', 'time machine', 'time loop'] },
    { id: 'superheroes', title: 'Superheroes', keywords: ['superhero', 'superheroes', 'comic book'] },
    { id: 'space', title: 'Space Adventure', keywords: ['space', 'outer space', 'spacecraft', 'astronaut'] },
    { id: 'heist', title: 'Heist', keywords: ['heist', 'robbery', 'bank robbery', 'casino'] },
    { id: 'dinosaurs', title: 'Dinosaurs', keywords: ['dinosaur', 'dinosaurs', 'prehistoric'] }
  ]

  const openKeywordModal = () => {
    setShowKeywordModal(true)
    setSelectedPresets([])
    setCustomKeywords('')
  }

  const togglePreset = (presetId) => {
    setSelectedPresets(prev =>
      prev.includes(presetId)
        ? prev.filter(id => id !== presetId)
        : [...prev, presetId]
    )
  }

  const createKeywordCollections = async () => {
    if (!selectedLibrary) return

    // Build keywords array from selected presets
    const keywords = selectedPresets.map(id =>
      keywordPresets.find(p => p.id === id)
    ).filter(Boolean)

    // Parse custom keywords (format: "Title: keyword1, keyword2")
    if (customKeywords.trim()) {
      const lines = customKeywords.trim().split('\n')
      for (const line of lines) {
        if (line.includes(':')) {
          const [title, keywordStr] = line.split(':')
          const keywordList = keywordStr.split(',').map(k => k.trim()).filter(Boolean)
          if (title.trim() && keywordList.length > 0) {
            keywords.push({
              title: title.trim(),
              keywords: keywordList
            })
          }
        }
      }
    }

    if (keywords.length === 0) {
      alert('Please select at least one preset or add custom keywords')
      return
    }

    setCreating(true)
    setShowKeywordModal(false)

    try {
      const res = await fetch('/api/collections/keyword', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          library_name: selectedLibrary.name,
          keywords
        })
      })

      const data = await res.json()
      if (data.status === 'success') {
        alert(`Created ${data.created} keyword collections!`)
        fetchCollections()
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Failed to create keyword collections:', error)
      alert('Failed to create keyword collections')
    } finally {
      setCreating(false)
    }
  }

  if (!selectedLibrary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Select a library first</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Create Collections</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={createDecadeCollections}
            disabled={creating}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition"
          >
            📅 Create Decade Collections
          </button>
          <button
            onClick={createStudioCollections}
            disabled={creating}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition"
          >
            🎬 Create Studio Collections
          </button>
          <button
            onClick={openKeywordModal}
            disabled={creating}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition"
          >
            🔍 Create Keyword Collections
          </button>
        </div>
        {creating && (
          <div className="mt-4 text-center text-blue-400">
            Creating collections... This may take a minute.
          </div>
        )}
      </div>

      {/* Existing Collections */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Existing Collections</h2>
          <button
            onClick={fetchCollections}
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            🔄 Refresh
          </button>
        </div>

        {loading ? (
          <div className="text-center text-gray-400 py-8">Loading...</div>
        ) : collections.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            No collections yet. Create some using the buttons above!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {collections.map((collection) => (
              <div
                key={collection.title}
                className="bg-gray-900 rounded-lg p-4 border border-gray-700"
              >
                <div className="font-semibold text-white">{collection.title}</div>
                <div className="text-sm text-gray-400 mt-1">
                  {collection.count} items
                </div>
                {collection.summary && (
                  <div className="text-xs text-gray-500 mt-2 line-clamp-2">
                    {collection.summary}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Keyword Collections Modal */}
      {showKeywordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={() => setShowKeywordModal(false)}>
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 border border-gray-700" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold mb-4">Create Keyword Collections</h2>

            {/* Preset checkboxes */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Select Presets:</h3>
              <div className="grid grid-cols-2 gap-3">
                {keywordPresets.map(preset => (
                  <label key={preset.id} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedPresets.includes(preset.id)}
                      onChange={() => togglePreset(preset.id)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">{preset.title}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Custom keywords input */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Add Custom Keywords:</h3>
              <p className="text-sm text-gray-400 mb-2">
                Format: <code className="bg-gray-900 px-1 rounded">Title: keyword1, keyword2, keyword3</code>
              </p>
              <p className="text-xs text-gray-500 mb-3">
                Example: <code className="bg-gray-900 px-1 rounded">Artificial Intelligence: AI, robot, android, cyborg</code>
              </p>
              <textarea
                value={customKeywords}
                onChange={(e) => setCustomKeywords(e.target.value)}
                placeholder="Artificial Intelligence: AI, robot, android, cyborg&#10;Car Chases: car chase, racing, street racing"
                rows="4"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-sm"
              />
            </div>

            {/* Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowKeywordModal(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={createKeywordCollections}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition font-semibold"
              >
                Create Collections
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Collections
