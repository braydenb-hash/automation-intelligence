import { useParams } from 'react-router-dom'

export default function WorkflowDetail() {
  const { slug } = useParams<{ slug: string }>()

  return (
    <div>
      <h1 className="font-serif text-3xl font-semibold text-cream">
        Workflow Blueprint
      </h1>
      <p className="mt-3 text-cream-dim">
        Full pipeline visualization and implementation guide for <span className="text-cream">{slug}</span>.
      </p>
    </div>
  )
}
