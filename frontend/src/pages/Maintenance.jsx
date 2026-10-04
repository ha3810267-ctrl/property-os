import { useEffect, useState } from "react"
import {
  Wrench,
  Plus,
  Search,
  X,
  Sparkles,
  Trash2,
  ExternalLink,
  Check,
  Phone,
  MapPin,
  Star,
  ChevronDown,
  ChevronUp,
  Mail,
} from "lucide-react"
import { apiRequest } from "../services/api"

const statuses = [
  "open",
  "in_progress",
  "completed",
  "cancelled",
]

const priorities = [
  "low",
  "normal",
  "high",
  "urgent",
]

export default function Maintenance() {
  const [requests, setRequests] = useState([])
  const [properties, setProperties] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")

  const [showModal, setShowModal] = useState(false)
  const [description, setDescription] = useState("")
  const [propertyId, setPropertyId] = useState("")
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState("")

  const [searchingExternalWorker, setSearchingExternalWorker] =
    useState(null)

  const [selectingExternalWorker, setSelectingExternalWorker] =
    useState(null)

  const [expandedReplies, setExpandedReplies] = useState({})

  async function loadData() {
    try {
      setLoading(true)
      setError("")

      const [maintenanceData, propertiesData] =
        await Promise.all([
          apiRequest("/maintenance-requests"),
          apiRequest("/properties"),
        ])

      setRequests(
        Array.isArray(maintenanceData)
          ? maintenanceData
          : []
      )

      setProperties(
        Array.isArray(propertiesData)
          ? propertiesData
          : []
      )
    } catch (error) {
      console.error(error)

      setError(
        error.message ||
          "Unable to load maintenance"
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  function toggleReply(requestId, candidateId, replyId) {
    const key = `${requestId}-${candidateId}-${replyId}`

    setExpandedReplies((current) => ({
      ...current,
      [key]: !current[key],
    }))
  }

  function isReplyExpanded(
    requestId,
    candidateId,
    replyId
  ) {
    const key = `${requestId}-${candidateId}-${replyId}`

    return expandedReplies[key] === true
  }

  function formatReplyDate(date) {
    if (!date) return ""

    const parsed = new Date(date)

    if (Number.isNaN(parsed.getTime())) {
      return ""
    }

    return parsed.toLocaleString()
  }

  function getReplyContent(reply) {
    if (reply?.text_body) {
      return reply.text_body
    }

    if (reply?.html_body) {
      return reply.html_body
    }

    return "No reply content was provided."
  }

  function getProperty(propertyId) {
    return properties.find(
      (property) => property.id === propertyId
    )
  }

  function openModal() {
    setDescription("")
    setPropertyId("")
    setFormError("")
    setShowModal(true)
  }

  function closeModal() {
    if (saving) return

    setShowModal(false)
    setDescription("")
    setPropertyId("")
    setFormError("")
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError("")

    if (!propertyId) {
      setFormError(
        "Please select a property"
      )
      return
    }

    if (!description.trim()) {
      setFormError(
        "Maintenance description is required"
      )
      return
    }

    const property = getProperty(
      Number(propertyId)
    )

    if (!property) {
      setFormError(
        "Selected property could not be found"
      )
      return
    }

    setSaving(true)

    try {
      const newRequest = await apiRequest(
        "/maintenance-requests",
        {
          method: "POST",
          body: JSON.stringify({
            description: description.trim(),
            property_id: Number(propertyId),
          }),
        }
      )

      setRequests((current) => [
        newRequest,
        ...current,
      ])

      setShowModal(false)
      setDescription("")
      setPropertyId("")
      setFormError("")
    } catch (error) {
      console.error(error)

      setFormError(
        error.message ||
          "Could not create maintenance request"
      )
    } finally {
      setSaving(false)
    }
  }

  async function updateRequest(id, updates) {
    try {
      setError("")

      const updated = await apiRequest(
        `/maintenance-requests/${id}`,
        {
          method: "PUT",
          body: JSON.stringify(updates),
        }
      )

      if (updates.status === "completed") {
        setRequests((current) =>
          current.filter(
            (request) => request.id !== id
          )
        )

        return
      }

      setRequests((current) =>
        current.map((request) =>
          request.id === id
            ? updated
            : request
        )
      )
    } catch (error) {
      console.error(error)

      setError(
        error.message ||
          "Could not update maintenance request"
      )
    }
  }

  async function deleteRequest(request) {
    const confirmed = window.confirm(
      `Delete this maintenance request?\n\n"${request.description}"`
    )

    if (!confirmed) return

    try {
      setError("")

      await apiRequest(
        `/maintenance-requests/${request.id}`,
        {
          method: "DELETE",
        }
      )

      setRequests((current) =>
        current.filter(
          (item) =>
            item.id !== request.id
        )
      )
    } catch (error) {
      console.error(error)

      setError(
        error.message ||
          "Could not delete maintenance request"
      )
    }
  }

  async function searchExternalWorkers(
    requestId
  ) {
    try {
      setSearchingExternalWorker(requestId)
      setError("")

      const result = await apiRequest(
        `/maintenance-requests/${requestId}/external-workers/search`,
        {
          method: "POST",
        }
      )

      const updated =
        result?.maintenance_request

      if (!updated) {
        throw new Error(
          "External worker search returned an invalid response"
        )
      }

      setRequests((current) =>
        current.map((request) =>
          request.id === requestId
            ? updated
            : request
        )
      )
    } catch (error) {
      console.error(error)

      setError(
        error.message ||
          "Could not search for external workers"
      )
    } finally {
      setSearchingExternalWorker(null)
    }
  }

  async function selectExternalWorker(
    requestId,
    candidateId
  ) {
    const key = `${requestId}-${candidateId}`

    try {
      setSelectingExternalWorker(key)
      setError("")

      const updated = await apiRequest(
        `/maintenance-requests/${requestId}/external-workers/${candidateId}/select`,
        {
          method: "POST",
        }
      )

      setRequests((current) =>
        current.map((request) =>
          request.id === requestId
            ? updated
            : request
        )
      )
    } catch (error) {
      console.error(error)

      setError(
        error.message ||
          "Could not select external worker"
      )
    } finally {
      setSelectingExternalWorker(null)
    }
  }

  function getExternalWorkers(request) {
    return Array.isArray(
      request.external_workers
    )
      ? request.external_workers
      : []
  }

  function formatStatus(status) {
    if (!status) return ""

    return status
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      )
  }

  function formatPhone(phone) {
    if (!phone) return null

    return phone
  }

  function formatMatchScore(score) {
    if (score == null) return null

    return Math.round(
      Number(score) * 100
    )
  }

  const filteredRequests = requests.filter(
    (request) => {
      if (request.status === "completed") {
        return false
      }

      const property = getProperty(
        request.property_id
      )

      const externalWorkers =
        getExternalWorkers(request)

      const externalWorkerNames =
        externalWorkers
          .map(
            (worker) =>
              worker.name || ""
          )
          .join(" ")

      const term =
        search.trim().toLowerCase()

      if (!term) {
        return true
      }

      return (
        request.description
          ?.toLowerCase()
          .includes(term) ||
        request.category
          ?.toLowerCase()
          .includes(term) ||
        property?.name
          ?.toLowerCase()
          .includes(term) ||
        property?.address
          ?.toLowerCase()
          .includes(term) ||
        externalWorkerNames
          .toLowerCase()
          .includes(term)
      )
    }
  )

  const completedRequests =
    requests.filter(
      (request) =>
        request.status === "completed"
    )

  return (
    <div className="dashboard-page maintenance-page">
      <div className="properties-header">
        <div className="properties-title">
          <p className="eyebrow">
            Operations
          </p>

          <h1>Maintenance</h1>

          <p className="page-subtitle">
            Track and manage maintenance requests
            across your properties
          </p>
        </div>

        <div className="properties-header-actions">
          <button
            className="primary-button"
            onClick={openModal}
            disabled={
              properties.length === 0
            }
          >
            <Plus size={17} />
            Add request
          </button>
        </div>
      </div>

      <div className="property-toolbar">
        <div className="search-box">
          <Search size={17} />

          <input
            id="maintenance-search"
            name="maintenance-search"
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search maintenance requests..."
          />
        </div>

        <span className="property-count">
          {filteredRequests.length} active
          {completedRequests.length > 0 &&
            ` · ${completedRequests.length} completed`}
        </span>
      </div>

      {!loading && error && (
        <div className="dashboard-card">
          <div className="empty-state">
            <h3>
              Unable to load maintenance
            </h3>

            <p>{error}</p>

            <button
              className="secondary-button"
              onClick={loadData}
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="dashboard-card">
          <div className="empty-state">
            <h3>
              Loading maintenance...
            </h3>
          </div>
        </div>
      )}

      {!loading &&
        !error &&
        filteredRequests.length === 0 &&
        completedRequests.length === 0 && (
          <div className="dashboard-card">
            <div className="empty-state">
              <div className="empty-icon">
                <Wrench size={21} />
              </div>

              <h3>
                No maintenance requests
              </h3>

              <p>
                {properties.length === 0
                  ? "Add a property before creating a maintenance request."
                  : "Create a maintenance request to start tracking work."}
              </p>

              {properties.length > 0 && (
                <button
                  className="primary-button"
                  onClick={openModal}
                >
                  <Plus size={17} />
                  Add request
                </button>
              )}
            </div>
          </div>
        )}

      {!loading &&
        !error &&
        filteredRequests.length > 0 && (
          <div className="maintenance-list">
            {filteredRequests.map(
              (request) => {
                const property =
                  getProperty(
                    request.property_id
                  )

                const externalWorkers =
                  getExternalWorkers(request)

                const selectedExternalWorker =
                  externalWorkers.find(
                    (worker) =>
                      worker.is_selected ===
                      true
                  )

                const isSearchingExternal =
                  searchingExternalWorker ===
                  request.id

                return (
                  <div
                    className={`maintenance-card priority-${request.priority}`}
                    key={request.id}
                  >
                    <div className="maintenance-card-main">
                      <div className="maintenance-icon">
                        <Wrench size={20} />
                      </div>

                      <div className="maintenance-content">
                        <div className="maintenance-top">
                          <h2>
                            {request.category ||
                              "Maintenance request"}
                          </h2>

                          <span
                            className={`priority-badge ${request.priority}`}
                          >
                            {request.priority}
                          </span>
                        </div>

                        <p className="maintenance-description">
                          {
                            request.description
                          }
                        </p>

                        <div className="maintenance-meta">
                          <span>
                            {property?.name ||
                              "Unknown property"}
                          </span>

                          <span>
                            {request.location ||
                              property?.address ||
                              "Location unavailable"}
                          </span>

                          <span>
                            {new Date(
                              request.created_at
                            ).toLocaleDateString()}
                          </span>
                        </div>

                        {!selectedExternalWorker && (
                          <div className="external-worker-search">
                            <div>
                              <div className="section-label">
                                Need an external contractor?
                              </div>

                              <p>
                                Search for suitable
                                contractors for this
                                maintenance request.
                              </p>
                            </div>

                            <button
                              type="button"
                              className="secondary-button"
                              onClick={() =>
                                searchExternalWorkers(
                                  request.id
                                )
                              }
                              disabled={
                                isSearchingExternal
                              }
                            >
                              <ExternalLink
                                size={16}
                              />

                              {isSearchingExternal
                                ? "Finding contractors..."
                                : "Find contractors"}
                            </button>
                          </div>
                        )}

                        {externalWorkers.length >
                          0 && (
                          <div className="external-worker-section">
                            <div className="external-worker-header">
                              <div>
                                <div className="external-worker-title-row">
                                  <span className="ai-assignment">
                                    <Sparkles
                                      size={13}
                                    />
                                    External contractors
                                  </span>

                                  <span className="external-worker-count">
                                    {externalWorkers.length}
                                  </span>
                                </div>

                                <h3>
                                  Recommended contractors
                                </h3>

                                <p>
                                  Contractors matched to this request.
                                  Those with public email addresses are
                                  contacted automatically.
                                </p>
                              </div>
                            </div>

                            {selectedExternalWorker ? (
                              <div className="external-worker-card selected">
                                <div className="external-worker-main">
                                  <div className="external-worker-card-header">
                                    <div className="external-worker-identity">
                                      <strong>
                                        {
                                          selectedExternalWorker.name
                                        }
                                      </strong>

                                      <span className="contractor-trade">
                                        {
                                          selectedExternalWorker.trade
                                        }
                                      </span>
                                    </div>

                                    <span className="selected-badge">
                                      <Check
                                        size={13}
                                      />
                                      Selected
                                    </span>
                                  </div>

                                  <div className="contractor-quick-info">
                                    {selectedExternalWorker.rating !=
                                      null && (
                                      <div className="contractor-stat">
                                        <Star
                                          size={14}
                                        />

                                        <div>
                                          <strong>
                                            {
                                              selectedExternalWorker.rating
                                            }
                                          </strong>

                                          {selectedExternalWorker.review_count !=
                                            null && (
                                            <span>
                                              {
                                                selectedExternalWorker.review_count
                                              }{" "}
                                              reviews
                                            </span>
                                          )}
                                        </div>
                                      </div>
                                    )}

                                    {selectedExternalWorker.availability && (
                                      <div className="contractor-stat">
                                        <Check
                                          size={14}
                                        />

                                        <div>
                                          <strong>
                                            Availability
                                          </strong>

                                          <span>
                                            {
                                              selectedExternalWorker.availability
                                            }
                                          </span>
                                        </div>
                                      </div>
                                    )}

                                    {selectedExternalWorker.location && (
                                      <div className="contractor-stat">
                                        <MapPin
                                          size={14}
                                        />

                                        <div>
                                          <strong>
                                            Location
                                          </strong>

                                          <span>
                                            {
                                              selectedExternalWorker.location
                                            }
                                          </span>
                                        </div>
                                      </div>
                                    )}
                                  </div>

                                  <div className="contractor-contact-row">
                                    {formatPhone(
                                      selectedExternalWorker.phone
                                    ) && (
                                      <span>
                                        <Phone
                                          size={14}
                                        />

                                        {
                                          selectedExternalWorker.phone
                                        }
                                      </span>
                                    )}

                                    {selectedExternalWorker.email && (
                                      <span>
                                        {
                                          selectedExternalWorker.email
                                        }
                                      </span>
                                    )}

                                    {selectedExternalWorker.website && (
                                      <a
                                        href={
                                          selectedExternalWorker.website
                                        }
                                        target="_blank"
                                        rel="noreferrer"
                                      >
                                        <ExternalLink
                                          size={14}
                                        />
                                        Website
                                      </a>
                                    )}
                                  </div>

                                  {selectedExternalWorker.match_score !=
                                    null && (
                                    <div className="contractor-match">
                                      <div className="contractor-match-top">
                                        <span>
                                          AI match score
                                        </span>

                                        <strong>
                                          {
                                            formatMatchScore(
                                              selectedExternalWorker.match_score
                                            )
                                          }
                                          %
                                        </strong>
                                      </div>

                                      <div className="match-bar">
                                        <div
                                          style={{
                                            width: `${formatMatchScore(
                                              selectedExternalWorker.match_score
                                            )}%`,
                                          }}
                                        />
                                      </div>
                                    </div>
                                  )}

                                  {selectedExternalWorker.match_reason && (
                                    <p className="match-reason">
                                      {
                                        selectedExternalWorker.match_reason
                                      }
                                    </p>
                                  )}

                                  <ContractorReplies
                                    requestId={request.id}
                                    worker={
                                      selectedExternalWorker
                                    }
                                    expandedReplies={
                                      expandedReplies
                                    }
                                    toggleReply={
                                      toggleReply
                                    }
                                    isReplyExpanded={
                                      isReplyExpanded
                                    }
                                    formatReplyDate={
                                      formatReplyDate
                                    }
                                    getReplyContent={
                                      getReplyContent
                                    }
                                  />
                                </div>
                              </div>
                            ) : (
                              <div className="external-worker-list">
                                {externalWorkers.map(
                                  (
                                    worker
                                  ) => {
                                    const workerKey =
                                      `${request.id}-${worker.id}`

                                    const isSelecting =
                                      selectingExternalWorker ===
                                      workerKey

                                    const matchScore =
                                      formatMatchScore(
                                        worker.match_score
                                      )

                                    return (
                                      <div
                                        className="external-worker-card"
                                        key={`${request.id}-${worker.provider}-${worker.external_id}`}
                                      >
                                        <div className="external-worker-main">
                                          <div className="external-worker-card-header">
                                            <div className="external-worker-identity">
                                              <strong>
                                                {
                                                  worker.name
                                                }
                                              </strong>

                                              <span className="contractor-trade">
                                                {
                                                  worker.trade
                                                }
                                              </span>
                                            </div>

                                            {matchScore !=
                                              null && (
                                              <div className="match-score-badge">
                                                <span>
                                                  Match
                                                </span>

                                                <strong>
                                                  {
                                                    matchScore
                                                  }
                                                  %
                                                </strong>
                                              </div>
                                            )}
                                          </div>

                                          <div className="contractor-quick-info">
                                            {worker.rating !=
                                              null && (
                                              <div className="contractor-stat">
                                                <Star
                                                  size={
                                                    14
                                                  }
                                                />

                                                <div>
                                                  <strong>
                                                    {
                                                      worker.rating
                                                    }
                                                  </strong>

                                                  {worker.review_count !=
                                                    null && (
                                                    <span>
                                                      {
                                                        worker.review_count
                                                      }{" "}
                                                      reviews
                                                    </span>
                                                  )}
                                                </div>
                                              </div>
                                            )}

                                            {worker.availability && (
                                              <div className="contractor-stat">
                                                <Check
                                                  size={
                                                    14
                                                  }
                                                />

                                                <div>
                                                  <strong>
                                                    Availability
                                                  </strong>

                                                  <span>
                                                    {
                                                      worker.availability
                                                    }
                                                  </span>
                                                </div>
                                              </div>
                                            )}

                                            {worker.location && (
                                              <div className="contractor-stat">
                                                <MapPin
                                                  size={
                                                    14
                                                  }
                                                />

                                                <div>
                                                  <strong>
                                                    Location
                                                  </strong>

                                                  <span>
                                                    {
                                                      worker.location
                                                    }
                                                  </span>
                                                </div>
                                              </div>
                                            )}
                                          </div>

                                          <div className="contractor-contact-row">
                                            {formatPhone(
                                              worker.phone
                                            ) && (
                                              <span>
                                                <Phone
                                                  size={
                                                    14
                                                  }
                                                />

                                                {
                                                  worker.phone
                                                }
                                              </span>
                                            )}

                                            {worker.email && (
                                              <span>
                                                {
                                                  worker.email
                                                }
                                              </span>
                                            )}

                                            {worker.website && (
                                              <a
                                                href={
                                                  worker.website
                                                }
                                                target="_blank"
                                                rel="noreferrer"
                                              >
                                                <ExternalLink
                                                  size={
                                                    14
                                                  }
                                                />
                                                Website
                                              </a>
                                            )}
                                          </div>

                                          {matchScore !=
                                            null && (
                                            <div className="contractor-match">
                                              <div className="contractor-match-top">
                                                <span>
                                                  AI match score
                                                </span>

                                                <strong>
                                                  {
                                                    matchScore
                                                  }
                                                  %
                                                </strong>
                                              </div>

                                              <div className="match-bar">
                                                <div
                                                  style={{
                                                    width: `${matchScore}%`,
                                                  }}
                                                />
                                              </div>
                                            </div>
                                          )}

                                          {worker.match_reason && (
                                            <p className="match-reason">
                                              {
                                                worker.match_reason
                                              }
                                            </p>
                                          )}

                                          <ContractorReplies
                                            requestId={
                                              request.id
                                            }
                                            worker={
                                              worker
                                            }
                                            expandedReplies={
                                              expandedReplies
                                            }
                                            toggleReply={
                                              toggleReply
                                            }
                                            isReplyExpanded={
                                              isReplyExpanded
                                            }
                                            formatReplyDate={
                                              formatReplyDate
                                            }
                                            getReplyContent={
                                              getReplyContent
                                            }
                                          />
                                        </div>

                                        <div className="external-worker-action">
                                          <button
                                            type="button"
                                            className="primary-button"
                                            disabled={
                                              isSelecting
                                            }
                                            onClick={() =>
                                              selectExternalWorker(
                                                request.id,
                                                worker.id
                                              )
                                            }
                                          >
                                            {isSelecting
                                              ? "Selecting..."
                                              : "Use contractor"}
                                          </button>
                                        </div>
                                      </div>
                                    )
                                  }
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="maintenance-controls">
                      <select
                        id={`status-${request.id}`}
                        name={`status-${request.id}`}
                        value={request.status}
                        onChange={(event) =>
                          updateRequest(
                            request.id,
                            {
                              status:
                                event.target
                                  .value,
                            }
                          )
                        }
                      >
                        {statuses.map(
                          (status) => (
                            <option
                              key={status}
                              value={status}
                            >
                              {formatStatus(
                                status
                              )}
                            </option>
                          )
                        )}
                      </select>

                      <select
                        id={`priority-${request.id}`}
                        name={`priority-${request.id}`}
                        value={
                          request.priority
                        }
                        onChange={(event) =>
                          updateRequest(
                            request.id,
                            {
                              priority:
                                event.target
                                  .value,
                            }
                          )
                        }
                      >
                        {priorities.map(
                          (priority) => (
                            <option
                              key={priority}
                              value={
                                priority
                              }
                            >
                              {priority}
                            </option>
                          )
                        )}
                      </select>

                      <button
                        className="property-action delete"
                        onClick={() =>
                          deleteRequest(
                            request
                          )
                        }
                        title="Delete maintenance request"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                )
              }
            )}
          </div>
        )}

      {completedRequests.length > 0 && (
        <div className="dashboard-card">
          <div className="empty-state">
            <h3>
              Completed maintenance
            </h3>

            <p>
              {completedRequests.length}{" "}
              {completedRequests.length === 1
                ? "request"
                : "requests"}{" "}
              completed
            </p>
          </div>

          <div className="maintenance-list">
            {completedRequests.map(
              (request) => {
                const property =
                  getProperty(
                    request.property_id
                  )

                return (
                  <div
                    className="maintenance-card"
                    key={request.id}
                  >
                    <div className="maintenance-card-main">
                      <div className="maintenance-icon">
                        <Wrench size={20} />
                      </div>

                      <div className="maintenance-content">
                        <div className="maintenance-top">
                          <h2>
                            {request.category ||
                              "Maintenance request"}
                          </h2>

                          <span className="priority-badge">
                            Completed
                          </span>
                        </div>

                        <p className="maintenance-description">
                          {
                            request.description
                          }
                        </p>

                        <div className="maintenance-meta">
                          <span>
                            {property?.name ||
                              "Unknown property"}
                          </span>

                          <span>
                            {request.location ||
                              property?.address ||
                              "Location unavailable"}
                          </span>

                          <span>
                            {new Date(
                              request.created_at
                            ).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="maintenance-controls">
                      <button
                        className="property-action delete"
                        onClick={() =>
                          deleteRequest(
                            request
                          )
                        }
                        title="Delete maintenance request"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                )
              }
            )}
          </div>
        </div>
      )}

      {showModal && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeModal()
            }
          }}
        >
          <div className="modal">
            <div className="modal-header">
              <div>
                <p className="eyebrow">
                  Operations
                </p>

                <h2>
                  Add maintenance request
                </h2>
              </div>

              <button
                type="button"
                className="icon-button"
                onClick={closeModal}
                disabled={saving}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <label>
                Property

                <select
                  id="maintenance-property"
                  name="maintenance-property"
                  value={propertyId}
                  onChange={(event) =>
                    setPropertyId(
                      event.target.value
                    )
                  }
                  disabled={saving}
                >
                  <option value="">
                    Select a property
                  </option>

                  {properties.map(
                    (property) => (
                      <option
                        key={property.id}
                        value={property.id}
                      >
                        {property.name}
                        {property.address
                          ? ` — ${property.address}`
                          : ""}
                      </option>
                    )
                  )}
                </select>
              </label>

              <label>
                Description

                <textarea
                  id="maintenance-description"
                  name="maintenance-description"
                  value={description}
                  onChange={(event) =>
                    setDescription(
                      event.target.value
                    )
                  }
                  placeholder="Describe the maintenance issue..."
                  disabled={saving}
                  rows={5}
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
                  onClick={closeModal}
                  disabled={saving}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-button"
                  disabled={saving}
                >
                  {saving
                    ? "Creating..."
                    : "Create request"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function ContractorReplies({
  requestId,
  worker,
  expandedReplies,
  toggleReply,
  isReplyExpanded,
  formatReplyDate,
  getReplyContent,
}) {
  const replies = Array.isArray(worker?.replies)
    ? worker.replies.filter(
        (reply) =>
          reply.direction === "inbound"
      )
    : []

  if (replies.length === 0) {
    return null
  }

  return (
    <div className="contractor-replies">
      <div className="contractor-replies-header">
        <div>
          <div className="section-label">
            Contractor replies
          </div>

          <p>
            {replies.length}{" "}
            {replies.length === 1
              ? "reply"
              : "replies"}{" "}
            received
          </p>
        </div>

        <div className="contractor-reply-count">
          <Mail size={14} />
          {replies.length}
        </div>
      </div>

      <div className="contractor-reply-list">
        {replies.map((reply, index) => {
          const replyId =
            reply.id ??
            reply.resend_message_id ??
            reply.message_id ??
            index

          const expanded =
            isReplyExpanded(
              requestId,
              worker.id,
              replyId
            )

          return (
            <div
              className="contractor-reply"
              key={replyId}
            >
              <button
                type="button"
                className="contractor-reply-toggle"
                onClick={() =>
                  toggleReply(
                    requestId,
                    worker.id,
                    replyId
                  )
                }
                aria-expanded={expanded}
              >
                <div className="contractor-reply-summary">
                  <Mail size={15} />

                  <div>
                    <strong>
                      {reply.sender_email ||
                        worker.email ||
                        "Contractor reply"}
                    </strong>

                    <span>
                      {reply.subject ||
                        "Reply received"}

                      {reply.received_at &&
                        ` · ${formatReplyDate(
                          reply.received_at
                        )}`}
                    </span>
                  </div>
                </div>

                {expanded ? (
                  <ChevronUp size={17} />
                ) : (
                  <ChevronDown size={17} />
                )}
              </button>

              {expanded && (
                <div className="contractor-reply-body">
                  {reply.subject && (
                    <div className="contractor-reply-subject">
                      <strong>
                        Subject
                      </strong>

                      <span>
                        {reply.subject}
                      </span>
                    </div>
                  )}

                  {reply.sender_email && (
                    <div className="contractor-reply-meta">
                      <strong>
                        From
                      </strong>

                      <span>
                        {reply.sender_email}
                      </span>
                    </div>
                  )}

                  {reply.recipient_email && (
                    <div className="contractor-reply-meta">
                      <strong>
                        To
                      </strong>

                      <span>
                        {reply.recipient_email}
                      </span>
                    </div>
                  )}

                  <div className="contractor-reply-content">
                    <pre>
                      {getReplyContent(reply)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}