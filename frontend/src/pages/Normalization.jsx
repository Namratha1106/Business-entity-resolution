import { useState } from 'react'
import { Play, RefreshCw, GitCompare } from 'lucide-react'

export default function Normalization() {
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [message, setMessage] = useState('')

  const applyNormalization = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch('/api/normalization/apply', { method: 'POST' })
      const data = await response.json()
      setMessage(data.message)
      
      // Fetch stats after applying
      const statsResponse = await fetch('/api/normalization/stats')
      const statsData = await statsResponse.json()
      setStats(statsData)
    } catch (error) {
      setMessage('Error applying normalization: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/normalization/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      setMessage('Error fetching stats: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Normalization</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="mb-4 text-gray-300">
          <p>Normalization includes:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Lowercasing all text</li>
            <li>Removing punctuation</li>
            <li>Standardizing whitespace</li>
            <li>Replacing "&" with "and"</li>
            <li>Removing legal suffixes (Ltd, Inc, Corp, etc.)</li>
            <li>Expanding address abbreviations (st → street, ave → avenue, etc.)</li>
          </ul>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={applyNormalization}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <Play className="w-5 h-5 mr-2" />
            Apply Normalization
          </button>
          <button
            onClick={fetchStats}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-600"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Refresh Stats
          </button>
        </div>

        {message && (
          <div className="mb-4 p-4 bg-blue-900 text-white rounded-md">
            {message}
          </div>
        )}

        {stats && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Normalization Statistics</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(stats).map(([source, data]) => (
                <div key={source} className="bg-gray-700 p-4 rounded-md">
                  <h4 className="text-white font-medium mb-2 capitalize">{source}</h4>
                  <div className="text-gray-300 space-y-1 text-sm">
                    <p>Name changes: {data.name_changes.toLocaleString()}</p>
                    <p>Address changes: {data.address_changes.toLocaleString()}</p>
                    <p>Empty names after: {data.empty_names_after_norm.toLocaleString()}</p>
                    <p>Empty addresses after: {data.empty_addresses_after_norm.toLocaleString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
