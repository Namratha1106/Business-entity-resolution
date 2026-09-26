import { useState } from 'react'
import { Search, Database } from 'lucide-react'

export default function DataExplorer() {
  const [source, setSource] = useState('source1')
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/dataset/sample/${source}?n=20`)
      const result = await response.json()
      setData(result)
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Data Explorer</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="flex gap-4 mb-6">
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="px-4 py-2 bg-gray-700 text-white rounded-md border border-gray-600"
          >
            <option value="source1">Source 1</option>
            <option value="source2">Source 2</option>
            <option value="source3">Source 3</option>
            <option value="ground_truth">Ground Truth</option>
          </select>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <Search className="w-5 h-5 mr-2" />
            Load Sample
          </button>
        </div>

        {data.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-gray-700 text-white">
              <thead>
                <tr>
                  {Object.keys(data[0]).map((key) => (
                    <th key={key} className="px-4 py-2 text-left border-b border-gray-600">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((row, idx) => (
                  <tr key={idx} className="border-b border-gray-600">
                    {Object.values(row).map((value, cellIdx) => (
                      <td key={cellIdx} className="px-4 py-2">
                        {typeof value === 'string' && value.length > 50
                          ? value.substring(0, 50) + '...'
                          : String(value)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
