type Props = {
  children: React.ReactNode
}

export default function Card({ children }: Props) {
  return (
    <div className="
      bg-[#111827]
      border border-gray-800
      rounded-xl
      p-6
      shadow-lg
    ">
      {children}
    </div>
  )
}