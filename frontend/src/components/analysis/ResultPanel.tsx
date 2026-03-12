import Card from "../ui/Card"
import ReactMarkdown from "react-markdown"

interface ResultPanelProps {
  data: string
}

export default function ResultPanel({ data }: ResultPanelProps) {
  return (
    <Card>
      <div className="flex items-center justify-between mb-4 border-b border-gray-800 pb-2">
        <h2 className="text-lg font-semibold text-white">Analiză Detaliată</h2>
        {data && <span className="text-xs text-blue-400">Sursă: Llama 3 + RAG</span>}
      </div>

      <div className="min-h-[450px] prose prose-invert max-w-none">
        {data ? (
          <div className="text-gray-300 text-sm md:text-base leading-relaxed">
            {/* Aceasta este magia care stilizează textul */}
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  return (
                    <code className="bg-gray-800 p-1 rounded text-blue-300" {...props}>
                      {children}
                    </code>
                  )
                },
                pre({ node, children, ...props }: any) {
                  return (
                    <pre className="bg-[#020617] p-4 rounded-lg border border-gray-700 overflow-x-auto" {...props}>
                      {children}
                    </pre>
                  )
                }
              }}
            >
              {data}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-[350px] text-gray-500 italic">
            <p>Aștept configurarea proiectului...</p>
          </div>
        )}
      </div>
    </Card>
  )
}