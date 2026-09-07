import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"

import AppLayout from "./layouts/AppLayout"

import Landing from "./pages/Landing"
import Dashboard from "./pages/Dashboard"
import Properties from "./pages/Properties"
import Tenants from "./pages/Tenants"
import Workers from "./pages/Workers"
import Login from "./pages/Login"
import Maintenance from "./pages/Maintenance"
import TenantSignup from "./pages/TenantSignup"
import TenantDashboard from "./pages/TenantDashboard"
import AcceptInvitation from "./pages/AcceptInvitation"
import Account from "./pages/Account"
import ResetPassword from "./pages/ResetPassword"
import ForgotPassword from "./pages/ForgotPassword"


function getUserFromToken() {
  const token = localStorage.getItem("access_token")

  if (!token) {
    return null
  }

  try {
    const payload = JSON.parse(atob(token.split(".")[1]))

    if (payload.exp && payload.exp * 1000 < Date.now()) {
      localStorage.removeItem("access_token")
      return null
    }

    return payload
  } catch {
    localStorage.removeItem("access_token")
    return null
  }
}


function StaffRoute({ children }) {
  const user = getUserFromToken()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role === "tenant") {
    return <Navigate to="/tenant-dashboard" replace />
  }

  return children
}


function TenantRoute({ children }) {
  const user = getUserFromToken()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role !== "tenant") {
    return <Navigate to="/dashboard" replace />
  }

  return children
}


function App() {
  return (
    <BrowserRouter>

      <Routes>

        {/* Public landing page */}

        <Route
          path="/"
          element={<Landing />}
        />


        {/* Public */}

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/forgot-password"
          element={<ForgotPassword />}
        />

        <Route
          path="/tenant-signup"
          element={<TenantSignup />}
        />

        <Route
          path="/accept-invitation"
          element={<AcceptInvitation />}
        />

        <Route
          path="/reset-password"
          element={<ResetPassword />}
        />


        {/* Tenant */}

        <Route
          path="/tenant-dashboard"
          element={
            <TenantRoute>
              <TenantDashboard />
            </TenantRoute>
          }
        />


        {/* Staff */}

        <Route
          element={
            <StaffRoute>
              <AppLayout />
            </StaffRoute>
          }
        >

          <Route
            path="/dashboard"
            element={<Dashboard />}
          />

          <Route
            path="/properties"
            element={<Properties />}
          />

          <Route
            path="/tenants"
            element={<Tenants />}
          />

          <Route
            path="/workers"
            element={<Workers />}
          />

          <Route
            path="/maintenance"
            element={<Maintenance />}
          />

          <Route
            path="/account"
            element={<Account />}
          />

        </Route>


        {/* Unknown route */}

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />

      </Routes>

    </BrowserRouter>
  )
}


export default App