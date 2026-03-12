type Props = {
  placeholder?: string
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  disabled?: boolean // <--- Adaugă asta
}

export default function Input({ placeholder, value, onChange, disabled }: Props) {
  return (
    <input
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled} // <--- Adaugă asta
      className="
        w-full
        bg-[#0B1120]
        border border-gray-700
        rounded-lg
        p-3
        text-gray-200
        disabled:opacity-50
      "
    />
  )
}