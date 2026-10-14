function starPoints(cx, cy, r) {
  return Array.from({ length: 10 }, (_, i) => {
    const a = -Math.PI / 2 + (i * Math.PI) / 5
    const rr = i % 2 === 0 ? r : r * 0.45
    return `${(cx + rr * Math.cos(a)).toFixed(1)},${(cy + rr * Math.sin(a)).toFixed(1)}`
  }).join(' ')
}

// Shape = outcome, color = team, size = xG. Shape is never color-only.
export default function Marker({ cx, cy, outcome, xg, color, ring = '#ffffff', size }) {
  const r = size ?? (xg === null || xg === undefined ? 9 : 7 + Math.sqrt(xg) * 20)
  const common = { stroke: ring, strokeWidth: 2, strokeLinejoin: 'round' }
  const opacity = xg === null || xg === undefined ? 0.6 : 1
  switch (outcome) {
    case 'goal':
      return <polygon points={starPoints(cx, cy, r * 1.25)} fill={color} opacity={opacity} {...common} />
    case 'blocked':
      return <rect x={cx - r} y={cy - r} width={2 * r} height={2 * r} rx="2" fill={color} opacity={opacity} {...common} />
    case 'off_target':
      return <circle cx={cx} cy={cy} r={r} fill="#ffffff" stroke={color} strokeWidth="2.5" />
    case 'post':
      return <polygon points={`${cx},${cy - r * 1.2} ${cx + r * 1.1},${cy + r * 0.9} ${cx - r * 1.1},${cy + r * 0.9}`} fill={color} opacity={opacity} {...common} />
    default: // saved
      return <circle cx={cx} cy={cy} r={r} fill={color} opacity={opacity} {...common} />
  }
}
