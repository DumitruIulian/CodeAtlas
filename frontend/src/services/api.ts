export async function analyzeRepo(url: string, question: string) {

  const res = await fetch("http://localhost:8000/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ url, question })
  })

  return res.json()
}