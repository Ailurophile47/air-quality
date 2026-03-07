import React from 'react'
import { Cloud, MapPin, RefreshCw } from 'lucide-react'

function Header({ city }) {
  return (
    <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border-b border-slate-800 sticky top-0 z-50 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg">
              <Cloud className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                Urban Air Quality
              </h1>
              <div className="flex items-center gap-2 text-slate-400 text-sm mt-1">
                <MapPin className="w-4 h-4" />
                <span>Intelligence Platform • {city}</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="p-3 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors group"
            title="Refresh data"
          >
            <RefreshCw className="w-5 h-5 text-slate-400 group-hover:text-cyan-400 transition-colors" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default Header
