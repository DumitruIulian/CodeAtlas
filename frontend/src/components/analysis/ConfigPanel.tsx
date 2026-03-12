import { useState } from "react"
import Card from "../ui/Card"
import Input from "../ui/Input"
import Button from "../ui/Button"

interface ConfigPanelProps {
  onAnalysisComplete: (result: string) => void
}

export default function ConfigPanel({ onAnalysisComplete }: ConfigPanelProps) {
  const [repoUrl, setRepoUrl] = useState("")
  const [question, setQuestion] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) return alert("Introdu un URL de GitHub!")
    
    setIsLoading(true)
    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repoUrl: repoUrl,
          question: question || "Analizează acest cod."
        }),
      })

      if (!response.ok) throw new Error("Eroare la server")

      const data = await response.json()
      // Trimitem răspunsul către părintele Home.tsx
      onAnalysisComplete(data.answer) 
      
    } catch (error: any) {
      console.error(error)
      alert("Eroare: " + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card>
      <h2 className="text-lg font-semibold text-white mb-4">Configurare</h2>
      
      <div className="space-y-4">
        <Input 
          placeholder="GitHub repository URL" 
          value={repoUrl}
          onChange={(e: any) => setRepoUrl(e.target.value)} 
          disabled={isLoading}
        />

        <textarea
          placeholder="Întrebarea ta despre cod..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={isLoading}
          className="w-full bg-[#0B1120] border border-gray-700 rounded-lg p-3 text-gray-200 min-h-[120px] outline-none focus:border-blue-500 transition"
        />

        <Button onClick={handleAnalyze} disabled={isLoading}>
          {isLoading ? "Se analizează..." : "Analizează Codul"}
        </Button>
      </div>
    </Card>
  )
}