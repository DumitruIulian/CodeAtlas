import { useState } from "react"
import Sidebar from "./Sidebar"
import Header from "./Header"

type Props = {
  children: React.ReactNode
}

export default function MainLayout({ children }: Props) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

  return (
    <div className="flex bg-[#020617] h-screen overflow-hidden">
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onToggle={() => setIsSidebarCollapsed((prev) => !prev)}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header />

        <div className="flex-1 min-h-0 overflow-hidden p-8">
          {children}
        </div>
      </div>
    </div>
  )
}