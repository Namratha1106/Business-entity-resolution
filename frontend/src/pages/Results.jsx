import { useState } from 'react'
import { Play, Download, Database } from 'lucide-react'

export default function Results() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [message, setMessage] = useState('')

  const generatePredictions = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch('/api/results/predict', { method: 'POST' })
      const data = await response.json()
      setMessage(`Generated predictions: ${data.total_predictions.toLocaleString()} entities, ${data.matched_entities.toLocaleString()} matched, ${data.unmatched_entities.toLocaleString()} unmatched`)
      
      // Fetch sample results
      const resultsResponse = await fetch('/api/results/results?limit=50')
      const resultsData = await resultsResponse.json()
      setResults(resultsData)
    } catch (error) {
      setMessage('Error generating predictions: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchResults = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/results/results?limit=50')
      const data = await response.json()
      setResults(data)
    } catch (error) {
      setMessage('Error fetching results: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Results</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="mb-4 text-gray-300">
          <p>Generate predictions on test set using trained model and optimized threshold.</p>
          <p className="mt-2">Output files: matching_results.tsv, candidate_pairs.tsv</p>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={generatePredictions}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <Play className="w-5 h-5 mr-2" />
            Generate Predictions
          </button>
          <button
            onClick={fetchResults}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-600"
          >
            <Download className="w-5 h-5 mr-2" />
            Refresh Results
          </button>
        </div>

        {message && (
          <div className="mb-4 p-4 bg-blue-900 text-white rounded-md">
            {message}
          </div>
        )}

        {results.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Prediction Results (Sample)</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-gray-700 text-white">
                <thead>
                  <tr>
                    <th className="px-4 py-2 text-left border-b border-gray-600">Source 1 ID</th>
                    <th className="px-4 py-2 text-left border-b border-gray-600">Matched IDs</th>
                    <th className="px-4 py-2 text-left border-b border-gray-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((row, idx) => (
                    <tr key={idx} className="border-b border-gray-600">
                      <td className="px-4 py-2">{row.source1_entity_id}</td>
                      <td className="px-4 py-2">
                        {row.matched_entity_ids 
                          ? (row.matched_entity_ids.length > 50 
                              ? row.matched_entity_ids.substring(0, 50) + '...'
                              : row.matched_entity_ids)
                          : '<empty>'}
                      </td>
                      <td className="px-4 py-2">
                        {row.matched_entity_ids 
                          ? <span className="text-green-400">MATCHED</span>
                          : <span className="text-red-400">NO MATCH</span>}
                      </td>
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
