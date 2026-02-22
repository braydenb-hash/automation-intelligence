import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import GrainOverlay from '../common/GrainOverlay'

interface ShellProps {
  children: ReactNode
}

export default function Shell({ children }: ShellProps) {
  return (
    <div className="min-h-screen bg-midnight">
      <GrainOverlay />
      <Sidebar />
      <main className="ml-52 min-h-screen p-8">
        <div className="mx-auto max-w-6xl">
          {children}
        </div>
      </main>
    </div>
  )
}
