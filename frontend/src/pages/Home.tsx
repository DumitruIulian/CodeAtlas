import { useState } from "react"
import { useNavigate } from "react-router-dom"
import Card from "../components/ui/Card"
import Button from "../components/ui/Button"
import Input from "../components/ui/Input"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

export default function Home() {
  const navigate = useNavigate()
  const [repoUrl, setRepoUrl] = useState("")
  const [isIndexing, setIsIndexing] = useState(false)

  const extractRepoName = (url: string) => {
    try {
      const parsed = new URL(url)
      const parts = parsed.pathname.split("/").filter(Boolean)
      if (parts.length >= 2) {
        return `${parts[0]}/${parts[1]}`
      }
    } catch (_) {
      return null
    }
    return null
  }

  const handleIndexRepo = async () => {
    if (!repoUrl.trim()) {
      alert("Introdu un URL de GitHub!")
      return
    }

    setIsIndexing(true)
    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repoUrl,
          question: "Indexează acest repository pentru navigare ulterioară."
        })
      })

      if (!response.ok) throw new Error("Eroare la server")

      const data = await response.json()
      if (data.status !== "success") {
        throw new Error("Indexarea nu a fost finalizată cu succes.")
      }

      const fallbackName = extractRepoName(repoUrl) || repoUrl

      // Mic handshake cu backend-ul: așteptăm să apară proiectul în /api/projects
      async function waitForProjectByUrl(url: string, retries = 5, delayMs = 300) {
        for (let i = 0; i < retries; i++) {
          try {
            const res = await fetch("http://localhost:8000/api/projects")
            if (res.ok) {
              const json = await res.json()
              const projects = json.projects ?? []
              const match = projects.find((p: any) => p.url === url)
              if (match) {
                return match
              }
            }
          } catch {
            // ignorăm și reîncercăm
          }
          await new Promise((resolve) => setTimeout(resolve, delayMs))
        }
        return null
      }

      const project = await waitForProjectByUrl(repoUrl)
      const targetName = project?.name ?? fallbackName

      // mică întârziere suplimentară pentru a fi siguri că vector DB este stabil
      await new Promise((resolve) => setTimeout(resolve, 500))

      // după indexare, redirecționăm utilizatorul în Dashboard
      navigate("/dashboard")
    } catch (error: any) {
      console.error(error)
      alert("Eroare: " + error.message)
    } finally {
      setIsIndexing(false)
    }
  }

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      <div className="flex-1 min-h-0 grid place-items-center">
        <div className="max-w-2xl w-full space-y-8 text-center px-2">
          <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
            <span className="block">Navighează codul ca pe o hartă</span>
            <span className="block">
              cu{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
                CodeAtlas
              </span>
            </span>
          </h1>
          <p className="text-gray-400 text-lg">
            Începe prin a introduce URL-ul unui repository GitHub. Vom indexa codul și apoi
            poți explora totul printr-un chat inteligent.
          </p>

          <Card>
            <div className="relative w-full">
              <Input
                placeholder="https://github.com/user/repository"
                value={repoUrl}
                onChange={(e: any) => setRepoUrl(e.target.value)}
                disabled={isIndexing}
                className="text-base md:text-lg py-3 pr-32"
              />
              <Button
                onClick={handleIndexRepo}
                disabled={isIndexing}
                className="absolute right-2 top-1/2 -translate-y-1/2 h-11 px-5 text-base md:text-lg w-auto"
              >
                {isIndexing ? "Indexing Repository..." : "Analyze"}
              </Button>
            </div>
          </Card>
        </div>
      </div>

      {isIndexing && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/60 z-20">
          <div className="bg-[#020617] border border-gray-800 rounded-xl px-8 py-6 flex items-center gap-4 shadow-xl">
            <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <div className="text-left">
              <p className="text-white font-semibold">Indexing Repository...</p>
              <p className="text-gray-400 text-sm">
                Extragem structura codului și pregătim harta pentru navigare.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}