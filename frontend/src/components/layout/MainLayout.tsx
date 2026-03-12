import Sidebar from "./Sidebar"
import Header from "./Header"

type Props = {
  children: React.ReactNode
}

export default function MainLayout({ children }: Props) {
  return (
    <div className="flex bg-[#020617] min-h-screen">

      <Sidebar />

      <div className="flex-1 flex flex-col">
        <Header />

        <div className="p-8">
          {children}
        </div>

      </div>

    </div>
  )
}