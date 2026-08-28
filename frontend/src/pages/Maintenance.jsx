import { useEffect, useState } from "react"
import {
  Wrench,
  Plus,
  Search,
  X,
  UserRound,
  Sparkles,
  Trash2,
  ExternalLink,
  Check,
  Mail,
  Clock,
  PoundSterling,
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
  const [tenants, setTenants] = useState([])
  const [properties, setProperties] = useState([])
  const [workers, setWorkers] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")

  const [showModal, setShowModal] = useState(false)
  const [description, setDescription] = useState("")
  const [tenantId, setTenantId] = useState("")
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState("")

  const [assigningId, setAssigningId] = useState(null)
  const [removingAssignment, setRemovingAssignment] = useState(null)

  const [searchingExternalWorker, setSearchingExternalWorker] =
    useState(null)

  const [selectingExternalWorker, setSelectingExternalWorker] =
    useState(null)

  const [contactingExternalWorker, setContactingExternalWorker] =
    useState(null)

  async function loadData() {
    try {
      setLoading(true)
      setError("")

      const [
        maintenanceData,
        tenantsData,
        propertiesData,
        usersData,
      ] = await Promise.all([
        apiRequest("/maintenance-requests"),
        apiRequest("/tenants"),
        apiRequest("/properties"),
        apiRequest("/users"),
      ])

      setRequests(
        Array.isArray(maintenanceData)
          ? maintenanceData
          : []
      )

      setTenants(
        Array.isArray(tenantsData)
          ? tenantsData
          : []
      )

      setProperties(
        Array.isArray(propertiesData)
          ? propertiesData
          : []
      )

      setWorkers(
        Array.isArray(usersData)
          ? usersData.filter(
              (user) =>
                user.role === "worker" &&
                user.is_active === true
            )
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

  function openModal() {
    setDescription("")
    setTenantId("")
    setFormError("")
    setShowModal(true)
  }

  function closeModal() {
    if (saving) return

    setShowModal(false)
    setDescription("")
    setTenantId("")
    setFormError("")
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError("")

    if (!description.trim()) {
      setFormError(
        "Maintenance description is required"
      )
      return
    }

    if (!tenantId) {
      setFormError(
        "Please select a tenant"
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
            tenant_id: Number(tenantId),
          }),
        }
      )

      setRequests((current) => [
        newRequest,
        ...current,
      ])

      setShowModal(false)
      setDescription("")
      setTenantId("")
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

  async function assignWorker(
    requestId,
    userId
  ) {
    if (!userId) return

    const numericUserId = Number(userId)

    try {
      setAssigningId(requestId)
      setError("")

      const updated = await apiRequest(
        `/maintenance-requests/${requestId}/assign`,
        {
          method: "POST",
          body: JSON.stringify({
            user_id: numericUserId,
          }),
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
          "Could not assign worker"
      )
    } finally {
      setAssigningId(null)
    }
  }

  async function removeAssignment(
    requestId,
    userId
  ) {
    const confirmed = window.confirm(
      "Remove this worker from the maintenance request?"
    )

    if (!confirmed) return

    const key = `${requestId}-${userId}`

    try {
      setRemovingAssignment(key)
      setError("")

      const updated = await apiRequest(
        `/maintenance-requests/${requestId}/assign/${userId}`,
        {
          method: "DELETE",
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
          "Could not remove worker assignment"
      )
    } finally {
      setRemovingAssignment(null)
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

  async function contactExternalWorker(
    requestId,
    candidateId
  ) {
    const key = `${requestId}-${candidateId}`

    try {
      setContactingExternalWorker(key)
      setError("")

      const updated = await apiRequest(
        `/maintenance-requests/${requestId}/external-workers/${candidateId}/contact`,
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
          "Could not contact external worker"
      )
    } finally {
      setContactingExternalWorker(null)
    }
  }

  function getTenant(tenantId) {
    return tenants.find(
      (tenant) => tenant.id === tenantId
    )
  }

  function getProperty(tenantId) {
    const tenant = getTenant(tenantId)

    if (!tenant) return null

    return properties.find(
      (property) =>
        property.id === tenant.property_id
    )
  }

  function getWorker(userId) {
    return workers.find(
      (worker) => worker.id === userId
    )
  }

  function getAssignments(request) {
    return Array.isArray(
      request.assignments
    )
      ? request.assignments
      : []
  }

  function getExternalWorkers(request) {
    return Array.isArray(
      request.external_workers
    )
      ? request.external_workers
      : []
  }

  function getWorkerName(assignment) {
    if (assignment.worker_name) {
      return assignment.worker_name
    }

    const worker = getWorker(
      assignment.user_id
    )

    if (worker?.name) {
      return worker.name
    }

    return `Worker #${assignment.user_id}`
  }

  function formatStatus(status) {
    if (!status) return ""

    return status
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      )
  }

  function formatContactStatus(status) {
    if (!status) return "Not contacted"

    if (status === "email_sent") {
      return "Email sent"
    }

    if (status === "contacted") {
      return "Contacted"
    }

    if (status === "email_failed") {
      return "Email failed"
    }

    if (status === "no_email") {
      return "No email available"
    }

    if (
      status === "response_received" ||
      status === "responded"
    ) {
      return "Response received"
    }

    return status.replaceAll("_", " ")
  }

  function formatResponseQuality(
    quality
  ) {
    if (!quality) return null

    if (quality === "good") {
      return "Good response"
    }

    if (quality === "poor") {
      return "Poor response"
    }

    if (quality === "unavailable") {
      return "Unavailable"
    }

    if (quality === "unclear") {
      return "Unclear response"
    }

    return quality
  }

  function formatPrice(price) {
    if (
      price === null ||
      price === undefined ||
      price === ""
    ) {
      return null
    }

    const numericPrice = Number(price)

    if (Number.isNaN(numericPrice)) {
      return null
    }

    return `£${numericPrice.toFixed(2)}`
  }

  const filteredRequests = requests.filter(
    (request) => {
      if (request.status === "completed") {
        return false
      }

      const tenant = getTenant(
        request.tenant_id
      )

      const property = getProperty(
        request.tenant_id
      )

      const assignments =
        getAssignments(request)

      const assignedWorkerNames =
        assignments
          .map((assignment) =>
            getWorkerName(assignment)
          )
          .join(" ")

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
        tenant?.name
          ?.toLowerCase()
          .includes(term) ||
        property?.name
          ?.toLowerCase()
          .includes(term) ||
        assignedWorkerNames
          .toLowerCase()
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
              tenants.length === 0
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
                {tenants.length === 0
                  ? "Add a tenant before creating a maintenance request."
                  : "Create a maintenance request to start tracking work."}
              </p>

              {tenants.length > 0 && (
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
                const tenant =
                  getTenant(
                    request.tenant_id
                  )

                const property =
                  getProperty(
                    request.tenant_id
                  )

                const assignments =
                  getAssignments(request)

                const externalWorkers =
                  getExternalWorkers(request)

                const assignedWorkerIds =
                  assignments.map(
                    (assignment) =>
                      assignment.user_id
                  )

                const availableWorkers =
                  workers.filter(
                    (worker) =>
                      !assignedWorkerIds.includes(
                        worker.id
                      )
                  )

                const selectedExternalWorker =
                  externalWorkers.find(
                    (worker) =>
                      worker.is_selected ===
                      true
                  )

                const hasInternalAssignment =
                  assignments.length > 0

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
                            {tenant?.name ||
                              "Unknown tenant"}
                          </span>

                          <span>
                            {property?.name ||
                              "Unknown property"}
                          </span>

                          <span>
                            {new Date(
                              request.created_at
                            ).toLocaleDateString()}
                          </span>
                        </div>

                        <div className="assignment-row">
                          <div className="assignment-info">
                            <UserRound
                              size={15}
                            />

                            {assignments.length ===
                            0 ? (
                              <span>
                                Unassigned
                              </span>
                            ) : (
                              <div className="assignment-list">
                                {assignments.map(
                                  (
                                    assignment
                                  ) => {
                                    const assignmentKey =
                                      `${request.id}-${assignment.user_id}`

                                    return (
                                      <div
                                        className="assignment-item"
                                        key={
                                          assignmentKey
                                        }
                                      >
                                        <div>
                                          <span>
                                            {getWorkerName(
                                              assignment
                                            )}
                                          </span>

                                          {assignment.assignment_method ===
                                            "ai" && (
                                            <span className="ai-assignment">
                                              <Sparkles
                                                size={
                                                  13
                                                }
                                              />
                                              AI assigned
                                              {assignment.score !=
                                                null &&
                                                ` · ${Math.round(
                                                  assignment.score *
                                                    100
                                                )}%`}
                                            </span>
                                          )}

                                          {assignment.assignment_method ===
                                            "manual" && (
                                            <span className="ai-assignment">
                                              Manual
                                            </span>
                                          )}
                                        </div>

                                        <button
                                          type="button"
                                          className="property-action delete"
                                          disabled={
                                            removingAssignment ===
                                            assignmentKey
                                          }
                                          onClick={() =>
                                            removeAssignment(
                                              request.id,
                                              assignment.user_id
                                            )
                                          }
                                          title="Remove worker"
                                        >
                                          <X
                                            size={
                                              14
                                            }
                                          />
                                        </button>
                                      </div>
                                    )
                                  }
                                )}
                              </div>
                            )}
                          </div>

                          <select
                            id={`worker-${request.id}`}
                            name={`worker-${request.id}`}
                            value=""
                            disabled={
                              assigningId ===
                                request.id ||
                              availableWorkers.length ===
                                0
                            }
                            onChange={(event) =>
                              assignWorker(
                                request.id,
                                event.target
                                  .value
                              )
                            }
                          >
                            <option value="">
                              {availableWorkers.length ===
                              0
                                ? "All workers assigned"
                                : "Add worker"}
                            </option>

                            {availableWorkers.map(
                              (worker) => (
                                <option
                                  key={
                                    worker.id
                                  }
                                  value={
                                    worker.id
                                  }
                                >
                                  {
                                    worker.name
                                  }
                                </option>
                              )
                            )}
                          </select>
                        </div>

                        {hasInternalAssignment &&
                          !selectedExternalWorker && (
                            <div className="external-worker-search">
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
                                  ? "Finding external workers..."
                                  : "Need an external worker?"}
                              </button>

                              <p>
                                Keep your current
                                worker assigned and
                                search for an external
                                provider as well
                              </p>
                            </div>
                          )}

                        {!hasInternalAssignment &&
                          externalWorkers.length ===
                            0 && (
                            <div className="external-worker-search">
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
                                  ? "Finding external workers..."
                                  : "Search external workers"}
                              </button>
                            </div>
                          )}

                        {externalWorkers.length >
                          0 && (
                          <div className="external-worker-section">
                            <div className="external-worker-header">
                              <div>
                                <span className="ai-assignment">
                                  <Sparkles
                                    size={13}
                                  />
                                  External match
                                </span>

                                <h3>
                                  Recommended external
                                  workers
                                </h3>

                                <p>
                                  {hasInternalAssignment
                                    ? "Your current worker remains assigned. Choose an external provider if additional help is needed."
                                    : "Choose the external provider you want to use for this request."}
                                </p>
                              </div>
                            </div>

                            {selectedExternalWorker ? (
                              <div className="external-worker-card selected">
                                <div>
                                  <strong>
                                    {
                                      selectedExternalWorker.name
                                    }
                                  </strong>

                                  <p>
                                    {
                                      selectedExternalWorker.trade
                                    }
                                    {" · "}
                                    {
                                      selectedExternalWorker.location
                                    }
                                  </p>

                                  {selectedExternalWorker.email && (
                                    <p>
                                      <Mail
                                        size={14}
                                      />
                                      {" "}
                                      {
                                        selectedExternalWorker.email
                                      }
                                    </p>
                                  )}

                                  <p>
                                    ⭐{" "}
                                    {
                                      selectedExternalWorker.rating
                                    }
                                    {" · "}
                                    {
                                      selectedExternalWorker.review_count
                                    }
                                    {" reviews"}
                                  </p>

                                  <p>
                                    {
                                      selectedExternalWorker.availability
                                    }
                                  </p>

                                  {selectedExternalWorker.match_score !=
                                    null && (
                                    <p className="ai-assignment">
                                      <Sparkles
                                        size={13}
                                      />
                                      Match score:{" "}
                                      {Math.round(
                                        Number(
                                          selectedExternalWorker.match_score
                                        ) *
                                          100
                                      )}
                                      %
                                    </p>
                                  )}

                                  {selectedExternalWorker.match_reason && (
                                    <p>
                                      {
                                        selectedExternalWorker.match_reason
                                      }
                                    </p>
                                  )}

                                  <div className="external-worker-contact-status">
                                    <Mail
                                      size={14}
                                    />

                                    <span>
                                      {formatContactStatus(
                                        selectedExternalWorker.contact_status
                                      )}
                                    </span>
                                  </div>

                                  {selectedExternalWorker.email_sent_at && (
                                    <p>
                                      Email sent{" "}
                                      {new Date(
                                        selectedExternalWorker.email_sent_at
                                      ).toLocaleString()}
                                    </p>
                                  )}
                                </div>

                                <div className="external-worker-provider">
                                  <span>
                                    {
                                      selectedExternalWorker.provider
                                    }
                                  </span>

                                  <Check
                                    size={15}
                                  />

                                  <button
                                    type="button"
                                    className="secondary-button"
                                    disabled
                                  >
                                    <Check
                                      size={15}
                                    />
                                    Selected
                                  </button>
                                </div>

                                <div className="external-worker-actions">
                                  {selectedExternalWorker.contact_status !==
                                    "email_sent" &&
                                    selectedExternalWorker.contact_status !==
                                      "response_received" &&
                                    selectedExternalWorker.contact_status !==
                                      "responded" && (
                                      <button
                                        type="button"
                                        className="primary-button"
                                        disabled={
                                          contactingExternalWorker ===
                                          `${request.id}-${selectedExternalWorker.id}`
                                        }
                                        onClick={() =>
                                          contactExternalWorker(
                                            request.id,
                                            selectedExternalWorker.id
                                          )
                                        }
                                      >
                                        <Mail
                                          size={
                                            15
                                          }
                                        />

                                        {contactingExternalWorker ===
                                        `${request.id}-${selectedExternalWorker.id}`
                                          ? "Sending..."
                                          : "Contact contractor"}
                                      </button>
                                    )}

                                  {(selectedExternalWorker.contact_status ===
                                    "email_sent" ||
                                    selectedExternalWorker.contact_status ===
                                      "response_received" ||
                                    selectedExternalWorker.contact_status ===
                                      "responded") && (
                                    <span className="ai-assignment">
                                      <Mail
                                        size={
                                          13
                                        }
                                      />
                                      Enquiry sent
                                    </span>
                                  )}
                                </div>

                                {selectedExternalWorker.response_received_at && (
                                  <div className="contractor-response">
                                    <div className="contractor-response-header">
                                      <div>
                                        <span className="ai-assignment">
                                          <Sparkles
                                            size={
                                              13
                                            }
                                          />
                                          AI response
                                          analysis
                                        </span>

                                        <h4>
                                          Contractor
                                          response
                                        </h4>
                                      </div>

                                      {selectedExternalWorker.response_quality && (
                                        <span
                                          className={`priority-badge ${selectedExternalWorker.response_quality}`}
                                        >
                                          {formatResponseQuality(
                                            selectedExternalWorker.response_quality
                                          )}
                                        </span>
                                      )}
                                    </div>

                                    {selectedExternalWorker.gemini_summary && (
                                      <p>
                                        {
                                          selectedExternalWorker.gemini_summary
                                        }
                                      </p>
                                    )}

                                    <div className="contractor-response-meta">
                                      {selectedExternalWorker.quoted_price !=
                                        null && (
                                        <span>
                                          <PoundSterling
                                            size={
                                              14
                                            }
                                          />
                                          Quote:{" "}
                                          <strong>
                                            {formatPrice(
                                              selectedExternalWorker.quoted_price
                                            )}
                                          </strong>
                                        </span>
                                      )}

                                      {selectedExternalWorker.estimated_start && (
                                        <span>
                                          <Clock
                                            size={
                                              14
                                            }
                                          />
                                          Start:{" "}
                                          {
                                            selectedExternalWorker.estimated_start
                                          }
                                        </span>
                                      )}

                                      {selectedExternalWorker.can_take_job ===
                                        true && (
                                        <span>
                                          <Check
                                            size={
                                              14
                                            }
                                          />
                                          Available
                                          for job
                                        </span>
                                      )}

                                      {selectedExternalWorker.can_take_job ===
                                        false && (
                                        <span>
                                          <X
                                            size={
                                              14
                                            }
                                          />
                                          Cannot take
                                          job
                                        </span>
                                      )}
                                    </div>

                                    {selectedExternalWorker.last_message && (
                                      <details>
                                        <summary>
                                          View contractor
                                          message
                                        </summary>

                                        <p>
                                          {
                                            selectedExternalWorker.last_message
                                          }
                                        </p>
                                      </details>
                                    )}
                                  </div>
                                )}
                              </div>
                            ) : (
                              <div className="external-worker-list">
                                {externalWorkers
                                  .slice(
                                    0,
                                    4
                                  )
                                  .map(
                                    (
                                      worker
                                    ) => {
                                      const workerKey =
                                        `${request.id}-${worker.id}`

                                      const isSelecting =
                                        selectingExternalWorker ===
                                        workerKey

                                      return (
                                        <div
                                          className="external-worker-card"
                                          key={`${request.id}-${worker.provider}-${worker.external_id}`}
                                        >
                                          <div>
                                            <strong>
                                              {
                                                worker.name
                                              }
                                            </strong>

                                            <p>
                                              {
                                                worker.trade
                                              }
                                              {" · "}
                                              {
                                                worker.location
                                              }
                                            </p>

                                            {worker.email && (
                                              <p>
                                                <Mail
                                                  size={14}
                                                />
                                                {" "}
                                                {
                                                  worker.email
                                                }
                                              </p>
                                            )}

                                            <p>
                                              ⭐{" "}
                                              {
                                                worker.rating
                                              }
                                              {" · "}
                                              {
                                                worker.review_count
                                              }
                                              {" reviews"}
                                            </p>

                                            <p>
                                              {
                                                worker.availability
                                              }
                                            </p>

                                            {worker.match_score !=
                                              null && (
                                              <p className="ai-assignment">
                                                <Sparkles
                                                  size={
                                                    13
                                                  }
                                                />
                                                Match
                                                score:{" "}
                                                {Math.round(
                                                  Number(
                                                    worker.match_score
                                                  ) *
                                                    100
                                                )}
                                                %
                                              </p>
                                            )}

                                            {worker.match_reason && (
                                              <p>
                                                {
                                                  worker.match_reason
                                                }
                                              </p>
                                            )}

                                            <div className="external-worker-contact-status">
                                              <Mail
                                                size={
                                                  14
                                                }
                                              />

                                              <span>
                                                {formatContactStatus(
                                                  worker.contact_status
                                                )}
                                              </span>
                                            </div>
                                          </div>

                                          <div className="external-worker-provider">
                                            <span>
                                              {
                                                worker.provider
                                              }
                                            </span>

                                            <ExternalLink
                                              size={
                                                15
                                              }
                                            />

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
                                                : "Use worker"}
                                            </button>
                                          </div>
                                        </div>
                                      )
                                    }
                                  )}
                              </div>
                            )}

                            {selectedExternalWorker && (
                              <div className="ai-assignment">
                                <Check
                                  size={13}
                                />
                                External provider
                                selected
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
                const tenant =
                  getTenant(
                    request.tenant_id
                  )

                const property =
                  getProperty(
                    request.tenant_id
                  )

                const assignments =
                  getAssignments(request)

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
                            {tenant?.name ||
                              "Unknown tenant"}
                          </span>

                          <span>
                            {property?.name ||
                              "Unknown property"}
                          </span>

                          <span>
                            {assignments.length >
                            0
                              ? assignments
                                  .map(
                                    (
                                      assignment
                                    ) =>
                                      getWorkerName(
                                        assignment
                                      )
                                  )
                                  .join(
                                    ", "
                                  )
                              : "Completed"}
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
                Tenant

                <select
                  id="maintenance-tenant"
                  name="maintenance-tenant"
                  value={tenantId}
                  onChange={(event) =>
                    setTenantId(
                      event.target.value
                    )
                  }
                  disabled={saving}
                >
                  <option value="">
                    Select a tenant
                  </option>

                  {tenants.map(
                    (tenant) => {
                      const property =
                        getProperty(
                          tenant.id
                        )

                      return (
                        <option
                          key={tenant.id}
                          value={
                            tenant.id
                          }
                        >
                          {tenant.name}
                          {property
                            ? ` — ${property.name}`
                            : ""}
                        </option>
                      )
                    }
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