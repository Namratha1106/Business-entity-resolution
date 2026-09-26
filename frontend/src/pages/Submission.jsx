import { useState } from 'react'
import { Play, CheckCircle, XCircle, FileText } from 'lucide-react'

export default function Submission() {
  const [loading, setLoading] = useState(false)
  const [validationResult, setValidationResult] = useState(null)
  const [message, setMessage] = useState('')

  const validateSubmission = async () => {
    setLoading(true)
    setMessage('')
    setValidationResult(null)
    try {
      const response = await fetch('/api/submission/validate', { method: 'POST' })
      const data = await response.json()
      setValidationResult(data)
      if (data.valid) {
        setMessage('Submission is VALID!')
      } else {
        setMessage('Submission is INVALID. Fix the errors below.')
      }
    } catch (error) {
      setMessage('Error validating submission: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const createZip = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await fetch('/api/submission/create-zip', { method: 'POST' })
      const data = await response.json()
      setMessage(`Submission zip created: ${data.zip_path}`)
    } catch (error) {
      setMessage('Error creating zip: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Submission</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <div className="mb-4 text-gray-300">
          <p>Validate and package your submission for the Amazon ML Challenge.</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>Validates matching_results.tsv format</li>
            <li>Validates candidate_pairs.tsv format</li>
            <li>Checks all test S1 entities are present</li>
            <li>Checks for duplicate IDs and invalid prefixes</li>
            <li>Creates submission zip with code and outputs</li>
          </ul>
        </div>

        <div className="flex gap-4 mb-6">
          <button
            onClick={validateSubmission}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-600"
          >
            <FileText className="w-5 h-5 mr-2" />
            Validate Submission
          </button>
          <button
            onClick={createZip}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-600"
          >
            <Play className="w-5 h-5 mr-2" />
            Create Submission Zip
          </button>
        </div>

        {message && (
          <div className={`mb-4 p-4 rounded-md ${validationResult?.valid ? 'bg-green-900' : 'bg-red-900'} text-white`}>
            {message}
          </div>
        )}

        {validationResult && (
          <div className="mt-6 space-y-4">
            {validationResult.valid ? (
              <div className="flex items-center text-green-400">
                <CheckCircle className="w-6 h-6 mr-2" />
                <span className="text-lg font-semibold">Submission Valid</span>
              </div>
            ) : (
              <div className="flex items-center text-red-400">
                <XCircle className="w-6 h-6 mr-2" />
                <span className="text-lg font-semibold">Submission Invalid</span>
              </div>
            )}

            {validationResult.errors && validationResult.errors.length > 0 && (
              <div className="bg-red-900 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Errors:</h4>
                <ul className="list-disc list-inside text-red-200 space-y-1">
                  {validationResult.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            {validationResult.warnings && validationResult.warnings.length > 0 && (
              <div className="bg-yellow-900 p-4 rounded-md">
                <h4 className="text-white font-medium mb-2">Warnings:</h4>
                <ul className="list-disc list-inside text-yellow-200 space-y-1">
                  {validationResult.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
