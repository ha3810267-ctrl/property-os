import { useEffect, useState } from "react"
import { apiRequest } from "../services/api"


export default function Account() {

  const [user, setUser] = useState(null)
  const [organisation, setOrganisation] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const [showPasswordForm, setShowPasswordForm] = useState(false)

  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const [passwordLoading, setPasswordLoading] = useState(false)
  const [passwordError, setPasswordError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState("")


  useEffect(() => {

    async function loadAccount() {

      try {

        setError("")

        const currentUser = await apiRequest("/me")

        setUser(currentUser)

        const organisations = await apiRequest("/organisations")

        const currentOrganisation = organisations.find(
          (organisation) =>
            organisation.id === currentUser.organisation_id
        )

        setOrganisation(currentOrganisation || null)

      } catch (err) {

        console.error(err)

        setError("Unable to load account details")

      } finally {

        setLoading(false)

      }
    }

    loadAccount()

  }, [])


  function openPasswordForm() {

    setShowPasswordForm(true)

    setPasswordError("")
    setPasswordSuccess("")

  }


  function closePasswordForm() {

    setShowPasswordForm(false)

    setCurrentPassword("")
    setNewPassword("")
    setConfirmPassword("")

    setPasswordError("")
    setPasswordSuccess("")

  }


  async function handleChangePassword(event) {

    event.preventDefault()

    setPasswordError("")
    setPasswordSuccess("")


    if (!currentPassword) {

      setPasswordError(
        "Please enter your current password"
      )

      return

    }


    if (!newPassword) {

      setPasswordError(
        "Please enter a new password"
      )

      return

    }


    if (!confirmPassword) {

      setPasswordError(
        "Please confirm your new password"
      )

      return

    }


    if (newPassword !== confirmPassword) {

      setPasswordError(
        "New passwords do not match"
      )

      return

    }


    if (currentPassword === newPassword) {

      setPasswordError(
        "New password must be different from your current password"
      )

      return

    }


    try {

      setPasswordLoading(true)

      const response = await apiRequest(
        "/change-password",
        {
          method: "POST",
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword
          })
        }
      )


      setPasswordSuccess(
        response?.message ||
        "Password changed successfully"
      )

      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")

    } catch (err) {

      console.error(err)

      setPasswordError(
        err?.message ||
        "Unable to change password"
      )

    } finally {

      setPasswordLoading(false)

    }

  }


  if (loading) {

    return (
      <div className="page">

        <div className="page-header">

          <div>

            <h1>Account</h1>

            <p>
              Manage your account and organisation
            </p>

          </div>

        </div>

        <p>Loading account...</p>

      </div>
    )

  }


  return (
    <div className="page">

      <div className="page-header">

        <div>

          <h1>Account</h1>

          <p>
            Manage your account and organisation
          </p>

        </div>

      </div>


      {error && (
        <div className="error-message">
          {error}
        </div>
      )}


      {/* Account */}

      <section className="settings-section">

        <div className="settings-section-header">

          <h2>Account</h2>

          <p>
            Your account information
          </p>

        </div>


        <div className="settings-card">

          <div className="settings-row">

            <div>

              <span className="settings-label">
                Name
              </span>

              <span className="settings-value">
                {user?.name || "—"}
              </span>

            </div>

          </div>


          <div className="settings-row">

            <div>

              <span className="settings-label">
                Email
              </span>

              <span className="settings-value">
                {user?.email || "—"}
              </span>

            </div>

          </div>


          <div className="settings-row">

            <div>

              <span className="settings-label">
                Role
              </span>

              <span className="settings-value">

                {user?.role
                  ? user.role
                      .replace("_", " ")
                      .replace(/\b\w/g, letter =>
                        letter.toUpperCase()
                      )
                  : "—"}

              </span>

            </div>

          </div>

        </div>

      </section>


      {/* Organisation */}

      <section className="settings-section">

        <div className="settings-section-header">

          <h2>Organisation</h2>

          <p>
            Your organisation details
          </p>

        </div>


        <div className="settings-card">

          <div className="settings-row">

            <div>

              <span className="settings-label">
                Organisation name
              </span>

              <span className="settings-value">
                {organisation?.name || "—"}
              </span>

            </div>

          </div>


          <div className="settings-row">

            <div>

              <span className="settings-label">
                Organisation ID
              </span>

              <span className="settings-value">
                {organisation?.id || "—"}
              </span>

            </div>

          </div>

        </div>

      </section>


      {/* Security */}

      <section className="settings-section">

        <div className="settings-section-header">

          <h2>Security</h2>

          <p>
            Manage your account security
          </p>

        </div>


        <div className="settings-card">

          <div className="settings-row">

            <div>

              <span className="settings-label">
                Password
              </span>

              <span className="settings-value">
                ••••••••
              </span>

            </div>


            {!showPasswordForm && (

              <button
                type="button"
                className="settings-button"
                onClick={openPasswordForm}
              >
                Change password
              </button>

            )}

          </div>


          {showPasswordForm && (

            <div className="password-form">

              {passwordError && (

                <div className="error-message">
                  {passwordError}
                </div>

              )}


              {passwordSuccess && (

                <div className="success-message">
                  {passwordSuccess}
                </div>

              )}


              <form
                onSubmit={handleChangePassword}
              >

                <div className="form-group">

                  <label>
                    Current password
                  </label>

                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(event) =>
                      setCurrentPassword(
                        event.target.value
                      )
                    }
                    autoComplete="current-password"
                    disabled={passwordLoading}
                  />

                </div>


                <div className="form-group">

                  <label>
                    New password
                  </label>

                  <input
                    type="password"
                    value={newPassword}
                    onChange={(event) =>
                      setNewPassword(
                        event.target.value
                      )
                    }
                    autoComplete="new-password"
                    disabled={passwordLoading}
                  />

                </div>


                <div className="form-group">

                  <label>
                    Confirm new password
                  </label>

                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(event) =>
                      setConfirmPassword(
                        event.target.value
                      )
                    }
                    autoComplete="new-password"
                    disabled={passwordLoading}
                  />

                </div>


                <div className="password-form-actions">

                  <button
                    type="submit"
                    className="settings-button"
                    disabled={passwordLoading}
                  >
                    {passwordLoading
                      ? "Changing..."
                      : "Change password"}
                  </button>


                  <button
                    type="button"
                    className="settings-button secondary"
                    onClick={closePasswordForm}
                    disabled={passwordLoading}
                  >
                    Cancel
                  </button>

                </div>

              </form>

            </div>

          )}

        </div>

      </section>

    </div>
  )
}