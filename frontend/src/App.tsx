import { Routes, Route } from 'react-router-dom'
import Shell from './components/layout/Shell'
import Home from './pages/Home'
import Workflows from './pages/Workflows'
import Tools from './pages/Tools'
import Saved from './pages/Saved'

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/tools" element={<Tools />} />
        <Route path="/saved" element={<Saved />} />
      </Routes>
    </Shell>
  )
}
