import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { apiRequest } from "../services/api"

export default function ForgotPassword() {
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")

  async function handleSubmit(event) {
    event.preventDefault()

    setMessage("")
    setError("")
    setLoading(true)

    try {
      const data = await apiRequest("/forgot-password", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
        }),
      })

      setMessage(
        data?.message ||
        "If an account exists for this email, a password reset link will be sent"
      )

    } catch (error) {
      console.error(error)

      setError(
        error.message ||
        "Unable to request a password reset"
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

          <p className="eyebrow">
            Account recovery
          </p>

          <h1>
            Forgot your password?
          </h1>

          <p>
            Enter your email and we'll send you a
            link to reset your password
          </p>

        </div>


        <form onSubmit={handleSubmit}>

          <label>
            Email

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="you@example.com"
              autoComplete="email"
              required
              disabled={loading}
            />

          </label>


          {error && (
            <p className="form-error">
              {error}
            </p>
          )}


          {message && (
            <p className="success-message">
              {message}
            </p>
          )}


          <button
            type="submit"
            className="primary-button login-button"
            disabled={loading}
          >
            {loading
              ? "Sending..."
              : "Send reset link"}
          </button>

        </form>


        <div
          style={{
            marginTop: "20px",
            textAlign: "center",
          }}
        >

          <button
            type="button"
            className="secondary-button"
            onClick={() => navigate("/login")}
            disabled={loading}
          >
            Back to sign in
          </button>

        </div>

      </div>

    </div>
  )
}