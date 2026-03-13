import { useState } from "react"
import Button from "../components/ui/Button"
import { useNavigate } from "react-router-dom"

export default function Settings() {
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadingAction, setLoadingAction] = useState<"cache" | "reset" | null>(null)
  const navigate = useNavigate()

  const callEndpoint = async (path: string, type: "cache" | "reset") => {
    setLoadingAction(type)
    setMessage(null)
    setError(null)
    try {
      const res = await fetch(`http://localhost:8000${path}`, {
        method: "POST"
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(data.detail || data.error || "Unknown error")
      }
      setMessage(data.message || "Operation completed successfully.")
      if (type === "reset") {
        alert("System Reset Successful")
        // după reset, facem reload complet pentru a forța recitirea datelor (projects.json gol etc.)
        window.location.href = "/"
      }
    } catch (e: any) {
      setError(e.message || "Request failed.")
    } finally {
      setLoadingAction(null)
    }
  }

  const handleClearCache = async () => {
    const ok = window.confirm("Ești sigur că vrei să ștergi vector cache-ul?")
    if (!ok) return
    await callEndpoint("/api/system/clear-cache", "cache")
  }

  const handleResetApp = async () => {
    const first = window.confirm(
      "Atenție! Această acțiune va șterge toate datele indexate. Continui?"
    )
    if (!first) return
    const second = window.confirm(
      "Ești ABSOLUT sigur? Această acțiune nu poate fi anulată."
    )
    if (!second) return
    console.log("🚀 System reset triggered")
    await callEndpoint("/api/system/reset-app", "reset")
  }

  return (
    <div className="h-full w-full">
      <div className="max-w-3xl mx-auto h-full flex flex-col gap-8">
        <header className="mt-2">
          <h1 className="text-2xl font-semibold text-white tracking-tight">Settings</h1>
          <p className="mt-1 text-sm text-slate-400">
            System configuration and maintenance tools.
          </p>
        </header>

        <section className="mt-4">
          <div className="rounded-2xl border border-red-900/60 bg-red-950/20 p-5">
            <h2 className="text-sm font-semibold text-red-400 uppercase tracking-[0.2em] mb-3">
              Danger Zone
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              These actions are destructive and should be used with caution. They are meant for
              troubleshooting or starting over from a clean state.
            </p>

            <div className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-100">
                    Clear Vector Cache
                  </p>
                  <p className="text-xs text-slate-400">
                    Deletes the ChromaDB cache. Indexed repositories will be re-embedded on
                    next use.
                  </p>
                </div>
                <Button
                  className="border border-red-500/70 text-red-400 bg-transparent hover:bg-red-600/20 px-4 py-2 text-xs font-semibold rounded-full"
                  onClick={handleClearCache}
                  disabled={loadingAction !== null}
                >
                  {loadingAction === "cache" ? "Clearing..." : "Clear Vector Cache"}
                </Button>
              </div>

              <div className="h-px bg-red-900/40 my-2" />

              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-red-400">
                    Reset Application Data
                  </p>
                  <p className="text-xs text-slate-400">
                    Removes all indexed repositories, vector cache, and storage files. This
                    cannot be undone.
                  </p>
                </div>
                <Button
                  className="bg-red-600 hover:bg-red-500 px-4 py-2 text-xs font-semibold rounded-full"
                  onClick={handleResetApp}
                  disabled={loadingAction !== null}
                >
                  {loadingAction === "reset" ? "Resetting..." : "Reset App Data"}
                </Button>
              </div>
            </div>

            {(message || error) && (
              <div className="mt-4 text-xs">
                {message && <p className="text-emerald-400">{message}</p>}
                {error && <p className="text-red-400">{error}</p>}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

