type Props = {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean // <--- Adaugă asta
  className?: string
}

export default function Button({ children, onClick, disabled, className }: Props) {
  return (
    <button
      onClick={onClick}
      disabled={disabled} // <--- Adaugă asta
      className={`
        bg-blue-600
        hover:bg-blue-500
        transition
        rounded-lg
        font-semibold
        ${disabled ? "opacity-50 cursor-not-allowed" : ""} 
        ${className ?? "w-full p-3"}
      `}
    >
      {children}
    </button>
  )
}