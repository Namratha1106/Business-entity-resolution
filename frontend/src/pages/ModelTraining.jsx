import { useState } from 'react'
import { Play, Save, Brain, TrendingUp } from 'lucide-react'

export default function ModelTraining() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [message, setMessage] = useState('')

  const trainModels = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch('/api/training/train', { method: 'POST' })
      const data = await response.json()
      setMessage(`Training complete. Best model: ${data.best_model}`)
      setResults(data)
    } catch (error) {
      setMessage('Error training models: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const saveModel = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch('/api/training/save', { method: 'POST' })
      const data = await response.json()
      setMessage(data.message)
    } catch (error) {
      setMessage('Error saving model: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Model Training</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="mb-4 text-gray-300">
          <p>Models trained and compared:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li><strong>Logistic Regression:</strong> Linear model with balanced class weights</li>
            <li><strong>Random Forest:</strong> Ensemble of 100 decision trees</li>
            <li><strong>Gradient Boosting:</strong> 100 boosting iterations</li>
          </ul>
          <p className="mt-2">Best model selected by F0.5 score on validation set.</p>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={trainModels}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <Brain className="w-5 h-5 mr-2" />
            Train Models
          </button>
          <button
            onClick={saveModel}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-600"
          >
            <Save className="w-5 h-5 mr-2" />
            Save Model
          </button>
        </div>

        {message && (
          <div className="mb-4 p-4 bg-blue-900 text-white rounded-md">
            {message}
          </div>
        )}

        {results && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Training Results</h3>
            
            <div className="bg-gray-700 p-4 rounded-md">
              <p className="text-white font-medium mb-2">Best Model: {results.best_model}</p>
            </div>

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
                  {Object.entries(results.results).map(([name, metrics]) => (
                    <tr key={name} className="border-b border-gray-600">
                      <td className="px-4 py-2 font-medium">{name}</td>
                      <td className="px-4 py-2">{metrics.precision.toFixed(4)}</td>
                      <td className="px-4 py-2">{metrics.recall.toFixed(4)}</td>
                      <td className="px-4 py-2">{metrics.f1.toFixed(4)}</td>
                      <td className="px-4 py-2 font-bold">{metrics.f05.toFixed(4)}</td>
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
