import { useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import { CheckCircle2, LockKeyhole, UserRound } from "lucide-react"
import { apiRequest } from "../services/api"

export default function AcceptInvitation() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const token = searchParams.get("token")

  const [name, setName] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError("")

    if (!token) {
      setError("This invitation link is invalid.")
      return
    }

    if (!name.trim()) {
      setError("Please enter your name.")
      return
    }

    if (!password) {
      setError("Please enter a password.")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.")
      return
    }

    setLoading(true)

    try {
      await apiRequest(
        "/service-provider-invitations/accept",
        {
          method: "POST",
          body: JSON.stringify({
            token,
            name: name.trim(),
            password,
          }),
        }
      )

      setSuccess(true)
    } catch (error) {
      console.error(error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-card invitation-card">
          <div className="invitation-success-icon">
            <CheckCircle2 size={30} />
          </div>

          <p className="eyebrow">
            Service Provider
          </p>

          <h1>You're all set</h1>

          <p className="auth-subtitle">
            Your account has been created successfully.
            You can now sign in and access Property SaaS.
          </p>

          <button
            className="primary-button invitation-full-button"
            onClick={() => navigate("/login")}
          >
            Go to login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-page">
      <div className="auth-card invitation-card">

        <div className="invitation-icon">
          <UserRound size={25} />
        </div>

        <p className="eyebrow">
          Property SaaS
        </p>

        <h1>Accept your invitation</h1>

        <p className="auth-subtitle">
          Create your account to connect with the
          organisation that invited you.
        </p>

        <div className="invitation-info">
          <LockKeyhole size={17} />

          <span>
            Your account details are securely stored.
          </span>
        </div>

        <form onSubmit={handleSubmit}>

          <label>
            Name

            <input
              type="text"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="Your name"
              disabled={loading}
              autoComplete="name"
            />
          </label>

          <label>
            Password

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Create a password"
              disabled={loading}
              autoComplete="new-password"
            />
          </label>

          <label>
            Confirm password

            <input
              type="password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(event.target.value)
              }
              placeholder="Confirm your password"
              disabled={loading}
              autoComplete="new-password"
            />
          </label>

          {error && (
            <div className="form-error invitation-error">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="primary-button invitation-full-button"
            disabled={loading}
          >
            {loading
              ? "Creating account..."
              : "Accept invitation"}
          </button>

        </form>

        <p className="invitation-footer">
          By continuing, you'll create your Property SaaS
          worker account.
        </p>

      </div>
    </div>
  )
}