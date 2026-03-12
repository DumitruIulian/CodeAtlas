import { useState } from "react"
import ConfigPanel from "../components/analysis/ConfigPanel"
import ResultPanel from "../components/analysis/ResultPanel"

export default function Home() {
  // Aici ținem rezultatul analizei
  const [analysisResult, setAnalysisResult] = useState<string>("")

  return (
    <div className="grid grid-cols-3 gap-6">
      <div className="col-span-1">
        {/* Pasăm funcția de setare către ConfigPanel */}
        <ConfigPanel onAnalysisComplete={(result: string) => setAnalysisResult(result)} />
      </div>

      <div className="col-span-2">
        {/* Pasăm rezultatul către ResultPanel pentru afișare */}
        <ResultPanel data={analysisResult} />
      </div>
    </div>
  )
}