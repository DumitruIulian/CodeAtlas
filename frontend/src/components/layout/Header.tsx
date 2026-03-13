import { Globe } from "lucide-react"

export default function Header() {
  return (
    <div className="h-16 border-b border-gray-800 flex items-center px-6">
      <div className="flex items-center gap-4" style={{ filter: "drop-shadow(0 0 10px rgba(56, 189, 248, 0.7))" }}>
        <Globe className="w-9 h-9 text-sky-400 animate-spin-slow" />
        <span className="text-2xl font-bold tracking-tight text-white">
          CodeAtlas
        </span>
      </div>
    </div>
  )
}