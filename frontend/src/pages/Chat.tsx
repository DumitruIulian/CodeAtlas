import { useEffect, useRef, useState } from "react"
import { useParams } from "react-router-dom"
import Card from "../components/ui/Card"
import Button from "../components/ui/Button"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

type ChatMessage = {
  id: string
  role: "user" | "assistant" | "system"
  content: string
}

type Project = {
  url: string
  name: string
  languages: string[]
  chunks: number
  last_indexed_at: string
}

export default function Chat() {
  const { repoName } = useParams<{ repoName: string }>()

  const [repoUrl, setRepoUrl] = useState<string | null>(null)
  const [displayName, setDisplayName] = useState<string | null>(null)
  const [isLoadingRepo, setIsLoadingRepo] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [currentInput, setCurrentInput] = useState("")
  const [isSending, setIsSending] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const messagesContainerRef = useRef<HTMLDivElement | null>(null)
  const shouldAutoScrollRef = useRef(true)
  const typingBufferRef = useRef<string>("")
  const typingTimerRef = useRef<number | null>(null)

  useEffect(() => {
    if (!repoName) {
      setLoadError("Nu a fost specificat niciun repository în URL.")
      setIsLoadingRepo(false)
      return
    }

    let cancelled = false

    async function resolveRepo() {
      try {
        setIsLoadingRepo(true)
        setLoadError(null)

        const res = await fetch("http://localhost:8000/api/projects")
        if (!res.ok) {
          throw new Error("Nu am putut încărca lista de proiecte.")
        }

        const json = await res.json()
        const projects: Project[] = json.projects ?? []

        const decodedName = decodeURIComponent(repoName)

        // Normalizăm numele astfel încât să se potrivească cu formatul salvat în history
        const normalize = (value: string) => value.replace(/\.git$/i, "")

        let match = projects.find((p) => normalize(p.name) === normalize(decodedName))
        if (!match) {
          match = projects.find((p) => normalize(p.url) === normalize(decodedName))
        }

        if (!match) {
          throw new Error(
            `Nu am găsit niciun repository indexat cu numele \"${decodedName}\".`
          )
        }

        if (!cancelled) {
          setRepoUrl(match.url)
          setDisplayName(match.name)
          setMessages([
            {
              id: crypto.randomUUID(),
              role: "system",
              content: `Codebase for ${match.name} is indexed (last update: ${match.last_indexed_at}). Ask anything about this repository.`
            }
          ])
        }
      } catch (err: any) {
        if (!cancelled) {
          setLoadError(err.message ?? "Eroare la încărcarea repository-ului.")
        }
      } finally {
        if (!cancelled) {
          setIsLoadingRepo(false)
        }
      }
    }

    resolveRepo()

    return () => {
      cancelled = true
      if (typingTimerRef.current !== null) {
        clearInterval(typingTimerRef.current)
        typingTimerRef.current = null
      }
    }
  }, [repoName])

  useEffect(() => {
    if (shouldAutoScrollRef.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  const handleSendMessage = async () => {
    if (!currentInput.trim() || !repoUrl) return

    shouldAutoScrollRef.current = true

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: currentInput.trim()
    }

    setMessages((prev) => [...prev, userMessage])
    setCurrentInput("")
    setIsSending(true)

    try {
      const assistantId = crypto.randomUUID()
      setMessages((prev) => [
        ...prev,
        { id: assistantId, role: "assistant", content: "" }
      ])

      const response = await fetch("http://localhost:8000/analyze?stream=1", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repoUrl,
          question: userMessage.content
        })
      })

      if (!response.ok) throw new Error("Eroare la server")

      const contentType = response.headers.get("content-type") || ""
      if (contentType.includes("application/json")) {
        const data = await response.json()
        const answer = data.answer || "Nu am putut genera un răspuns."
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, content: answer } : m))
        )
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error("Stream indisponibil în răspuns.")
      }

      const decoder = new TextDecoder("utf-8")

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        if (!chunk) continue
        typingBufferRef.current += chunk

        if (typingTimerRef.current === null) {
          typingTimerRef.current = window.setInterval(() => {
            const buffer = typingBufferRef.current
            if (!buffer.length) {
              if (typingTimerRef.current !== null) {
                clearInterval(typingTimerRef.current)
                typingTimerRef.current = null
              }
              return
            }

            const toAppend = buffer.slice(0, 1)
            typingBufferRef.current = buffer.slice(1)

            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: (m.content ?? "") + toAppend } : m
              )
            )
          }, 20)
        }
      }
    } catch (error: any) {
      console.error(error)
      alert("Eroare: " + error.message)
    } finally {
      setIsSending(false)
    }
  }

  const isChatDisabled = !repoUrl || isSending || isLoadingRepo || !!loadError

  if (isLoadingRepo) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm">
        <div className="flex items-center gap-3">
          <span className="h-5 w-5 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
          <span>Se încarcă contextul pentru repository...</span>
        </div>
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="h-full flex items-center justify-center text-red-400 text-sm">
        {loadError}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="h-full min-h-0 w-full max-w-5xl mx-auto flex flex-col gap-4 overflow-hidden">
          <div className="flex items-center justify-between">
            <Card>
              <div className="flex items-center gap-3">
                <span className="inline-flex h-2 w-2 rounded-full bg-green-400" />
                <div className="text-sm text-gray-300">
                  <p className="font-semibold">Repository indexed</p>
                  <p className="text-xs text-gray-400">
                    {displayName ?? repoUrl}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          <div className="flex-1 min-h-0 overflow-hidden">
            <Card className="h-full min-h-0 flex flex-col overflow-hidden">
              <div
                ref={messagesContainerRef}
                className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden space-y-4 px-1 py-1 pb-4"
                onScroll={() => {
                  const el = messagesContainerRef.current
                  if (!el) return
                  const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
                  shouldAutoScrollRef.current = distanceFromBottom < 120
                }}
              >
                {messages.map((msg) => {
                  const isUser = msg.role === "user"
                  const isAssistant = msg.role === "assistant"

                  return (
                    <div
                      key={msg.id}
                      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`flex items-end gap-2 max-w-[85%] ${
                          isUser ? "flex-row-reverse ml-auto" : "flex-row"
                        }`}
                      >
                        {isAssistant && (
                          <div className="shrink-0 w-7 h-7 rounded-full bg-gradient-to-br from-blue-500/60 to-purple-500/60 border border-white/10 flex items-center justify-center text-[11px] text-white/90">
                            AI
                          </div>
                        )}

                        <div
                          className={`
                            min-w-0 px-4 py-3 text-sm md:text-base animate-fadeIn
                            ${
                              isUser
                                ? "bg-blue-800/70 text-white rounded-3xl rounded-br-md border border-blue-500/10"
                                : isAssistant
                                ? "bg-gray-900 text-gray-100 rounded-3xl rounded-bl-md border border-gray-700"
                                : "bg-gray-800 text-gray-200 italic rounded-3xl rounded-bl-md"
                            }
                          `}
                        >
                          {isAssistant ? (
                            <div className="prose prose-invert max-w-none">
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  code({ inline, className, children, ...props }: any) {
                                    if (inline) {
                                      return (
                                        <code
                                          className="bg-gray-800 px-1 py-0.5 rounded text-blue-300 text-[0.9em]"
                                          {...props}
                                        >
                                          {children}
                                        </code>
                                      )
                                    }

                                    return (
                                      <pre className="bg-[#020617] p-3 rounded-lg border border-gray-700 overflow-x-auto text-xs md:text-sm">
                                        <code {...props}>{children}</code>
                                      </pre>
                                    )
                                  },
                                  pre({ children, ...props }: any) {
                                    return (
                                      <pre
                                        className="bg-[#020617] p-3 rounded-lg border border-gray-700 overflow-x-auto text-xs md:text-sm"
                                        {...props}
                                      >
                                        {children}
                                      </pre>
                                    )
                                  }
                                }}
                              >
                                {msg.content}
                              </ReactMarkdown>
                              {isSending && msg.content === "" && (
                                <span className="inline-block ml-1 text-gray-400 animate-pulse">
                                  ▍
                                </span>
                              )}
                            </div>
                          ) : (
                            <span>{msg.content}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}

                {messages.length === 0 && (
                  <div className="h-full flex items-center justify-center text-gray-500 text-sm italic">
                    Aștept întrebarea ta despre acest repository...
                  </div>
                )}

                {isSending && (
                  <div className="flex justify-start">
                    <div className="bg-gray-900 text-gray-300 px-4 py-2 rounded-3xl rounded-bl-md border border-gray-700 inline-flex items-center gap-2 text-xs">
                      <span className="inline-flex h-2 w-2 rounded-full bg-green-400 animate-pulse" />
                      <span>AI is thinking...</span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              <div className="pt-3 border-t border-gray-800 mt-2">
                <div className="w-full min-w-0 flex items-center gap-2 bg-[#020617] border border-gray-700 rounded-2xl px-2 py-2 overflow-x-hidden">
                  <textarea
                    placeholder={
                      isChatDisabled
                        ? "Așteaptă pregătirea contextului..."
                        : "Întreabă orice despre cod..."
                    }
                    value={currentInput}
                    onChange={(e) => {
                      setCurrentInput(e.target.value)
                      e.currentTarget.style.height = "auto"
                      e.currentTarget.style.height = `${e.currentTarget.scrollHeight}px`
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault()
                        if (!isChatDisabled && currentInput.trim()) {
                          handleSendMessage()
                        }
                      }
                    }}
                    disabled={isChatDisabled}
                    className="flex-1 min-w-0 bg-transparent px-2 py-2 text-gray-200 min-h-[44px] max-h-[160px] outline-none focus:outline-none transition resize-none leading-6 overflow-x-hidden"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={isChatDisabled || !currentInput.trim()}
                    className="h-10 px-4 flex items-center justify-center shrink-0 w-auto"
                  >
                    {isSending ? "Trimit..." : "Trimite"}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

