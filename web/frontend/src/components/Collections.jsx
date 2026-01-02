import { useState, useEffect } from 'react'

function Collections({ selectedLibrary }) {
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [showKeywordModal, setShowKeywordModal] = useState(false)
  const [showStudioModal, setShowStudioModal] = useState(false)
  const [showDecadeModal, setShowDecadeModal] = useState(false)
  const [selectedPresets, setSelectedPresets] = useState([])
  const [selectedStudios, setSelectedStudios] = useState([])
  const [selectedDecades, setSelectedDecades] = useState([])
  const [customKeywords, setCustomKeywords] = useState('')
  const [expandedCollection, setExpandedCollection] = useState(null)
  const [collectionItems, setCollectionItems] = useState([])
  const [itemsTotal, setItemsTotal] = useState(0)
  const [itemsHasMore, setItemsHasMore] = useState(false)

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

    // Build decades array from selected presets
    const decades = selectedDecades.map(id =>
      decadePresets.find(d => d.id === id)
    ).filter(Boolean)

    if (decades.length === 0) {
      alert('Please select at least one decade')
      return
    }

    setCreating(true)
    setShowDecadeModal(false)

    try {
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
        alert(`Created ${data.created} decade collection${data.created > 1 ? 's' : ''}!`)
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

    // Build studios array from selected presets
    const studios = selectedStudios.map(id =>
      studioPresets.find(s => s.id === id)
    ).filter(Boolean)

    if (studios.length === 0) {
      alert('Please select at least one studio')
      return
    }

    setCreating(true)
    setShowStudioModal(false)

    try {
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
        alert(`Created ${data.created} studio collection${data.created > 1 ? 's' : ''}!`)
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

  // Movie studio presets
  const movieStudioPresets = [
    { id: 'marvel', title: 'Marvel Cinematic Universe', studios: ['Marvel Studios'] },
    { id: 'dc', title: 'DC Universe', studios: ['DC Comics', 'DC Entertainment'] },
    { id: 'disney', title: 'Disney Classics', studios: ['Walt Disney Pictures', 'Disney'] },
    { id: 'pixar', title: 'Pixar', studios: ['Pixar', 'Pixar Animation Studios'] },
    { id: 'warner', title: 'Warner Bros', studios: ['Warner Bros.', 'Warner Brothers'] },
    { id: 'universal', title: 'Universal Pictures', studios: ['Universal Pictures', 'Universal'] },
    { id: 'paramount', title: 'Paramount Pictures', studios: ['Paramount Pictures', 'Paramount'] },
    { id: 'sony', title: 'Sony Pictures', studios: ['Sony Pictures', 'Columbia Pictures'] },
    { id: 'a24', title: 'A24', studios: ['A24'] },
    { id: 'dreamworks', title: 'DreamWorks', studios: ['DreamWorks', 'DreamWorks Animation'] },
    { id: 'lionsgate', title: 'Lionsgate', studios: ['Lionsgate', 'Lions Gate'] },
    { id: 'ghibli', title: 'Studio Ghibli', studios: ['Studio Ghibli'] }
  ]

  // TV show studio/network presets
  const tvStudioPresets = [
    { id: 'netflix', title: 'Netflix Originals', studios: ['Netflix'] },
    { id: 'hbo', title: 'HBO', studios: ['HBO', 'HBO Max'] },
    { id: 'amazon', title: 'Amazon Prime', studios: ['Amazon', 'Amazon Studios', 'Prime Video'] },
    { id: 'apple', title: 'Apple TV+', studios: ['Apple TV+', 'Apple'] },
    { id: 'disney-plus', title: 'Disney+', studios: ['Disney+'] },
    { id: 'hulu', title: 'Hulu', studios: ['Hulu'] },
    { id: 'showtime', title: 'Showtime', studios: ['Showtime'] },
    { id: 'starz', title: 'Starz', studios: ['Starz'] },
    { id: 'fx', title: 'FX', studios: ['FX', 'FX Productions'] },
    { id: 'amc', title: 'AMC', studios: ['AMC', 'AMC Studios'] },
    { id: 'paramount-plus', title: 'Paramount+', studios: ['Paramount+', 'CBS'] },
    { id: 'peacock', title: 'Peacock', studios: ['Peacock', 'NBC'] },
    { id: 'bbc', title: 'BBC', studios: ['BBC', 'BBC One', 'BBC Two'] }
  ]

  // Use appropriate presets based on library type
  const studioPresets = selectedLibrary?.type === 'show' ? tvStudioPresets : movieStudioPresets

  const decadePresets = [
    { id: '1950s', title: '1950s Movies', start: 1950, end: 1959 },
    { id: '1960s', title: '1960s Movies', start: 1960, end: 1969 },
    { id: '1970s', title: '1970s Movies', start: 1970, end: 1979 },
    { id: '1980s', title: '1980s Movies', start: 1980, end: 1989 },
    { id: '1990s', title: '1990s Movies', start: 1990, end: 1999 },
    { id: '2000s', title: '2000s Movies', start: 2000, end: 2009 },
    { id: '2010s', title: '2010s Movies', start: 2010, end: 2019 },
    { id: '2020s', title: '2020s Movies', start: 2020, end: 2029 }
  ]

  const openKeywordModal = () => {
    setShowKeywordModal(true)
    setSelectedPresets([])
    setCustomKeywords('')
  }

  const openStudioModal = () => {
    setShowStudioModal(true)
    setSelectedStudios([])
  }

  const openDecadeModal = () => {
    setShowDecadeModal(true)
    setSelectedDecades([])
  }

  const togglePreset = (presetId) => {
    setSelectedPresets(prev =>
      prev.includes(presetId)
        ? prev.filter(id => id !== presetId)
        : [...prev, presetId]
    )
  }

  const toggleStudio = (studioId) => {
    setSelectedStudios(prev =>
      prev.includes(studioId)
        ? prev.filter(id => id !== studioId)
        : [...prev, studioId]
    )
  }

  const toggleDecade = (decadeId) => {
    setSelectedDecades(prev =>
      prev.includes(decadeId)
        ? prev.filter(id => id !== decadeId)
        : [...prev, decadeId]
    )
  }

  const deleteCollection = async (collectionTitle) => {
    if (!selectedLibrary) return

    if (!confirm(`Delete collection "${collectionTitle}"? This cannot be undone.`)) {
      return
    }

    try {
      const res = await fetch(`/api/collections/${encodeURIComponent(collectionTitle)}?library_name=${selectedLibrary.name}`, {
        method: 'DELETE'
      })

      const data = await res.json()
      if (data.status === 'success') {
        alert(`Deleted collection: ${collectionTitle}`)
        fetchCollections()
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error('Failed to delete collection:', error)
      alert('Failed to delete collection')
    }
  }

  const toggleCollectionExpansion = async (collectionTitle) => {
    // If clicking the same collection, collapse it
    if (expandedCollection === collectionTitle) {
      setExpandedCollection(null)
      setCollectionItems([])
      setItemsTotal(0)
      setItemsHasMore(false)
      return
    }

    // Expand new collection
    setExpandedCollection(collectionTitle)
    setCollectionItems([]) // Clear previous items
    setItemsTotal(0)
    setItemsHasMore(false)

    // Fetch items
    try {
      const res = await fetch(`/api/collections/${encodeURIComponent(collectionTitle)}/items?library_name=${selectedLibrary.name}`)
      const data = await res.json()

      // Only update if this collection is still the expanded one (prevents race condition)
      if (data.items) {
        setExpandedCollection(current => {
          if (current === collectionTitle) {
            setCollectionItems(data.items)
            setItemsTotal(data.total || data.items.length)
            setItemsHasMore(data.has_more || false)
          }
          return current
        })
      }
    } catch (error) {
      console.error('Failed to fetch collection items:', error)
    }
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
        if (data.created === 0) {
          alert('0 collections created - all already exist')
        } else {
          alert(`Created ${data.created} keyword collection${data.created > 1 ? 's' : ''}!`)
        }
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
            onClick={openDecadeModal}
            disabled={creating}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition"
          >
            📅 Create Decade Collections
          </button>
          <button
            onClick={openStudioModal}
            disabled={creating}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition"
          >
            {selectedLibrary?.type === 'show' ? '📺 Create Network Collections' : '🎬 Create Studio Collections'}
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-start">
            {collections.map((collection) => {
              const isExpanded = expandedCollection === collection.title
              return (
                <div
                  key={collection.title}
                  className="bg-gray-900 rounded-lg border border-gray-700 relative group overflow-hidden"
                >
                  {/* Collection Header - Clickable */}
                  <div
                    onClick={() => toggleCollectionExpansion(collection.title)}
                    className="p-4 cursor-pointer hover:bg-gray-800 transition"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-semibold text-white pr-8">{collection.title}</div>
                        <div className="text-sm text-gray-400 mt-1">
                          {collection.count} items
                        </div>
                        {collection.summary && !isExpanded && (
                          <div className="text-xs text-gray-500 mt-2 line-clamp-2">
                            {collection.summary}
                          </div>
                        )}
                      </div>
                      {/* Expand/Collapse Indicator */}
                      <div className="text-gray-400 text-sm ml-2">
                        {isExpanded ? '▼' : '▶'}
                      </div>
                    </div>
                  </div>

                  {/* Delete button - appears on hover */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteCollection(collection.title)
                    }}
                    className="absolute top-2 right-8 opacity-0 group-hover:opacity-100 transition bg-red-600 hover:bg-red-700 text-white text-xs px-2 py-1 rounded z-10"
                    title="Delete collection"
                  >
                    ✕
                  </button>

                  {/* Expanded Items List */}
                  {isExpanded && (
                    <div className="border-t border-gray-700 p-4 bg-gray-950 max-h-96 overflow-y-auto">
                      {collectionItems.length === 0 ? (
                        <div className="text-gray-500 text-sm">Loading items...</div>
                      ) : (
                        <>
                          <div className="space-y-2">
                            {collectionItems.map((item, idx) => (
                              <div key={idx} className="flex justify-between items-center text-sm">
                                <div className="text-gray-300">
                                  {item.title}
                                  {item.year && <span className="text-gray-500 ml-2">({item.year})</span>}
                                </div>
                                {item.rating && (
                                  <div className="text-yellow-500 text-xs">★ {item.rating}</div>
                                )}
                              </div>
                            ))}
                          </div>
                          {itemsHasMore && (
                            <div className="mt-3 pt-3 border-t border-gray-800 text-gray-500 text-xs text-center">
                              + {itemsTotal - collectionItems.length} more items (showing first {collectionItems.length} of {itemsTotal})
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Studio Collections Modal */}
      {showStudioModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={() => setShowStudioModal(false)}>
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 border border-gray-700" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold mb-4">
              {selectedLibrary?.type === 'show' ? 'Create Network Collections' : 'Create Studio Collections'}
            </h2>

            {/* Studio checkboxes */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">
                {selectedLibrary?.type === 'show' ? 'Select Networks:' : 'Select Studios:'}
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {studioPresets.map(studio => (
                  <label key={studio.id} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedStudios.includes(studio.id)}
                      onChange={() => toggleStudio(studio.id)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">{studio.title}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowStudioModal(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={createStudioCollections}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition font-semibold"
              >
                Create Collections
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Decade Collections Modal */}
      {showDecadeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={() => setShowDecadeModal(false)}>
          <div className="bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 border border-gray-700" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-2xl font-bold mb-4">Create Decade Collections</h2>

            {/* Decade checkboxes */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Select Decades:</h3>
              <div className="grid grid-cols-2 gap-3">
                {decadePresets.map(decade => (
                  <label key={decade.id} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedDecades.includes(decade.id)}
                      onChange={() => toggleDecade(decade.id)}
                      className="w-4 h-4"
                    />
                    <span className="text-sm">{decade.title}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDecadeModal(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={createDecadeCollections}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition font-semibold"
              >
                Create Collections
              </button>
            </div>
          </div>
        </div>
      )}

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
