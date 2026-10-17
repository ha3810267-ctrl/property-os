
import {
  Search,
  ClipboardList,
  AlertTriangle,
  ArrowUpRight,
  Plus,
  Mail,
  ChevronDown,
  ChevronUp,
} from "lucide-react"

import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { apiRequest } from "../services/api"

export default function Dashboard() {
  const navigate = useNavigate()

  const [stats, setStats] = useState(null)
  const [recentRequests, setRecentRequests] = useState([])
  const [recentReplies, setRecentReplies] = useState([])
  const [expandedReplyRequests, setExpandedReplyRequests] = useState(
    () => new Set()
  )
  const [maintenanceLoading, setMaintenanceLoading] =
    useState(true)

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [statsData, maintenanceData] =
          await Promise.all([
            apiRequest("/dashboard/stats"),
            apiRequest("/maintenance-requests"),
          ])

        setStats(statsData)

        const requests = Array.isArray(maintenanceData)
          ? maintenanceData
          : []

        const activeRequests = requests.filter(
          (request) =>
            request.status !== "completed" &&
            request.status !== "cancelled"
        )

        const sortedRequests = [...activeRequests].sort(
          (a, b) =>
            new Date(b.created_at) - new Date(a.created_at)
        )

        setRecentRequests(sortedRequests.slice(0, 6))

        const replies = []

        requests.forEach((request) => {
          const externalWorkers = Array.isArray(
            request.external_workers
          )
            ? request.external_workers
            : []

          externalWorkers.forEach((worker) => {
            const workerReplies = Array.isArray(worker.replies)
              ? worker.replies
              : []

            workerReplies.forEach((reply) => {
              if (reply.direction !== "inbound") {
                return
              }

              replies.push({
                ...reply,
                maintenance_request_id: request.id,
                maintenance_description: request.description,
                maintenance_category: request.category,
                property_address:
                  request.property_address || request.location,
                contractor_name:
                  worker.name ||
                  worker.business_name ||
                  worker.company_name ||
                  "Service professional",
              })
            })
          })
        })

        replies.sort(
          (a, b) =>
            new Date(
              b.received_at || b.created_at || b.date
            ) -
            new Date(
              a.received_at || a.created_at || a.date
            )
        )

        setRecentReplies(replies.slice(0, 5))
      } catch (error) {
        console.error("Failed to load dashboard:", error)
      } finally {
        setMaintenanceLoading(false)
      }
    }

    loadDashboard()
  }, [])

  function formatDate(date) {
    if (!date) return ""

    const parsedDate = new Date(date)

    if (Number.isNaN(parsedDate.getTime())) {
      return ""
    }

    return parsedDate.toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
    })
  }

  function formatReplyDate(reply) {
    return formatDate(
      reply.received_at || reply.created_at || reply.date
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
      return "Service professional sent a reply."
    }

    return cleaned.length > 180
      ? `${cleaned.slice(0, 180)}...`
      : cleaned
  }

  const repliesByRequest = recentReplies.reduce((groups, reply) => {
    const requestId = reply.maintenance_request_id
    const existing = groups.get(requestId)

    if (existing) {
      existing.replies.push(reply)
    } else {
      groups.set(requestId, {
        id: requestId,
        description: reply.maintenance_description,
        category: reply.maintenance_category,
        propertyAddress: reply.property_address,
        replies: [reply],
      })
    }

    return groups
  }, new Map())

  function toggleReplyRequest(requestId) {
    setExpandedReplyRequests((current) => {
      const next = new Set(current)
      if (next.has(requestId)) {
        next.delete(requestId)
      } else {
        next.add(requestId)
      }
      return next
    })
  }

  function createRequest() {
    navigate("/requests")
  }

  function viewAllRequests() {
    navigate("/requests")
  }

  function openRequest() {
    navigate("/requests")
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Your workspace</p>

          <h1>Dashboard</h1>

          <p className="page-subtitle">
            Find the right professionals, manage your requests
            and keep track of responses in one place.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={createRequest}
        >
          <Plus size={17} />
          Find a professional
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-top">
            <p>Locations</p>
            <Search size={18} />
          </div>

          <h2>{stats?.properties ?? "—"}</h2>

          <span>Saved service locations</span>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <p>Open requests</p>
            <ClipboardList size={18} />
          </div>

          <h2>{stats?.open_maintenance ?? "—"}</h2>

          <span>Requests still in progress</span>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <p>Urgent requests</p>
            <AlertTriangle size={18} />
          </div>

          <h2>{stats?.urgent_issues ?? "—"}</h2>

          <span>Requests marked high priority</span>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <p>Recent replies</p>
            <Mail size={18} />
          </div>

          <h2>{recentReplies.length}</h2>

          <span>Responses from professionals</span>
        </div>
      </div>

      <section className="dashboard-card">
        <div className="card-header">
          <div>
            <p className="eyebrow">Communication</p>

            <h2>Recent replies</h2>

            <p className="card-subtitle">
              The latest responses from professionals contacted
              about your service requests.
            </p>
          </div>

          <button
            className="text-button"
            onClick={viewAllRequests}
          >
            View requests
            <ArrowUpRight size={14} />
          </button>
        </div>

        {maintenanceLoading ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Mail size={20} />
            </div>

            <h3>Loading replies...</h3>

            <p>Checking for recent responses.</p>
          </div>
        ) : recentReplies.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Mail size={20} />
            </div>

            <h3>No replies yet</h3>

            <p>
              Responses from professionals will appear here
              when they reply to your requests.
            </p>
          </div>
        ) : (
          <div className="dashboard-reply-requests">
            {[...repliesByRequest.values()].map((request) => {
              const expanded = expandedReplyRequests.has(request.id)
              const label = request.description || request.category || "Service request"

              return (
                <section className="dashboard-reply-request" key={request.id}>
                  <button
                    type="button"
                    className="dashboard-reply-request-toggle"
                    aria-expanded={expanded}
                    onClick={() => toggleReplyRequest(request.id)}
                  >
                    <span className="dashboard-maintenance-icon">
                      <ClipboardList size={17} />
                    </span>
                    <span className="dashboard-reply-request-heading">
                      <span className="dashboard-maintenance-top">
                        <strong>{request.category || "Service request"}</strong>
                        <span className="dashboard-reply-count">
                          {request.replies.length} {request.replies.length === 1 ? "reply" : "replies"}
                        </span>
                      </span>
                      <span className="dashboard-reply-request-description">{label}</span>
                      <span className="dashboard-maintenance-meta">
                        <span>{request.propertyAddress || "Location not specified"}</span>
                        <span>Latest {formatReplyDate(request.replies[0])}</span>
                      </span>
                    </span>
                    <span className="dashboard-reply-request-chevron" aria-hidden="true">
                      {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                    </span>
                  </button>

                  {expanded && (
                    <div className="dashboard-reply-list">
                      {request.replies.map((reply, index) => (
                        <article
                          className="dashboard-reply-item"
                          key={reply.id || `${request.id}-${index}`}
                        >
                          <div className="dashboard-reply-item-top">
                            <strong>{reply.contractor_name}</strong>
                            <span>{formatReplyDate(reply)}</span>
                          </div>
                          <p className="dashboard-reply-subject">
                            {reply.subject || "Professional reply"}
                          </p>
                          <p className="dashboard-reply-preview">{getReplyPreview(reply)}</p>
                        </article>
                      ))}
                      <button
                        type="button"
                        className="dashboard-reply-view-request"
                        onClick={openRequest}
                      >
                        Open service requests <ArrowUpRight size={14} />
                      </button>
                    </div>
                  )}
                </section>
              )
            })}
          </div>
        )}
      </section>

      <section className="dashboard-card dashboard-maintenance-card">
        <div className="card-header">
          <div>
            <p className="eyebrow">Your activity</p>

            <h2>Recent requests</h2>

            <p className="card-subtitle">
              Your latest service requests and their current details.
            </p>
          </div>

          <button
            className="text-button"
            onClick={viewAllRequests}
          >
            View all
            <ArrowUpRight size={14} />
          </button>
        </div>

        {maintenanceLoading ? (
          <div className="empty-state">
            <div className="empty-icon">
              <ClipboardList size={20} />
            </div>

            <h3>Loading requests...</h3>

            <p>Getting your latest requests.</p>
          </div>
        ) : recentRequests.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <ClipboardList size={20} />
            </div>

            <h3>No recent requests</h3>

            <p>
              Tell Matchly what you need and start finding
              suitable professionals.
            </p>

            <button
              className="primary-button"
              onClick={createRequest}
            >
              <Plus size={17} />
              Find a professional
            </button>
          </div>
        ) : (
          <div className="dashboard-maintenance-list">
            {recentRequests.map((request) => {
              const priority = request.priority || "normal"

              return (
                <div
                  className="dashboard-maintenance-item"
                  key={request.id}
                  onClick={openRequest}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" ||
                      event.key === " "
                    ) {
                      event.preventDefault()
                      openRequest()
                    }
                  }}
                >
                  <div className="dashboard-maintenance-icon">
                    <ClipboardList size={17} />
                  </div>

                  <div className="dashboard-maintenance-content">
                    <div className="dashboard-maintenance-top">
                      <strong>
                        {request.category || "Service request"}
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
                          "Location not specified"}
                      </span>

                      <span>{formatDate(request.created_at)}</span>
                    </div>
                  </div>

                  <div className="dashboard-maintenance-arrow">
                    <ArrowUpRight size={16} />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
