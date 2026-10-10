import { useState } from "react"
import { NavLink, Outlet, Navigate } from "react-router-dom"
import {
  LayoutDashboard,
  Building2,
  Wrench,
  UserRound,
  LogOut,
  Mail,
  Menu,
  X,
} from "lucide-react"

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const token = localStorage.getItem("access_token")

  if (!token) {
    return <Navigate to="/login" replace />
  }

  try {
    JSON.parse(atob(token.split(".")[1]))
  } catch {
    localStorage.removeItem("access_token")
    return <Navigate to="/login" replace />
  }

  function handleLogout() {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }

  function closeMobileMenu() {
    setMobileMenuOpen(false)
  }

  return (
    <div className={`app-shell ${mobileMenuOpen ? "mobile-menu-open" : ""}`}>
      {mobileMenuOpen && (
        <button
          type="button"
          className="mobile-sidebar-backdrop"
          aria-label="Close navigation menu"
          onClick={closeMobileMenu}
        />
      )}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">P</div>
          <span>PropertyOS</span>

          <button
            type="button"
            className="mobile-menu-close"
            aria-label="Close navigation menu"
            onClick={closeMobileMenu}
          >
            <X size={21} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end onClick={closeMobileMenu}>
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </NavLink>

          <NavLink to="/properties" onClick={closeMobileMenu}>
            <Building2 size={18} />
            <span>Properties</span>
          </NavLink>

          <NavLink to="/maintenance" onClick={closeMobileMenu}>
            <Wrench size={18} />
            <span>Maintenance</span>
          </NavLink>

          <NavLink to="/contact" onClick={closeMobileMenu}>
            <Mail size={18} />
            <span>Contact Us</span>
          </NavLink>
        </nav>

        <div className="sidebar-bottom">
          <NavLink to="/account" onClick={closeMobileMenu}>
            <UserRound size={18} />
            <span>Account</span>
          </NavLink>

          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
          >
            <LogOut size={18} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="mobile-topbar">
          <button
            type="button"
            className="mobile-menu-toggle"
            aria-label="Open navigation menu"
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu size={22} />
          </button>

          <div className="mobile-brand">
            <div className="brand-mark">P</div>
            <span>PropertyOS</span>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  )
}