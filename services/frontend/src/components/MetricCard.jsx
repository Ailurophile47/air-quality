import React from 'react'

function MetricCard({ title, value, subtitle, icon, colorClass = 'text-cyan-400', bgGradient = 'from-slate-800 to-slate-900' }) {
  return (
    <div className={`metric-card bg-gradient-to-br ${bgGradient}`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="metric-label">{title}</p>
          <p className={`metric-value ${colorClass}`}>{value}</p>
        </div>
        <div className={`p-3 bg-slate-700/50 rounded-lg ${colorClass}`}>{icon}</div>
      </div>
      <p className="text-xs text-slate-500 mt-2">{subtitle}</p>
    </div>
  )
}

export default MetricCard
