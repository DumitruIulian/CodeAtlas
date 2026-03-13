import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Github, GitBranch, Activity, Database, Clock } from "lucide-react"
import Card from "../components/ui/Card"
import Button from "../components/ui/Button"

type Project = {
  url: string
  name: string
  languages: string[]
  chunks: number
  last_indexed_at: string
  health_status?: string
}

type Stats = {
  total_repos: number
  total_chunks: number
  storage_bytes: number
  api_calls: number
}

const recentQuestions = [
  { question: "Cum funcționează autentificarea în acest monorepo?", timeAgo: "2h ago" },
  { question: "Arată-mi toate rutele critice de checkout.", timeAgo: "5h ago" },
  { question: "Unde este implementat caching-ul pentru API?", timeAgo: "11h ago" },
  { question: "Ce module frontend folosesc Zustand?", timeAgo: "1d ago" },
  { question: "Care sunt dependențele dintre payment și notifications?", timeAgo: "2d ago" }
]

function formatDate(date: Date) {
  return date.toLocaleDateString("ro-RO", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric"
  })
}

function formatBytes(bytes: number): string {
  if (!bytes || bytes <= 0) return "0 B"
  const units = ["B", "KB", "MB", "GB", "TB"]
  let idx = 0
  let value = bytes
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024
    idx++
  }
  return `${value.toFixed(1)} ${units[idx]}`
}

export default function Dashboard() {
  const today = new Date()
  const navigate = useNavigate()

  const [projects, setProjects] = useState<Project[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState<string | null>(null)

  async function loadProjectsAndStats() {
    const projectsRes = await fetch("http://localhost:8000/api/projects")
    const statsRes = await fetch("http://localhost:8000/api/stats")
    if (!projectsRes.ok) throw new Error("Nu am putut încărca lista de proiecte.")
    if (!statsRes.ok) throw new Error("Nu am putut încărca statisticile.")
    const projectsJson = await projectsRes.json()
    const statsJson = await statsRes.json()
    return { projects: projectsJson.projects ?? [], stats: statsJson as Stats }
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setIsLoading(true)
        setIsError(null)
        const { projects, stats: s } = await loadProjectsAndStats()
        if (!cancelled) {
          setProjects(projects)
          setStats(s)
        }
      } catch (err: any) {
        if (!cancelled) setIsError(err?.message ?? "Eroare la încărcarea datelor din Dashboard.")
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  // Reîncarcă proiectele la focus ca să vezi verdictul după audit în background sau după chat
  useEffect(() => {
    const onFocus = () => {
      loadProjectsAndStats()
        .then(({ projects, stats: s }) => {
          setProjects(projects)
          setStats(s)
        })
        .catch(() => {})
    }
    window.addEventListener("focus", onFocus)
    return () => window.removeEventListener("focus", onFocus)
  }, [])

  const mappedStats = [
    {
      label: "Total Repositories",
      value: stats ? stats.total_repos.toString() : "–",
      icon: GitBranch
    },
    {
      label: "Chunks Indexed",
      value: stats ? stats.total_chunks.toLocaleString("en-US") : "–",
      icon: Database
    },
    {
      label: "API Calls (24h)",
      value: stats ? stats.api_calls.toLocaleString("en-US") : "0",
      icon: Activity
    },
    {
      label: "Storage Usage",
      value: stats ? formatBytes(stats.storage_bytes) : "–",
      icon: Database
    }
  ]

  return (
    <div className="h-full w-full">
      <div className="max-w-6xl mx-auto h-full flex flex-col gap-8">
        {/* Header */}
        <header className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-400">Bun venit înapoi,</p>
            <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
              Iulian
            </h1>
            <p className="mt-1 text-sm text-slate-500">{formatDate(today)}</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/")}
              className="inline-flex items-center gap-2 rounded-full bg-sky-600 hover:bg-sky-500 text-xs md:text-sm font-semibold text-white px-4 py-2 shadow-lg shadow-sky-500/30 transition-transform hover:scale-[1.02]"
            >
              <span className="text-lg leading-none">＋</span>
              <span>Index New Repository</span>
            </button>
            <div className="hidden md:flex items-center gap-3 text-sm text-slate-400">
              <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400 mr-1" />
              Context engine online
            </div>
          </div>
        </header>

        {/* Stats Row */}
        <section className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {mappedStats.map((stat) => {
            const Icon = stat.icon
            return (
              <Card
                key={stat.label}
                className="bg-slate-900/50 border-slate-800/80 hover:border-sky-500/60 hover:bg-slate-900/80 transition-colors duration-200 group"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      {stat.label}
                    </p>
                    <p className="mt-2 text-2xl font-semibold text-white group-hover:text-sky-300">
                      {stat.value}
                    </p>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-sky-500/10 border border-sky-500/40 flex items-center justify-center text-sky-300 group-hover:scale-105 transition-transform">
                    <Icon size={18} />
                  </div>
                </div>
              </Card>
            )
          })}
        </section>

        {/* Main Content */}
        <main className="flex-1 min-h-0 grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left - Indexed Repositories */}
          <section className="xl:col-span-2 flex flex-col min-h-0 gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Github size={18} className="text-slate-300" />
                Indexed Repositories
              </h2>
              <span className="text-xs text-slate-500">
                {projects.length} active · actualizate recent
              </span>
            </div>

            <div className="grid md:grid-cols-2 gap-4 overflow-y-auto pr-1">
              {isLoading && (
                <div className="col-span-full flex justify-center items-center py-8 text-slate-500 text-sm">
                  <span className="h-4 w-4 rounded-full border-2 border-sky-500 border-t-transparent animate-spin mr-2" />
                  <span>Se încarcă proiectele indexate...</span>
                </div>
              )}

              {!isLoading && !projects.length && !isError && (
                <div className="col-span-full">
                  <Card className="bg-slate-900/70 border-slate-800/80 py-10 flex flex-col items-center justify-center text-center space-y-4">
                    <p className="text-lg font-semibold text-white">
                      Atlasul tău este gol.
                    </p>
                    <p className="text-sm text-slate-400 max-w-sm">
                      Începe prin a adăuga primul repository GitHub pentru a construi harta
                      arhitecturii sale.
                    </p>
                    <Button
                      className="mt-2 px-4 py-2 text-sm font-semibold rounded-full bg-sky-600 hover:bg-sky-500"
                      onClick={() => navigate("/")}
                    >
                      Începe indexarea
                    </Button>
                  </Card>
                </div>
              )}

              {isError && (
                <div className="col-span-full text-center text-sm text-red-400 py-6">
                  {isError}
                </div>
              )}

              {!isLoading &&
                projects.map((repo) => {
                  const health = repo.health_status || "Pending Audit"
                  const isReadyForAudit = health === "Ready for Audit"
                  const h = health.toLowerCase()
                  let badgeBg = "bg-slate-500/10"
                  let badgeText = "text-slate-500"
                  let badgeBorder = "border-slate-600/60"
                  if (h.includes("clean")) {
                    badgeBg = "bg-emerald-500/20"
                    badgeText = "text-emerald-400"
                    badgeBorder = "border-emerald-500/40"
                  } else if (h.includes("risk") || h.includes("bug") || h.includes("security")) {
                    badgeBg = "bg-red-500/20"
                    badgeText = "text-red-400"
                    badgeBorder = "border-red-500/40"
                  } else if (h.includes("debt") || h.includes("complexity")) {
                    badgeBg = "bg-amber-500/20"
                    badgeText = "text-amber-400"
                    badgeBorder = "border-amber-500/40"
                  } else if (isReadyForAudit) {
                    badgeBg = "bg-slate-500/10"
                    badgeText = "text-slate-500"
                    badgeBorder = "border-slate-600/60"
                  }
                  const badgeAnim = isReadyForAudit ? "animate-pulse" : ""

                  return (
                <Card
                  key={repo.url}
                  className="bg-slate-900/60 border-slate-800/80 hover:border-purple-500/60 hover:bg-slate-900/90 transition-all duration-200 group cursor-pointer"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 border border-slate-700 text-slate-200 group-hover:border-purple-500/70 group-hover:text-purple-300 transition-colors">
                        <Github size={18} />
                      </span>
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate group-hover:text-purple-200">
                        {repo.name}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Indexat ultima dată la {repo.last_indexed_at}
                      </p>

                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        {repo.languages.map((lang) => (
                          <span
                            key={lang}
                            className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-800/80 text-slate-200 border border-slate-700 group-hover:border-purple-500/60"
                          >
                            {lang}
                          </span>
                        ))}

                        <span
                          className={`
                            inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold
                            border ${badgeBorder} ${badgeBg} ${badgeText} ${badgeAnim}
                          `}
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-current" />
                          <span>{health}</span>
                        </span>
                      </div>

                      <div className="mt-4 flex justify-end">
                        <Button
                          className="px-3 py-1.5 text-xs font-semibold rounded-full bg-sky-600 hover:bg-sky-500 flex items-center gap-1"
                          onClick={() =>
                            navigate(`/chat/${encodeURIComponent(repo.name)}`)
                          }
                        >
                          <span>Open Map</span>
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
                )})}
            </div>
          </section>

          {/* Right - Recent Intelligence */}
          <section className="flex flex-col min-h-0 gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Clock size={18} className="text-slate-300" />
                Recent Intelligence
              </h2>
            </div>

            <Card className="bg-slate-900/60 border-slate-800/80 flex-1 min-h-0 flex flex-col">
              <ul className="space-y-3 overflow-y-auto pr-1">
                {recentQuestions.map((item, idx) => (
                  <li
                    key={idx}
                    className="group flex items-start gap-3 rounded-lg px-2 py-2 hover:bg-slate-900/80 transition-colors cursor-pointer"
                  >
                    <span className="mt-1 h-1.5 w-1.5 rounded-full bg-sky-400/90 group-hover:bg-sky-300 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-200 group-hover:text-white truncate">
                        {item.question}
                      </p>
                      <p className="mt-1 text-[11px] text-slate-500 flex items-center gap-1">
                        <Clock size={10} className="text-slate-500" />
                        <span>{item.timeAgo}</span>
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          </section>
        </main>
      </div>
    </div>
  )
}

