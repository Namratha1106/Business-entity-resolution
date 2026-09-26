import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'
import { RefreshCw, TrendingUp } from 'lucide-react'

export default function Evaluation() {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchMetrics()
  }, [])

  const fetchMetrics = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/evaluation/metrics')
      const data = await response.json()
      setMetrics(data)
    } catch (error) {
      console.error('Error fetching metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-white">Loading evaluation metrics...</div>
  }

  if (!metrics) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-white">Evaluation</h1>
        <div className="bg-gray-800 p-6 rounded-lg">
          <p className="text-gray-300">No metrics available. Train a model first.</p>
          <button
            onClick={fetchMetrics}
            className="mt-4 flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Refresh
          </button>
        </div>
      </div>
    )
  }

  const modelResults = Object.entries(metrics.results).map(([name, data]) => ({
    name,
    precision: data.precision,
    recall: data.recall,
    f1: data.f1,
    f05: data.f05
  }))

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Evaluation</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="flex justify-between items-center mb-6">
          <div>
            <p className="text-gray-400 text-sm">Best Model</p>
            <p className="text-2xl font-bold text-white">{metrics.best_model}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm">Best Threshold</p>
            <p className="text-2xl font-bold text-white">{metrics.best_threshold.toFixed(2)}</p>
          </div>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-600"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Refresh
          </button>
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Model Comparison (F0.5 Score)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={modelResults}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none' }} />
              <Legend />
              <Bar dataKey="f05" fill="#3B82F6" name="F0.5" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-white mb-4">All Metrics</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full bg-gray-700 text-white">
              <thead>
                <tr>
                  <th className="px-4 py-2 text-left border-b border-gray-600">Model</th>
                  <th className="px-4 py-2 text-left border-b border-gray-600">Precision</th>
                  <th className="px-4 py-2 text-left border-b border-gray-600">Recall</th>
                  <th className="px-4 py-2 text-left border-b border-gray-600">F1</th>
                  <th className="px-4 py-2 text-left border-b border-gray-600">F0.5</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics.results).map(([name, data]) => (
                  <tr key={name} className="border-b border-gray-600">
                    <td className="px-4 py-2 font-medium">{name}</td>
                    <td className="px-4 py-2">{data.precision.toFixed(4)}</td>
                    <td className="px-4 py-2">{data.recall.toFixed(4)}</td>
                    <td className="px-4 py-2">{data.f1.toFixed(4)}</td>
                    <td className="px-4 py-2 font-bold">{data.f05.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
