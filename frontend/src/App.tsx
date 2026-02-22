import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import Home from './pages/Home'
import Workflows from './pages/Workflows'
import Tools from './pages/Tools'
import Saved from './pages/Saved'

export default function App() {
  return (
    <BrowserRouter>
      <div className="grain flex min-h-screen">
        <Sidebar />
        <main className="ml-52 flex-1 p-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/workflows" element={<Workflows />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/saved" element={<Saved />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
