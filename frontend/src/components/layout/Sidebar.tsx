import { Home, LayoutDashboard, PlusCircle, Settings, Menu } from "lucide-react"
import { Link, useLocation } from "react-router-dom"

type SidebarProps = {
  isCollapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  const location = useLocation()

  const isHome = location.pathname === "/"
  const isDashboard = location.pathname.startsWith("/dashboard")
  const isIndexNew = location.pathname.startsWith("/index-new")

  return (
    <div
      className={`
        h-screen bg-[#0B1120] border-r border-gray-800
        flex flex-col
        transition-all duration-300 ease-in-out
        ${isCollapsed ? "w-16" : "w-64"}
      `}
    >
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        {!isCollapsed && (
          <h1 className="text-xl font-bold text-white">
            CodeAtlas
          </h1>
        )}
        <button
          onClick={onToggle}
          className="text-gray-300 hover:text-white p-1 rounded-md hover:bg-gray-800 transition"
        >
          <Menu size={20} />
        </button>
      </div>

      <div className="flex-1 p-4">
        <nav className="space-y-4 text-gray-300">
          <Link
            to="/"
            className={`flex items-center gap-3 hover:text-white cursor-pointer ${
              isHome ? "text-white" : ""
            }`}
          >
            <Home size={18} />
            {!isCollapsed && <span>Home</span>}
          </Link>

          <Link
            to="/dashboard"
            className={`flex items-center gap-3 hover:text-white cursor-pointer ${
              isDashboard ? "text-white" : ""
            }`}
          >
            <LayoutDashboard size={18} />
            {!isCollapsed && <span>Dashboard</span>}
          </Link>

          <Link
            to="/index-new"
            className={`flex items-center gap-3 hover:text-white cursor-pointer ${
              isIndexNew ? "text-white" : ""
            }`}
          >
            <PlusCircle size={18} />
            {!isCollapsed && <span>New Analysis</span>}
          </Link>

          <div className="flex items-center gap-3 hover:text-white cursor-pointer">
            <Settings size={18} />
            {!isCollapsed && <span>Settings</span>}
          </div>
        </nav>

        {!isCollapsed && (
          <div className="mt-8 space-y-3 text-sm text-gray-400">
            <p className="font-semibold text-gray-300">Recent Chats</p>
            <div className="space-y-2">
              <div className="truncate hover:text-white cursor-pointer">
                Refactor authentication module
              </div>
              <div className="truncate hover:text-white cursor-pointer">
                Explore payment service
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}