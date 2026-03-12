type Props = {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean // <--- Adaugă asta
}

export default function Button({ children, onClick, disabled }: Props) {
  return (
    <button
      onClick={onClick}
      disabled={disabled} // <--- Adaugă asta
      className={`
        w-full
        bg-blue-600
        hover:bg-blue-500
        transition
        p-3
        rounded-lg
        font-semibold
        ${disabled ? "opacity-50 cursor-not-allowed" : ""} 
      `}
    >
      {children}
    </button>
  )
}