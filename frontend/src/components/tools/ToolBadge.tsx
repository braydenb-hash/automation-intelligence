interface ToolBadgeProps {
  name: string
}

function toolHue(name: string): number {
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  return 15 + (Math.abs(hash) % 41) // 15–55 range for warm hues
}

export default function ToolBadge({ name }: ToolBadgeProps) {
  const hue = toolHue(name)

  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium font-mono"
      style={{
        backgroundColor: `hsla(${hue}, 50%, 50%, 0.12)`,
        color: `hsl(${hue}, 60%, 70%)`,
      }}
    >
      {name}
    </span>
  )
}
