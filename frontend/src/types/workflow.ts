export interface WorkflowStep {
  step: number
  action: string
  tool: string
  details: string
}

export interface Workflow {
  slug: string
  source_url: string
  source_title: string
  channel_name: string
  published: string
  use_case: string
  skill_level: string
  overview: string
  cost_estimate: string
  complexity: string
  value_score: number
  doc_path: string
  processed_at: string
  tools: string[]
  workflow_steps: WorkflowStep[]
  when_to_use: string[]
  when_not_to_use: string[]
  alternatives: string[]
  pattern_tags: string[]
}

export interface WorkflowDetail extends Workflow {
  html_content: string
}

export interface Stats {
  total_workflows: number
  by_level: Record<string, number>
  by_use_case: Record<string, number>
  high_value_count: number
  last_scan: string | null
  videos_processed: number
}
