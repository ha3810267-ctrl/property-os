import {
  Building2,
  Wrench,
  AlertTriangle,
  ArrowUpRight,
  Plus,
  Mail,
} from "lucide-react"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { apiRequest } from "../services/api"

export default function Dashboard() {
  const navigate = useNavigate()

  const [stats, setStats] = useState(null)
  const [recentRequests, setRecentRequests] = useState([])
  const [recentReplies, setRecentReplies] = useState([])
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

        const replies = []

        requests.forEach((request) => {
          const externalWorkers =
            Array.isArray(request.external_workers)
              ? request.external_workers
              : []

          externalWorkers.forEach((worker) => {
            const workerReplies =
              Array.isArray(worker.replies)
                ? worker.replies
                : []

            workerReplies.forEach((reply) => {
              if (
                reply.direction !== "inbound"
              ) {
                return
              }

              replies.push({
                ...reply,
                maintenance_request_id:
                  request.id,
                maintenance_description:
                  request.description,
                maintenance_category:
                  request.category,
                property_address:
                  request.property_address ||
                  request.location,
                contractor_name:
                  worker.name ||
                  worker.business_name ||
                  worker.company_name ||
                  "Contractor",
              })
            })
          })
        })

        replies.sort(
          (a, b) =>
            new Date(
              b.received_at ||
                b.created_at ||
                b.date
            ) -
            new Date(
              a.received_at ||
                a.created_at ||
                a.date
            )
        )

        setRecentReplies(
          replies.slice(0, 5)
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

  function formatReplyDate(reply) {
    return formatDate(
      reply.received_at ||
        reply.created_at ||
        reply.date
    )
  }

  function getReplyPreview(reply) {
    const text =
      reply.text_body ||
      reply.text ||
      reply.body ||
      reply.html_body ||
      reply.content ||
      ""

    const cleaned = String(text)
      .replace(/<[^>]*>/g, " ")
      .replace(/\s+/g, " ")
      .trim()

    if (!cleaned) {
      return "Contractor sent a reply."
    }

    return cleaned.length > 180
      ? `${cleaned.slice(0, 180)}...`
      : cleaned
  }

  function createMaintenanceRequest() {
    navigate("/maintenance")
  }

  function viewAllMaintenance() {
    navigate("/maintenance")
  }

  function viewMaintenanceRequest() {
    navigate("/maintenance")
  }

  return (
    <div className="dashboard-page">

      {/* HEADER */}

      <div className="page-header">

        <div>
          <p className="eyebrow">
            Overview
          </p>

          <h1>
            Dashboard
          </h1>

          <p className="page-subtitle">
            Keep track of your properties, maintenance
            requests and contractor responses.
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

      {/* STATS */}

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

        <div className="stat-card">

          <div className="stat-card-top">
            <p>
              Contractor replies
            </p>

            <Mail size={18} />
          </div>

          <h2>
            {recentReplies.length}
          </h2>

          <span>
            Recent responses received
          </span>

        </div>

      </div>

      {/* RECENT CONTRACTOR REPLIES */}

      <section className="dashboard-card">

        <div className="card-header">

          <div>
            <p className="eyebrow">
              Contractor communication
            </p>

            <h2>
              Recent replies
            </h2>

            <p className="card-subtitle">
              The latest responses from contractors
              contacted about your maintenance requests.
            </p>
          </div>

          <button
            className="text-button"
            onClick={
              viewAllMaintenance
            }
          >
            View maintenance
            <ArrowUpRight size={14} />
          </button>

        </div>

        {maintenanceLoading ? (

          <div className="empty-state">

            <div className="empty-icon">
              <Mail size={20} />
            </div>

            <h3>
              Loading replies...
            </h3>

            <p>
              Checking for recent contractor responses.
            </p>

          </div>

        ) : recentReplies.length === 0 ? (

          <div className="empty-state">

            <div className="empty-icon">
              <Mail size={20} />
            </div>

            <h3>
              No contractor replies yet
            </h3>

            <p>
              Contractor responses will appear here
              when they reply to your maintenance requests.
            </p>

          </div>

        ) : (

          <div className="dashboard-maintenance-list">

            {recentReplies.map(
              (reply, index) => {

                const subject =
                  reply.subject ||
                  "Contractor reply"

                return (
                  <div
                    className="dashboard-maintenance-item"
                    key={
                      reply.id ||
                      `${reply.maintenance_request_id}-${index}`
                    }
                    onClick={
                      viewMaintenanceRequest
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
                        viewMaintenanceRequest()
                      }
                    }}
                  >

                    <div className="dashboard-maintenance-icon">
                      <Mail size={17} />
                    </div>

                    <div className="dashboard-maintenance-content">

                      <div className="dashboard-maintenance-top">

                        <strong>
                          {reply.contractor_name}
                        </strong>

                        <span>
                          {formatReplyDate(
                            reply
                          )}
                        </span>

                      </div>

                      <p>
                        {subject}
                      </p>

                      <p>
                        {getReplyPreview(
                          reply
                        )}
                      </p>

                      <div className="dashboard-maintenance-meta">

                        <span>
                          {reply.property_address ||
                            "Property"}
                        </span>

                        <span>
                          {reply.maintenance_category ||
                            "Maintenance request"}
                        </span>

                      </div>

                    </div>

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

      {/* RECENT MAINTENANCE */}

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
              The latest maintenance issues across
              your properties.
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
              Create a maintenance request to get
              started.
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

                    <div className="dashboard-maintenance-icon">
                      <Wrench size={17} />
                    </div>

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
                          {request.property_address ||
                            request.location ||
                            "Property"}
                        </span>

                        <span>
                          {formatDate(
                            request.created_at
                          )}
                        </span>

                      </div>

                    </div>

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