import { useState } from 'react'
import { Database, Play, RefreshCw } from 'lucide-react'

export default function Dataset() {
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState(null)
  const [message, setMessage] = useState('')

  const loadDataset = async () => {
    setLoading(true)
    setMessage('')
    try {
      // Sampled load by default — full train files are millions of rows
      const response = await fetch('/api/dataset/load?nrows=10000', { method: 'POST' })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`)
      }
      const rows = data.train_rows
      setMessage(
        `Dataset loaded${data.sampled ? ` (sample of ${data.nrows} rows/source)` : ''}: ` +
        `S1=${rows.source1.toLocaleString()}, S2=${rows.source2.toLocaleString()}, ` +
        `S3=${rows.source3.toLocaleString()}, GT=${rows.ground_truth.toLocaleString()}`
      )
      
      // Fetch stats after loading
      const statsResponse = await fetch('/api/dataset/stats')
      const statsData = await statsResponse.json()
      if (!statsResponse.ok) {
        throw new Error(statsData.detail || `HTTP ${statsResponse.status}`)
      }
      setStats(statsData)
    } catch (error) {
      setMessage('Error loading dataset: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/dataset/stats')
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
      <h1 className="text-3xl font-bold text-white">Dataset</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="flex gap-4 mb-6">
          <button
            onClick={loadDataset}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <Play className="w-5 h-5 mr-2" />
            Load Dataset
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
            <h3 className="text-lg font-semibold text-white">Dataset Statistics</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-700 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Training Data</h4>
                <div className="text-gray-300 space-y-1">
                  <p>Source 1: {stats.train.source1_rows.toLocaleString()} rows</p>
                  <p>Source 2: {stats.train.source2_rows.toLocaleString()} rows</p>
                  <p>Source 3: {stats.train.source3_rows.toLocaleString()} rows</p>
                  <p>Ground Truth: {stats.train.ground_truth_rows.toLocaleString()} rows</p>
                </div>
              </div>
              
              <div className="bg-gray-700 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Columns</h4>
                <div className="text-gray-300 space-y-1">
                  <p>Source 1: {stats.train.source1_columns.join(', ')}</p>
                  <p>Source 2: {stats.train.source2_columns.join(', ')}</p>
                  <p>Source 3: {stats.train.source3_columns.join(', ')}</p>
                </div>
              </div>

              <div className="bg-gray-700 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Missing Values</h4>
                <div className="text-gray-300 space-y-1">
                  <p>Source 2 Address: {stats.train.missing_values.source2.business_address.toLocaleString()}</p>
                  <p>Source 3 Address: {stats.train.missing_values.source3.business_address.toLocaleString()}</p>
                </div>
              </div>

              <div className="bg-gray-700 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Duplicate IDs</h4>
                <div className="text-gray-300 space-y-1">
                  <p>Source 1: {stats.train.duplicate_ids.source1}</p>
                  <p>Source 2: {stats.train.duplicate_ids.source2}</p>
                  <p>Source 3: {stats.train.duplicate_ids.source3}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
