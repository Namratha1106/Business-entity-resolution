import { useState } from 'react'
import { Play, Brain, List } from 'lucide-react'

export default function Features() {
  const [loading, setLoading] = useState(false)
  const [featureNames, setFeatureNames] = useState([])
  const [message, setMessage] = useState('')

  const computeFeatures = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch('/api/features/compute', { method: 'POST' })
      const data = await response.json()
      setMessage(`Computed ${data.feature_rows.toLocaleString()} feature rows with ${data.feature_columns} features`)
    } catch (error) {
      setMessage('Error computing features: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchFeatureNames = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/features/names')
      const data = await response.json()
      setFeatureNames(data.feature_names)
    } catch (error) {
      setMessage('Error fetching feature names: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Feature Engineering</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="mb-4 text-gray-300">
          <p>Feature types computed for each candidate pair:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li><strong>Name Similarity:</strong> Exact match, Levenshtein, Jaro-Winkler, Token sort/set ratio, Jaccard, Length diff</li>
            <li><strong>Address Similarity:</strong> Exact match, Levenshtein, Jaro-Winkler, Token sort/set ratio, Jaccard, Length diff</li>
            <li><strong>Country Match:</strong> Binary indicator for country equality</li>
          </ul>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={computeFeatures}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <Play className="w-5 h-5 mr-2" />
            Compute Features
          </button>
          <button
            onClick={fetchFeatureNames}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-600"
          >
            <List className="w-5 h-5 mr-2" />
            Show Feature Names
          </button>
        </div>

        {message && (
          <div className="mb-4 p-4 bg-blue-900 text-white rounded-md">
            {message}
          </div>
        )}

        {featureNames.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Feature Names</h3>
            <div className="bg-gray-700 p-4 rounded-md">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {featureNames.map((name, idx) => (
                  <div key={idx} className="text-gray-300 text-sm">
                    {name}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
