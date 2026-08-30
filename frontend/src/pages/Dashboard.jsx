
import {
  Building2,
  Users,
  Wrench,
  AlertTriangle,
  ArrowUpRight,
  Plus,
} from "lucide-react"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { apiRequest } from "../services/api"

export default function Dashboard() {
  const navigate = useNavigate()

  const [stats, setStats] = useState(null)
  const [recentRequests, setRecentRequests] = useState([])
  const [maintenanceLoading, setMaintenanceLoading] =
    useState(true)

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [
          statsData,
          maintenanceData,
        ] = await Promise.all([
          apiRequest("/dashboard/stats"),
          apiRequest("/maintenance-requests"),
        ])

        setStats(statsData)

        const requests = Array.isArray(
          maintenanceData
        )
          ? maintenanceData
          : []

        const activeRequests =
          requests.filter(
            (request) =>
              request.status !== "completed" &&
              request.status !== "cancelled"
          )

        const sortedRequests = [
          ...activeRequests,
        ].sort(
          (a, b) =>
            new Date(b.created_at) -
            new Date(a.created_at)
        )

        setRecentRequests(
          sortedRequests.slice(0, 6)
        )
      } catch (error) {
        console.error(
          "Failed to load dashboard:",
          error
        )
      } finally {
        setMaintenanceLoading(false)
      }
    }

    loadDashboard()
  }, [])

  function formatStatus(status) {
    if (!status) return ""

    return status
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      )
  }

  function formatDate(date) {
    if (!date) return ""

    const parsedDate = new Date(date)

    if (
      Number.isNaN(
        parsedDate.getTime()
      )
    ) {
      return ""
    }

    return parsedDate.toLocaleDateString(
      undefined,
      {
        day: "numeric",
        month: "short",
        year: "numeric",
      }
    )
  }

  function createMaintenanceRequest() {
    navigate("/maintenance")
  }

  function viewAllMaintenance() {
    navigate("/maintenance")
  }

  return (
    <div className="dashboard-page">

      {/* ==================================================
          HEADER
      ================================================== */}

      <div className="page-header">

        <div>
          <p className="eyebrow">
            Overview
          </p>

          <h1>
            Dashboard
          </h1>

          <p className="page-subtitle">
            Here’s what’s happening across your properties
          </p>
        </div>

        <button
          className="primary-button"
          onClick={
            createMaintenanceRequest
          }
        >
          <Plus size={17} />
          New maintenance request
        </button>

      </div>

      {/* ==================================================
          STATS
      ================================================== */}

      <div className="stats-grid">

        <div className="stat-card">

          <div className="stat-card-top">
            <p>
              Properties
            </p>

            <Building2 size={18} />
          </div>

          <h2>
            {stats?.properties ?? "—"}
          </h2>

          <span>
            Total properties
          </span>

        </div>

        <div className="stat-card">

          <div className="stat-card-top">
            <p>
              Tenants
            </p>

            <Users size={18} />
          </div>

          <h2>
            {stats?.tenants ?? "—"}
          </h2>

          <span>
            Active tenants
          </span>

        </div>

        <div className="stat-card">

          <div className="stat-card-top">
            <p>
              Open maintenance
            </p>

            <Wrench size={18} />
          </div>

          <h2>
            {stats?.open_maintenance ?? "—"}
          </h2>

          <span>
            Requests needing attention
          </span>

        </div>

        <div className="stat-card">

          <div className="stat-card-top">
            <p>
              Urgent issues
            </p>

            <AlertTriangle size={18} />
          </div>

          <h2>
            {stats?.urgent_issues ?? "—"}
          </h2>

          <span>
            High priority requests
          </span>

        </div>

      </div>

      {/* ==================================================
          RECENT MAINTENANCE
      ================================================== */}

      <section className="dashboard-card dashboard-maintenance-card">

        <div className="card-header">

          <div>
            <p className="eyebrow">
              Maintenance
            </p>

            <h2>
              Recent requests
            </h2>

            <p className="card-subtitle">
              The latest maintenance issues requiring attention
            </p>
          </div>

          <button
            className="text-button"
            onClick={
              viewAllMaintenance
            }
          >
            View all
            <ArrowUpRight size={14} />
          </button>

        </div>

        {maintenanceLoading ? (

          <div className="empty-state">

            <div className="empty-icon">
              <Wrench size={20} />
            </div>

            <h3>
              Loading requests...
            </h3>

            <p>
              Getting your latest maintenance requests.
            </p>

          </div>

        ) : recentRequests.length === 0 ? (

          <div className="empty-state">

            <div className="empty-icon">
              <Wrench size={20} />
            </div>

            <h3>
              No recent requests
            </h3>

            <p>
              New maintenance requests will appear here
              when tenants report issues.
            </p>

            <button
              className="primary-button"
              onClick={
                createMaintenanceRequest
              }
            >
              <Plus size={17} />
              New request
            </button>

          </div>

        ) : (

          <div className="dashboard-maintenance-list">

            {recentRequests.map(
              (request) => {

                const priority =
                  request.priority ||
                  "normal"

                return (
                  <div
                    className="dashboard-maintenance-item"
                    key={request.id}
                    onClick={() =>
                      navigate(
                        "/maintenance"
                      )
                    }
                    role="button"
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (
                        event.key ===
                          "Enter" ||
                        event.key ===
                          " "
                      ) {
                        navigate(
                          "/maintenance"
                        )
                      }
                    }}
                  >

                    {/* Icon */}

                    <div className="dashboard-maintenance-icon">
                      <Wrench size={17} />
                    </div>

                    {/* Content */}

                    <div className="dashboard-maintenance-content">

                      <div className="dashboard-maintenance-top">

                        <strong>
                          {request.category ||
                            "Maintenance request"}
                        </strong>

                        <span
                          className={`priority-badge ${priority}`}
                        >
                          {priority}
                        </span>

                      </div>

                      <p>
                        {request.description ||
                          "No description provided"}
                      </p>

                      <div className="dashboard-maintenance-meta">

                        <span>
                          {formatStatus(
                            request.status
                          )}
                        </span>

                        <span>
                          {formatDate(
                            request.created_at
                          )}
                        </span>

                      </div>

                    </div>

                    {/* Arrow */}

                    <div className="dashboard-maintenance-arrow">
                      <ArrowUpRight
                        size={16}
                      />
                    </div>

                  </div>
                )
              }
            )}

          </div>

        )}

      </section>

    </div>
  )
}
