import Card from "../ui/Card"

type Props = {
  title: string
  content: string
}

export default function ResultCard({ title, content }: Props) {
  return (
    <Card>

      <h3 className="text-white font-semibold mb-2">
        {title}
      </h3>

      <p className="text-gray-400">
        {content}
      </p>

    </Card>
  )
}