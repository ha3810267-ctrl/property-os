
import { useEffect, useState } from "react"
import {
  Plus,
  Wrench,
  Home,
  Clock,
  CheckCircle2,
  UserRound,
} from "lucide-react"
import { apiRequest } from "../services/api"
import "../TenantDashboard.css"

export default function TenantDashboard() {
  const [tenant, setTenant] = useState(null)
  const [maintenance, setMaintenance] = useState([])

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const [error, setError] = useState("")
  const [formError, setFormError] = useState("")
  const [success, setSuccess] = useState("")

  const [showForm, setShowForm] = useState(false)
  const [description, setDescription] = useState("")

  async function loadDashboard(showLoading = true) {
    try {
      if (showLoading) {
        setLoading(true)
      }

      setError("")

      const [tenantData, maintenanceData] =
        await Promise.all([
          apiRequest("/tenant/me"),
          apiRequest("/maintenance-requests"),
        ])

      setTenant(tenantData)

      setMaintenance(
        Array.isArray(maintenanceData)
          ? maintenanceData
          : maintenanceData?.maintenance || []
      )
    } catch (err) {
      console.error(err)

      if (showLoading) {
        setError(
          err.message ||
            "Could not load your dashboard"
        )
      }
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    loadDashboard(true)

    const interval = setInterval(() => {
      loadDashboard(false)
    }, 5000)

    return () => {
      clearInterval(interval)
    }
  }, [])

  function getStatusClass(status) {
    if (!status) return ""

    return status
      .toLowerCase()
      .replace(/\s+/g, "-")
  }

  function openForm() {
    setDescription("")
    setFormError("")
    setSuccess("")
    setShowForm(true)
  }

  function closeForm() {
    if (submitting) return

    setShowForm(false)
    setDescription("")
    setFormError("")
  }

  async function handleSubmit(event) {
    event.preventDefault()

    setFormError("")
    setSuccess("")

    if (!description.trim()) {
      setFormError(
        "Please describe the maintenance problem"
      )
      return
    }

    if (description.trim().length < 10) {
      setFormError(
        "Please provide a little more detail about the problem"
      )
      return
    }

    setSubmitting(true)

    try {
      const newRequest = await apiRequest(
        "/maintenance-requests",
        {
          method: "POST",
          body: JSON.stringify({
            description: description.trim(),
            tenant_id: tenant.id,
          }),
        }
      )

      setMaintenance((current) => [
        newRequest,
        ...current,
      ])

      setDescription("")
      setShowForm(false)
      setSuccess(
        "Maintenance request submitted successfully"
      )
    } catch (err) {
      setFormError(
        err.message ||
          "Could not submit your maintenance request"
      )
    } finally {
      setSubmitting(false)
    }
  }

  function getAssignedWorkers(request) {
    if (!Array.isArray(request.assignments)) {
      return []
    }

    return request.assignments
  }

  function getSelectedExternalWorker(request) {
    if (
      !Array.isArray(request.external_workers)
    ) {
      return null
    }

    return (
      request.external_workers.find(
        (worker) => worker.is_selected === true
      ) || null
    )
  }

  if (loading) {
    return (
      <div className="page tenant-dashboard">
        <div className="page-header">
          <div>
            <p className="eyebrow">
              Tenant portal
            </p>

            <h1>
              Loading your dashboard...
            </h1>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page tenant-dashboard">
        <div className="page-header">
          <div>
            <p className="eyebrow">
              Tenant portal
            </p>

            <h1>
              Something went wrong
            </h1>

            <p>{error}</p>

            <button
              className="primary-button"
              onClick={() => loadDashboard(true)}
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    )
  }

  const openRequests = maintenance.filter(
    (request) =>
      request.status !== "completed" &&
      request.status !== "cancelled"
  ).length

  const completedRequests = maintenance.filter(
    (request) =>
      request.status === "completed"
  ).length

  return (
    <div className="page tenant-dashboard">
      <div className="page-header">
        <div>
          <p className="eyebrow">
            Tenant portal
          </p>

          <h1>
            Welcome
            {tenant?.name
              ? `, ${tenant.name}`
              : ""}
          </h1>

          <p>
            Manage your property and report
            maintenance problems.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={openForm}
        >
          <Plus size={17} />
          Report a problem
        </button>
      </div>

      {success && (
        <div className="tenant-success">
          <CheckCircle2 size={17} />
          {success}
        </div>
      )}

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <Home size={22} />

          <p className="eyebrow">
            Your property
          </p>

          <h2>
            {tenant?.property?.name ||
              tenant?.property_name ||
              "Property"}
          </h2>

          <p>
            {tenant?.property?.address ||
              tenant?.property_address ||
              "Your property information"}
          </p>
        </div>

        <div className="dashboard-card">
          <Clock size={22} />

          <p className="eyebrow">
            Open requests
          </p>

          <h2>{openRequests}</h2>

          <p>
            Maintenance requests currently
            being handled
          </p>
        </div>

        <div className="dashboard-card">
          <CheckCircle2 size={22} />

          <p className="eyebrow">
            Completed
          </p>

          <h2>{completedRequests}</h2>

          <p>
            Previously completed requests
          </p>
        </div>
      </div>

      <div className="page-section">
        <div className="section-header">
          <div>
            <p className="eyebrow">
              Maintenance
            </p>

            <h2>
              Your requests
            </h2>

            <p>
              Track problems reported to your
              property manager.
            </p>
          </div>

          <button
            className="secondary-button"
            onClick={openForm}
          >
            <Wrench size={17} />
            New request
          </button>
        </div>

        {maintenance.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Wrench size={22} />
            </div>

            <h3>
              No maintenance requests
            </h3>

            <p>
              If something needs fixing, you
              can report it here.
            </p>

            <button
              className="primary-button"
              onClick={openForm}
            >
              <Plus size={17} />
              Report a problem
            </button>
          </div>
        ) : (
          <div className="card-list">
            {maintenance.map((request) => {
              const assignedWorkers =
                getAssignedWorkers(request)

              const selectedExternalWorker =
                getSelectedExternalWorker(
                  request
                )

              return (
                <div
                  className="dashboard-card"
                  key={request.id}
                >
                  <div>
                    <p className="eyebrow">
                      {request.category ||
                        "Maintenance request"}
                    </p>

                    <h3>
                      {request.description ||
                        "No description available"}
                    </h3>

                    <p>
                      Priority:{" "}
                      {request.priority ||
                        "Normal"}
                    </p>
                  </div>

                  <div>
                    <span
                      className={`status ${getStatusClass(
                        request.status
                      )}`}
                    >
                      {request.status ||
                        "Open"}
                    </span>
                  </div>

                  <div className="tenant-maintenance-assignment">
                    <UserRound size={17} />

                    <div>
                      <p className="eyebrow">
                        {assignedWorkers.length === 1
                          ? "Assigned worker"
                          : "Assigned workers"}
                      </p>

                      {assignedWorkers.length > 0 ? (
                        <div>
                          {assignedWorkers.map(
                            (worker) => (
                              <strong
                                key={worker.user_id}
                                style={{
                                  display: "block",
                                  marginBottom: "4px",
                                }}
                              >
                                {worker.worker_name ||
                                  worker.name ||
                                  `Worker #${worker.user_id}`}
                              </strong>
                            )
                          )}
                        </div>
                      ) : (
                        <p>
                          Your request is waiting
                          to be assigned.
                        </p>
                      )}
                    </div>
                  </div>

                  {selectedExternalWorker && (
                    <div className="tenant-maintenance-assignment">
                      <Wrench size={17} />

                      <div>
                        <p className="eyebrow">
                          External provider
                        </p>

                        <strong>
                          {selectedExternalWorker.name}
                        </strong>

                        <p>
                          {selectedExternalWorker.trade}

                          {selectedExternalWorker.location
                            ? ` · ${selectedExternalWorker.location}`
                            : ""}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {showForm && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeForm()
            }
          }}
        >
          <div className="modal">
            <div className="modal-header">
              <div>
                <p className="eyebrow">
                  Maintenance
                </p>

                <h2>
                  Report a problem
                </h2>
              </div>
            </div>

            <p>
              Describe what is wrong with your
              property. PropertyOS will analyse
              the request and route it to the
              appropriate worker.
            </p>

            <form onSubmit={handleSubmit}>
              <label>
                What needs fixing?

                <textarea
                  value={description}
                  onChange={(event) =>
                    setDescription(
                      event.target.value
                    )
                  }
                  placeholder="e.g. The kitchen sink is leaking underneath the cabinet..."
                  rows={6}
                  disabled={submitting}
                />
              </label>

              {formError && (
                <p className="form-error">
                  {formError}
                </p>
              )}

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={closeForm}
                  disabled={submitting}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={submitting}
                >
                  {submitting
                    ? "Submitting..."
                    : "Submit request"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
