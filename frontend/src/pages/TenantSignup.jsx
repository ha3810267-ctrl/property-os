import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { apiRequest } from "../services/api"

export default function TenantSignup() {
  const navigate = useNavigate()

  const [tenantId, setTenantId] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()

    setError("")

    if (!tenantId.trim()) {
      setError("Tenant ID is required")
      return
    }

    if (!email.trim()) {
      setError("Email is required")
      return
    }

    if (!password) {
      setError("Password is required")
      return
    }

    setLoading(true)

    try {
      const data = await apiRequest("/tenant-signup", {
        method: "POST",
        body: JSON.stringify({
          tenant_id: Number(tenantId),
          email: email.trim(),
          password,
        }),
      })

      if (!data.access_token) {
        throw new Error(
          "Account created but no access token was returned"
        )
      }

      localStorage.setItem(
        "access_token",
        data.access_token
      )

      navigate("/tenant-dashboard")
    } catch (err) {
      setError(
        err.message || "Could not create your tenant account"
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="brand">
          <div className="brand-mark">P</div>
          <span>PropertyOS</span>
        </div>

        <div className="login-header">
          <p className="eyebrow">Tenant portal</p>

          <h1>Create your account</h1>

          <p>
            Set up your tenant account to access your property
            dashboard
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <label>
            Tenant ID

            <input
              type="number"
              value={tenantId}
              onChange={(event) => {
                setTenantId(event.target.value)
                setError("")
              }}
              placeholder="Enter your tenant ID"
              disabled={loading}
              required
            />
          </label>

          <label>
            Email

            <input
              type="email"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value)
                setError("")
              }}
              placeholder="you@example.com"
              autoComplete="email"
              disabled={loading}
              required
            />
          </label>

          <label>
            Password

            <input
              type="password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value)
                setError("")
              }}
              placeholder="Create a password"
              autoComplete="new-password"
              disabled={loading}
              required
            />
          </label>

          {error && (
            <p className="form-error">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="primary-button login-button"
            disabled={loading}
          >
            {loading
              ? "Creating account..."
              : "Create tenant account"}
          </button>
        </form>

        <div
          style={{
            marginTop: "20px",
            textAlign: "center",
          }}
        >
          <p>
            Already have an account?{" "}
            <button
              type="button"
              className="secondary-button"
              onClick={() => navigate("/login")}
              disabled={loading}
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}