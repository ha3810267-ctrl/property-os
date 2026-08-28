import { useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { apiRequest } from "../services/api"

export default function ResetPassword() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const token = searchParams.get("token")

  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()

    setError("")
    setSuccess("")

    if (!token) {
      setError("This password reset link is invalid")
      return
    }

    if (!newPassword) {
      setError("Please enter a new password")
      return
    }

    if (!confirmPassword) {
      setError("Please confirm your new password")
      return
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match")
      return
    }

    try {
      setLoading(true)

      const data = await apiRequest("/reset-password", {
        method: "POST",
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
      })

      setSuccess(
        data?.message ||
        "Password reset successfully"
      )

      setNewPassword("")
      setConfirmPassword("")

    } catch (error) {
      console.error(error)

      setError(
        error.message ||
        "Unable to reset password"
      )

    } finally {
      setLoading(false)
    }
  }

  function goToLogin() {
    navigate("/login")
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
            Reset your password
          </h1>

          <p>
            Choose a new password for your PropertyOS account
          </p>
        </div>

        {!success ? (
          <form onSubmit={handleSubmit}>

            <label>
              New password

              <input
                type="password"
                value={newPassword}
                onChange={(event) =>
                  setNewPassword(event.target.value)
                }
                placeholder="Enter your new password"
                autoComplete="new-password"
                required
                disabled={loading}
              />
            </label>

            <label>
              Confirm new password

              <input
                type="password"
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(event.target.value)
                }
                placeholder="Confirm your new password"
                autoComplete="new-password"
                required
                disabled={loading}
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
                ? "Resetting..."
                : "Reset password"}
            </button>

          </form>
        ) : (
          <div style={{ textAlign: "center" }}>

            <p>
              {success}
            </p>

            <button
              type="button"
              className="primary-button login-button"
              onClick={goToLogin}
            >
              Back to sign in
            </button>

          </div>
        )}

        {!success && (
          <div
            style={{
              marginTop: "20px",
              textAlign: "center",
            }}
          >
            <button
              type="button"
              className="secondary-button"
              onClick={goToLogin}
              disabled={loading}
            >
              Back to sign in
            </button>
          </div>
        )}

      </div>
    </div>
  )
}