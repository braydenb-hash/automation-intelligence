import type { WorkflowStep } from '../../types/workflow'

interface MiniPipelineProps {
  steps: WorkflowStep[]
}

export default function MiniPipeline({ steps }: MiniPipelineProps) {
  if (steps.length === 0) return null

  const displayed = steps.slice(0, 6)
  const hasMore = steps.length > 6

  return (
    <div className="flex items-center gap-0.5">
      {displayed.map((step, i) => (
        <div key={i} className="flex items-center">
          <div
            className="h-2 w-2 rounded-full bg-ember/60"
            title={`${step.step}. ${step.tool}: ${step.action}`}
          />
          {i < displayed.length - 1 && (
            <div className="h-px w-3 bg-border" />
          )}
        </div>
      ))}
      {hasMore && (
        <>
          <div className="h-px w-3 bg-border" />
          <span className="text-[10px] text-cream-dim">+{steps.length - 6}</span>
        </>
      )}
    </div>
  )
}
