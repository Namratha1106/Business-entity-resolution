import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Dataset from './pages/Dataset'
import DataExplorer from './pages/DataExplorer'
import Normalization from './pages/Normalization'
import Blocking from './pages/Blocking'
import Features from './pages/Features'
import ModelTraining from './pages/ModelTraining'
import Evaluation from './pages/Evaluation'
import Results from './pages/Results'
import Submission from './pages/Submission'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dataset" element={<Dataset />} />
          <Route path="/explorer" element={<DataExplorer />} />
          <Route path="/normalization" element={<Normalization />} />
          <Route path="/blocking" element={<Blocking />} />
          <Route path="/features" element={<Features />} />
          <Route path="/training" element={<ModelTraining />} />
          <Route path="/evaluation" element={<Evaluation />} />
          <Route path="/results" element={<Results />} />
          <Route path="/submission" element={<Submission />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
