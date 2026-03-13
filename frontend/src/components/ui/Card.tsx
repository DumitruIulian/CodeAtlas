type Props = {
  children: React.ReactNode
  className?: string
}

export default function Card({ children, className }: Props) {
  return (
    <div
      className={`
        bg-[#111827]
        border border-gray-800
        rounded-xl
        p-6
        shadow-lg
        ${className ?? ""}
      `}
    >
      {children}
    </div>
  )
}