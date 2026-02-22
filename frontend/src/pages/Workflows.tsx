import { useState, useMemo } from 'react'
import { useWorkflows } from '../hooks/useWorkflows'
import WorkflowCard from '../components/workflows/WorkflowCard'

const SORT_OPTIONS = [
  { value: 'value_score', label: 'Value Score' },
  { value: 'date', label: 'Date Added' },
  { value: 'title', label: 'Title' },
] as const

export default function Workflows() {
  const [sort, setSort] = useState('value_score')
  const [filterUseCase, setFilterUseCase] = useState('')
  const [filterLevel, setFilterLevel] = useState('')
  const [search, setSearch] = useState('')

  const { workflows, loading, error } = useWorkflows({
    sort,
    use_case: filterUseCase || undefined,
    skill_level: filterLevel || undefined,
  })

  // Derive unique values for filter dropdowns from the full dataset
  const useCases = useMemo(() => {
    const set = new Set(workflows.map((w) => w.use_case).filter(Boolean))
    return Array.from(set).sort()
  }, [workflows])

  const skillLevels = useMemo(() => {
    const set = new Set(workflows.map((w) => w.skill_level).filter(Boolean))
    return Array.from(set).sort()
  }, [workflows])

  // Client-side search filter on top of API results
  const filtered = useMemo(() => {
    if (!search.trim()) return workflows
    const q = search.toLowerCase()
    return workflows.filter(
      (w) =>
        w.source_title.toLowerCase().includes(q) ||
        w.overview.toLowerCase().includes(q) ||
        w.tools.some((t) => t.toLowerCase().includes(q))
    )
  }, [workflows, search])

  return (
    <div>
      <div className="mb-8">
        <h1 className="font-serif text-3xl font-semibold text-cream">
          Workflows
        </h1>
        <p className="mt-2 text-cream-dim">
          {loading
            ? 'Loading blueprints…'
            : `${filtered.length} workflow blueprint${filtered.length !== 1 ? 's' : ''}`}
        </p>
      </div>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <svg
            className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-cream-dim"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search workflows…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-border bg-surface py-2 pl-10 pr-4 text-sm text-cream placeholder-cream-dim/50 outline-none transition-colors focus:border-ember/40 focus:bg-surface-light"
          />
        </div>

        {/* Use case filter */}
        <select
          value={filterUseCase}
          onChange={(e) => setFilterUseCase(e.target.value)}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-cream outline-none transition-colors focus:border-ember/40"
        >
          <option value="">All use cases</option>
          {useCases.map((uc) => (
            <option key={uc} value={uc}>
              {uc}
            </option>
          ))}
        </select>

        {/* Skill level filter */}
        <select
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value)}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-cream outline-none transition-colors focus:border-ember/40"
        >
          <option value="">All levels</option>
          {skillLevels.map((sl) => (
            <option key={sl} value={sl}>
              {sl}
            </option>
          ))}
        </select>

        {/* Sort */}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-cream outline-none transition-colors focus:border-ember/40"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              Sort: {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 rounded-lg border border-rust/30 bg-rust/10 px-4 py-3 text-sm text-ember">
          Failed to load workflows: {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl border border-border bg-surface"
            >
              <div className="aspect-video w-full animate-pulse rounded-t-xl bg-surface-light" />
              <div className="space-y-3 p-5">
                <div className="h-4 w-3/4 animate-pulse rounded bg-surface-light" />
                <div className="h-3 w-full animate-pulse rounded bg-surface-light" />
                <div className="h-3 w-1/2 animate-pulse rounded bg-surface-light" />
                <div className="flex gap-2">
                  <div className="h-5 w-16 animate-pulse rounded-full bg-surface-light" />
                  <div className="h-5 w-14 animate-pulse rounded-full bg-surface-light" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Results grid */}
      {!loading && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((workflow) => (
            <WorkflowCard key={workflow.slug} workflow={workflow} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <p className="text-lg text-cream-dim">No workflows found</p>
          {search && (
            <p className="mt-2 text-sm text-cream-dim/60">
              Try adjusting your search or filters
            </p>
          )}
        </div>
      )}
    </div>
  )
}
