import React from 'react'

function ChartContainer({ title, subtitle, children }) {
  return (
    <div className="chart-container">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-white mb-1">{title}</h3>
        <p className="text-sm text-slate-400">{subtitle}</p>
      </div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  )
}

export default ChartContainer
