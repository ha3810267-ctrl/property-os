import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { apiRequest } from "../services/api"

export default function Login() {
  const navigate = useNavigate()

  const [mode, setMode] = useState("login")

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const [name, setName] = useState("")
  const [organisationName, setOrganisationName] = useState("")

  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  function switchMode(newMode) {
    setMode(newMode)
    setError("")
    setEmail("")
    setPassword("")
    setName("")
    setOrganisationName("")
  }

  async function handleSubmit(event) {
    event.preventDefault()

    setError("")
    setLoading(true)

    try {
      if (mode === "login") {
        const data = await apiRequest("/login", {
          method: "POST",
          body: JSON.stringify({
            email: email.trim(),
            password,
          }),
        })

        console.log("LOGIN DATA:", data)

        if (!data.access_token) {
          throw new Error(
            "Login succeeded but no access token was returned"
          )
        }

        localStorage.setItem(
          "access_token",
          data.access_token
        )

        localStorage.setItem(
          "current_user",
          JSON.stringify({
            id: data.id,
            name: data.name,
            email: data.email,
            role: data.role,
            organisation_id: data.organisation_id,
            tenant_id: data.tenant_id,
          })
        )

        if (
          data.role === "tenant" ||
          (data.tenant_id !== null &&
            data.tenant_id !== undefined)
        ) {
          navigate("/tenant-dashboard")
          return
        }

        navigate("/")
        return
      }

      const data = await apiRequest("/organisations/signup", {
        method: "POST",
        body: JSON.stringify({
          organisation_name: organisationName.trim(),
          name: name.trim(),
          email: email.trim(),
          password,
        }),
      })

      if (data.user) {
        setEmail(data.user.email)
      }

      setPassword("")
      setMode("login")

      setError(
        "Organisation created successfully — sign in to continue"
      )
    } catch (error) {
      setError(error.message || "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  const isSignup = mode === "signup"

  return (
    <div className="login-page">
      <div className="login-card">

        <div className="brand">
          <div className="brand-mark">P</div>
          <span>PropertyOS</span>
        </div>

        <div className="login-header">
          <p className="eyebrow">
            {isSignup ? "Get started" : "Welcome back"}
          </p>

          <h1>
            {isSignup
              ? "Create your organisation"
              : "Sign in"}
          </h1>

          <p>
            {isSignup
              ? "Set up your PropertyOS organisation"
              : "Sign in to manage your properties"}
          </p>
        </div>

        <form onSubmit={handleSubmit}>

          {isSignup && (
            <>
              <label>
                Organisation name

                <input
                  value={organisationName}
                  onChange={(event) =>
                    setOrganisationName(event.target.value)
                  }
                  placeholder="e.g. Smith Property Management"
                  required
                  disabled={loading}
                />
              </label>

              <label>
                Your name

                <input
                  value={name}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                  placeholder="e.g. John Smith"
                  required
                  disabled={loading}
                />
              </label>
            </>
          )}

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

          <label>
            Password

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
              autoComplete={
                isSignup
                  ? "new-password"
                  : "current-password"
              }
              required
              disabled={loading}
            />
          </label>

          {/* Forgot password */}

          {!isSignup && (
            <div
              style={{
                textAlign: "right",
                marginTop: "-8px",
                marginBottom: "16px",
              }}
            >
              <button
                type="button"
                className="secondary-button"
                onClick={() => navigate("/forgot-password")}
                disabled={loading}
              >
                Forgot password?
              </button>
            </div>
          )}

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
              ? isSignup
                ? "Creating..."
                : "Signing in..."
              : isSignup
                ? "Create organisation"
                : "Sign in"}
          </button>
        </form>

        <div
          style={{
            marginTop: "20px",
            textAlign: "center",
          }}
        >
          {isSignup ? (
            <p>
              Already have an account?{" "}

              <button
                type="button"
                className="secondary-button"
                onClick={() => switchMode("login")}
                disabled={loading}
              >
                Sign in
              </button>
            </p>
          ) : (
            <p>
              New to PropertyOS?{" "}

              <button
                type="button"
                className="secondary-button"
                onClick={() => switchMode("signup")}
                disabled={loading}
              >
                Create organisation
              </button>
            </p>
          )}
        </div>

      </div>
    </div>
  )
}