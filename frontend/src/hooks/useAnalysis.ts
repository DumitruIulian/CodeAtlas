import { useState } from "react"

export function useAnalysis() {

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  return {
    loading,
    result,
    setLoading,
    setResult
  }
}