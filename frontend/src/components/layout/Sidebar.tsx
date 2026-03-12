import { Home, History, Settings } from "lucide-react"

export default function Sidebar() {
  return (
    <div className="w-64 h-screen bg-[#0B1120] border-r border-gray-800 p-6">

      <h1 className="text-xl font-bold text-white mb-10">
        AI Navigator
      </h1>

      <nav className="space-y-4 text-gray-300">

        <div className="flex items-center gap-3 hover:text-white cursor-pointer">
          <Home size={18} />
          Dashboard
        </div>

        <div className="flex items-center gap-3 hover:text-white cursor-pointer">
          <History size={18} />
          History
        </div>

        <div className="flex items-center gap-3 hover:text-white cursor-pointer">
          <Settings size={18} />
          Settings
        </div>

      </nav>
    </div>
  )
}