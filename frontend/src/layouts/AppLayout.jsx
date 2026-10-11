
import { useState } from "react"
import { NavLink, Outlet, Navigate } from "react-router-dom"
import {
  LayoutDashboard,
  MapPin,
  Search,
  UserRound,
  LogOut,
  Mail,
  Menu,
  X,
  GitCompareArrows,
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
    <div className="app-shell">
      {mobileMenuOpen && (
        <button
          type="button"
          className="mobile-sidebar-backdrop"
          aria-label="Close navigation"
          onClick={closeMobileMenu}
        />
      )}

      <aside className={`sidebar ${mobileMenuOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <GitCompareArrows size={20} />
          </div>
          <span>Matchly</span>

          <button
            type="button"
            className="mobile-menu-close"
            aria-label="Close menu"
            onClick={closeMobileMenu}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <NavLink to="/" end onClick={closeMobileMenu}>
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </NavLink>

          <NavLink to="/requests" onClick={closeMobileMenu}>
            <Search size={18} />
            <span>Service Requests</span>
          </NavLink>

          <NavLink to="/locations" onClick={closeMobileMenu}>
            <MapPin size={18} />
            <span>Locations</span>
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
            aria-label="Open navigation"
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu size={22} />
          </button>

          <div className="mobile-brand">
            <div className="brand-mark">
              <GitCompareArrows size={20} />
            </div>
            <span>Matchly</span>
          </div>
        </header>

        <Outlet />
      </main>
    </div>
  )
}
