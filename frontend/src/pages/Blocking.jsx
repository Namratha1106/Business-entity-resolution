import { useState } from 'react'
import { Play, RefreshCw, Layers } from 'lucide-react'

export default function Blocking() {
  const [loading, setLoading] = useState(false)
  const [strategy, setStrategy] = useState('combined')
  const [stats, setStats] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [message, setMessage] = useState('')

  const generateCandidates = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch(`/api/blocking/generate?strategy=${strategy}`, { method: 'POST' })
      const data = await response.json()
      setMessage(`Generated ${data.candidate_count.toLocaleString()} candidates`)
      setStats(data.stats)
      
      // Fetch sample candidates
      const candidatesResponse = await fetch('/api/blocking/candidates?limit=20')
      const candidatesData = await candidatesResponse.json()
      setCandidates(candidatesData)
    } catch (error) {
      setMessage('Error generating candidates: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/blocking/stats')
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
      <h1 className="text-3xl font-bold text-white">Blocking</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="mb-4 text-gray-300">
          <p>Blocking strategies to reduce O(n²) complexity:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li><strong>Name Token:</strong> Block on first 2 tokens of business name</li>
            <li><strong>Country:</strong> Block on country field</li>
            <li><strong>Combined:</strong> Union of name token and country blocks</li>
          </ul>
        </div>

        <div className="flex gap-4 mb-6">
          <select
            value={strategy}
            onChange={(e) => setStrategy(e.target.value)}
            className="px-4 py-2 bg-gray-700 text-white rounded-md border border-gray-600"
          >
            <option value="name_token">Name Token</option>
            <option value="country">Country</option>
            <option value="combined">Combined</option>
          </select>
          <button
            onClick={generateCandidates}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <Play className="w-5 h-5 mr-2" />
            Generate Candidates
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
            <h3 className="text-lg font-semibold text-white">Blocking Statistics</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-700 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Candidate Generation</h4>
                <div className="text-gray-300 space-y-1">
                  <p>Total S1 entities: {stats.total_s1_entities.toLocaleString()}</p>
                  <p>Total S2 entities: {stats.total_s2_entities.toLocaleString()}</p>
                  <p>Total S3 entities: {stats.total_s3_entities.toLocaleString()}</p>
                  <p>Candidate pairs: {stats.candidate_pairs.toLocaleString()}</p>
                </div>
              </div>
              
              <div className="bg-gray-700 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Efficiency Metrics</h4>
                <div className="text-gray-300 space-y-1">
                  <p>Total possible pairs: {stats.total_possible_pairs.toLocaleString()}</p>
                  <p>Reduction ratio: {(stats.reduction_ratio * 100).toFixed(2)}%</p>
                  <p>Candidates per S1: {stats.candidates_per_s1.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {candidates.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Sample Candidates</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-gray-700 text-white">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left border-b border-gray-600">Source 1 ID</th>
                    <th className="px-4 py-2 text-left border-b border-gray-600">Candidate ID</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((row, idx) => (
                    <tr key={idx} className="border-b border-gray-600">
                      <td className="px-4 py-2">{row.source1_entity_id}</td>
                      <td className="px-4 py-2">{row.candidate_entity_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
