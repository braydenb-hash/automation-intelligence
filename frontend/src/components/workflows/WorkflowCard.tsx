import { Link } from 'react-router-dom'
import type { Workflow } from '../../types/workflow'
import ToolBadge from '../tools/ToolBadge'
import MiniPipeline from '../pipeline/MiniPipeline'

interface WorkflowCardProps {
  workflow: Workflow
}

function extractVideoId(url: string): string | null {
  try {
    const u = new URL(url)
    return u.searchParams.get('v')
  } catch {
    return null
  }
}

function Thumbnail({ url }: { url: string }) {
  const videoId = extractVideoId(url)
  if (!videoId) return null

  return (
    <div className="relative aspect-video w-full overflow-hidden rounded-lg bg-surface-light">
      <img
        src={`https://i.ytimg.com/vi/${videoId}/maxresdefault.jpg`}
        alt=""
        className="h-full w-full object-cover"
        onError={(e) => {
          const img = e.currentTarget
          if (!img.dataset.fallback) {
            img.dataset.fallback = '1'
            img.src = `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`
          }
        }}
      />
    </div>
  )
}

function levelColor(level: string): string {
  switch (level) {
    case 'beginner': return 'text-green-400 bg-green-400/10'
    case 'intermediate': return 'text-amber bg-amber/10'
    case 'advanced': return 'text-ember bg-ember/10'
    default: return 'text-cream-dim bg-surface-light'
  }
}

export default function WorkflowCard({ workflow }: WorkflowCardProps) {
  const overview = workflow.overview.length > 140
    ? workflow.overview.slice(0, 140).trimEnd() + '…'
    : workflow.overview

  return (
    <Link
      to={`/workflows/${workflow.slug}`}
      className="group flex flex-col rounded-xl border border-border bg-surface p-0 transition-all hover:border-ember/30 hover:bg-surface-light"
    >
      <Thumbnail url={workflow.source_url} />

      <div className="flex flex-1 flex-col gap-3 p-5">
        <div>
          <h3 className="font-sans text-base font-semibold text-cream leading-snug group-hover:text-ember transition-colors">
            {workflow.source_title}
          </h3>
          <p className="mt-1.5 text-sm text-cream-dim leading-relaxed">
            {overview}
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {workflow.tools.slice(0, 5).map((tool) => (
            <ToolBadge key={tool} name={tool} />
          ))}
          {workflow.tools.length > 5 && (
            <span className="inline-flex items-center rounded-full bg-surface-light px-2.5 py-0.5 text-xs font-mono text-cream-dim">
              +{workflow.tools.length - 5}
            </span>
          )}
        </div>

        <MiniPipeline steps={workflow.workflow_steps} />

        <div className="mt-auto flex items-center gap-3 pt-1">
          {workflow.use_case && (
            <span className="rounded-md bg-surface-light px-2 py-0.5 text-xs text-cream-dim">
              {workflow.use_case}
            </span>
          )}
          {workflow.skill_level && (
            <span className={`rounded-md px-2 py-0.5 text-xs font-medium ${levelColor(workflow.skill_level)}`}>
              {workflow.skill_level}
            </span>
          )}
          {workflow.value_score > 0 && (
            <span className="ml-auto font-mono text-xs text-amber" title="Value score">
              {workflow.value_score}/10
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
