import { NavLink, Outlet, Navigate } from "react-router-dom"
import {
  LayoutDashboard,
  Building2,
  Users,
  Wrench,
  UserRound,
  LogOut,
} from "lucide-react"

export default function AppLayout() {
  const token = localStorage.getItem("access_token")

  if (!token) {
    return <Navigate to="/login" replace />
  }

  let user = null

  try {
    const payload = JSON.parse(atob(token.split(".")[1]))
    user = payload
  } catch {
    localStorage.removeItem("access_token")
    return <Navigate to="/login" replace />
  }

  const isTenant = user?.role === "tenant"

  if (isTenant) {
    return <Navigate to="/tenant-dashboard" replace />
  }

  function handleLogout() {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }

  return (
    <div className="app-shell">

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-mark">P</div>
          <span>PropertyOS</span>
        </div>


        <nav className="sidebar-nav">

          <NavLink to="/" end>
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </NavLink>


          <NavLink to="/properties">
            <Building2 size={18} />
            <span>Properties</span>
          </NavLink>


          <NavLink to="/tenants">
            <Users size={18} />
            <span>Tenants</span>
          </NavLink>


          <NavLink to="/workers">
            <UserRound size={18} />
            <span>Workers</span>
          </NavLink>


          <NavLink to="/maintenance">
            <Wrench size={18} />
            <span>Maintenance</span>
          </NavLink>

        </nav>


        <div className="sidebar-bottom">

          <NavLink to="/account">
            <UserRound size={18} />
            <span>Account</span>
          </NavLink>


          <button
            className="logout-button"
            onClick={handleLogout}
          >
            <LogOut size={18} />
            <span>Sign out</span>
          </button>

        </div>

      </aside>


      <main className="main-content">
        <Outlet />
      </main>

    </div>
  )
}