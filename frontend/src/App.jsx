import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"

import AppLayout from "./layouts/AppLayout"

import Dashboard from "./pages/Dashboard"
import Login from "./pages/Login"
import Maintenance from "./pages/Maintenance"
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


function ProtectedRoute({ children }) {
  const user = getUserFromToken()

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}


function App() {
  return (
    <BrowserRouter>

      <Routes>

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
          path="/reset-password"
          element={<ResetPassword />}
        />


        {/* Authenticated */}

        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >

          <Route
            path="/"
            element={<Dashboard />}
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