import type { Workflow, WorkflowDetail, Stats } from '../types/workflow'

const BASE = '/api'

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function getWorkflows(params?: {
  use_case?: string
  skill_level?: string
  sort?: string
}): Promise<Workflow[]> {
  const query = new URLSearchParams()
  if (params?.use_case) query.set('use_case', params.use_case)
  if (params?.skill_level) query.set('skill_level', params.skill_level)
  if (params?.sort) query.set('sort', params.sort)
  const qs = query.toString()
  return fetchJSON<Workflow[]>(`${BASE}/workflows${qs ? `?${qs}` : ''}`)
}

export async function getWorkflow(slug: string): Promise<WorkflowDetail> {
  return fetchJSON<WorkflowDetail>(`${BASE}/workflows/${slug}`)
}

export async function getStats(): Promise<Stats> {
  return fetchJSON<Stats>(`${BASE}/stats`)
}
