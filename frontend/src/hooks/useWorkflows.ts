import { useState, useEffect } from 'react'
import type { Workflow } from '../types/workflow'
import { getWorkflows } from '../api/client'

interface UseWorkflowsOptions {
  use_case?: string
  skill_level?: string
  sort?: string
}

interface UseWorkflowsResult {
  workflows: Workflow[]
  loading: boolean
  error: string | null
}

export function useWorkflows(options?: UseWorkflowsOptions): UseWorkflowsResult {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    getWorkflows(options)
      .then((data) => {
        if (!cancelled) {
          setWorkflows(data)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message)
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [options?.use_case, options?.skill_level, options?.sort])

  return { workflows, loading, error }
}
