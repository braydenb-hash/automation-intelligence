export default function GrainOverlay() {
  return (
    <>
      <svg className="absolute w-0 h-0 overflow-hidden">
        <defs>
          <filter id="grain">
            <feTurbulence
              type="fractalNoise"
              baseFrequency="0.75"
              numOctaves={4}
              stitchTiles="stitch"
            />
            <feColorMatrix type="saturate" values="0" />
          </filter>
        </defs>
      </svg>

      <div className="pointer-events-none fixed inset-0 z-50 opacity-[0.08] grain-filter" />
    </>
  )
}
