import { useParams, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import type { WorkflowDetail as WorkflowDetailType } from '../types/workflow'
import { getWorkflow } from '../api/client'
import ToolBadge from '../components/tools/ToolBadge'

export default function WorkflowDetail() {
  const { slug } = useParams<{ slug: string }>()
  const [workflow, setWorkflow] = useState<WorkflowDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!slug) return
    let cancelled = false
    setLoading(true)

    getWorkflow(slug)
      .then((data) => {
        if (!cancelled) {
          setWorkflow(data)
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
  }, [slug])

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-48 animate-pulse rounded bg-surface-light" />
        <div className="h-4 w-96 animate-pulse rounded bg-surface-light" />
        <div className="h-64 w-full animate-pulse rounded-xl bg-surface-light" />
      </div>
    )
  }

  if (error || !workflow) {
    return (
      <div>
        <Link to="/workflows" className="text-sm text-ember hover:underline">
          &larr; Back to workflows
        </Link>
        <div className="mt-6 rounded-lg border border-rust/30 bg-rust/10 px-4 py-3 text-sm text-ember">
          {error || 'Workflow not found'}
        </div>
      </div>
    )
  }

  return (
    <div>
      <Link to="/workflows" className="text-sm text-ember hover:underline">
        &larr; Back to workflows
      </Link>

      <div className="mt-6">
        <h1 className="font-serif text-3xl font-semibold text-cream">
          {workflow.source_title}
        </h1>

        <p className="mt-3 text-cream-dim leading-relaxed">
          {workflow.overview}
        </p>

        <div className="mt-4 flex flex-wrap gap-2">
          {workflow.tools.map((tool) => (
            <ToolBadge key={tool} name={tool} />
          ))}
        </div>

        <div className="mt-4 flex items-center gap-4 text-sm text-cream-dim">
          {workflow.use_case && <span>{workflow.use_case}</span>}
          {workflow.skill_level && (
            <span className="capitalize">{workflow.skill_level}</span>
          )}
          {workflow.value_score > 0 && (
            <span className="font-mono text-amber">{workflow.value_score}/10</span>
          )}
          {workflow.channel_name && <span>via {workflow.channel_name}</span>}
        </div>

        {/* Placeholder for Phase 3 pipeline visualization */}
        <div className="mt-8 rounded-xl border border-border bg-surface p-8 text-center">
          <p className="text-cream-dim">
            Pipeline visualization — coming in Phase 3
          </p>
          <p className="mt-2 text-sm text-cream-dim/60">
            {workflow.workflow_steps.length} steps &middot;{' '}
            {workflow.tools.length} tools
          </p>
        </div>
      </div>
    </div>
  )
}
