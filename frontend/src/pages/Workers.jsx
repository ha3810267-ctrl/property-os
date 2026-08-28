import { useEffect, useState } from "react"
import {
  Users,
  Plus,
  Search,
  Pencil,
  Trash2,
  X,
  Mail,
} from "lucide-react"
import { apiRequest } from "../services/api"

export default function Workers() {
  const [workers, setWorkers] = useState([])
  const [providers, setProviders] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")

  const [showMenu, setShowMenu] = useState(false)
  const [showWorkerModal, setShowWorkerModal] =
    useState(false)
  const [showProviderModal, setShowProviderModal] =
    useState(false)

  const [editingWorker, setEditingWorker] =
    useState(null)

  const [editingProvider, setEditingProvider] =
    useState(null)

  // Internal worker fields
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [speciality, setSpeciality] = useState("")

  // Service provider fields
  const [providerName, setProviderName] =
    useState("")
  const [businessName, setBusinessName] =
    useState("")
  const [providerEmail, setProviderEmail] =
    useState("")
  const [phone, setPhone] = useState("")
  const [providerSpeciality, setProviderSpeciality] =
    useState("")
  const [serviceArea, setServiceArea] =
    useState("")

  const [saving, setSaving] = useState(false)
  const [sending, setSending] = useState(null)
  const [formError, setFormError] = useState("")
  const [success, setSuccess] = useState("")

  const [invitedProviders, setInvitedProviders] =
    useState([])

  async function loadData() {
    try {
      setLoading(true)
      setError("")

      const [workerData, providerData] =
        await Promise.all([
          apiRequest("/workers"),
          apiRequest("/service-providers"),
        ])

      setWorkers(
        workerData.filter(
          (worker) => worker.is_active
        )
      )

      setProviders(
        providerData.filter(
          (provider) => provider.is_active
        )
      )
    } catch (error) {
      console.error(error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  function openAddMenu() {
    setShowMenu((current) => !current)
  }

  function openAddWorkerModal() {
    setShowMenu(false)
    setEditingWorker(null)

    setName("")
    setEmail("")
    setPassword("")
    setSpeciality("")
    setFormError("")
    setSuccess("")

    setShowWorkerModal(true)
  }

  function openEditWorkerModal(worker) {
    setEditingWorker(worker)

    setName(worker.name)
    setEmail(worker.email)
    setPassword("")
    setSpeciality(worker.speciality || "")

    setFormError("")
    setSuccess("")
    setShowWorkerModal(true)
  }

  function openAddProviderModal() {
    setShowMenu(false)
    setEditingProvider(null)

    setProviderName("")
    setBusinessName("")
    setProviderEmail("")
    setPhone("")
    setProviderSpeciality("")
    setServiceArea("")

    setFormError("")
    setSuccess("")
    setShowProviderModal(true)
  }

  function openEditProviderModal(provider) {
    setEditingProvider(provider)

    setProviderName(provider.name || "")
    setBusinessName(provider.business_name || "")
    setProviderEmail(provider.email || "")
    setPhone(provider.phone || "")
    setProviderSpeciality(
      provider.speciality || ""
    )
    setServiceArea(
      provider.service_area || ""
    )

    setFormError("")
    setSuccess("")
    setShowProviderModal(true)
  }

  function closeWorkerModal() {
    if (saving) return

    setShowWorkerModal(false)
    setEditingWorker(null)

    setName("")
    setEmail("")
    setPassword("")
    setSpeciality("")
    setFormError("")
  }

  function closeProviderModal() {
    if (saving) return

    setShowProviderModal(false)
    setEditingProvider(null)

    setProviderName("")
    setBusinessName("")
    setProviderEmail("")
    setPhone("")
    setProviderSpeciality("")
    setServiceArea("")
    setFormError("")
  }

  async function handleWorkerSubmit(event) {
    event.preventDefault()
    setFormError("")
    setSuccess("")

    if (!name.trim()) {
      setFormError("Worker name is required")
      return
    }

    if (!email.trim()) {
      setFormError("Worker email is required")
      return
    }

    if (!editingWorker && !password) {
      setFormError("Password is required")
      return
    }

    if (!speciality.trim()) {
      setFormError("Worker speciality is required")
      return
    }

    setSaving(true)

    try {
      if (editingWorker) {
        const updatedWorker = await apiRequest(
          `/users/${editingWorker.id}`,
          {
            method: "PUT",
            body: JSON.stringify({
              name: name.trim(),
              email: email.trim(),
              speciality: speciality.trim(),
              ...(password
                ? { password }
                : {}),
            }),
          }
        )

        if (updatedWorker.is_active) {
          setWorkers((current) =>
            current.map((worker) =>
              worker.id === updatedWorker.id
                ? updatedWorker
                : worker
            )
          )
        } else {
          setWorkers((current) =>
            current.filter(
              (worker) =>
                worker.id !== updatedWorker.id
            )
          )
        }
      } else {
        const newWorker = await apiRequest(
          "/users",
          {
            method: "POST",
            body: JSON.stringify({
              name: name.trim(),
              email: email.trim(),
              password,
              role: "worker",
              speciality: speciality.trim(),
            }),
          }
        )

        if (newWorker.is_active) {
          setWorkers((current) => [
            ...current,
            newWorker,
          ])
        }
      }

      closeWorkerModal()
    } catch (error) {
      console.error(error)
      setFormError(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleProviderSubmit(event) {
    event.preventDefault()
    setFormError("")
    setSuccess("")

    if (!providerName.trim()) {
      setFormError(
        "Service provider name is required"
      )
      return
    }

    if (!providerEmail.trim()) {
      setFormError(
        "Service provider email is required"
      )
      return
    }

    if (!providerSpeciality.trim()) {
      setFormError(
        "Service provider speciality is required"
      )
      return
    }

    setSaving(true)

    try {
      if (editingProvider) {
        const updatedProvider = await apiRequest(
          `/service-providers/${editingProvider.id}`,
          {
            method: "PUT",
            body: JSON.stringify({
              name: providerName.trim(),
              business_name:
                businessName.trim() || null,
              email: providerEmail.trim(),
              phone: phone.trim() || null,
              speciality:
                providerSpeciality.trim(),
              service_area:
                serviceArea.trim() || null,
            }),
          }
        )

        if (updatedProvider.is_active) {
          setProviders((current) =>
            current.map((provider) =>
              provider.id ===
              updatedProvider.id
                ? updatedProvider
                : provider
            )
          )
        } else {
          setProviders((current) =>
            current.filter(
              (provider) =>
                provider.id !==
                updatedProvider.id
            )
          )
        }

        setSuccess(
          `${updatedProvider.name} was updated successfully`
        )
      } else {
        const newProvider = await apiRequest(
          "/service-providers",
          {
            method: "POST",
            body: JSON.stringify({
              name: providerName.trim(),
              business_name:
                businessName.trim() || null,
              email: providerEmail.trim(),
              phone: phone.trim() || null,
              speciality:
                providerSpeciality.trim(),
              service_area:
                serviceArea.trim() || null,
            }),
          }
        )

        setProviders((current) => [
          ...current,
          newProvider,
        ])

        setSuccess(
          `${newProvider.name} was added as a service provider`
        )
      }

      closeProviderModal()
    } catch (error) {
      console.error(error)
      setFormError(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function sendInvitation(provider) {
    setSending(provider.id)
    setError("")
    setSuccess("")

    try {
      await apiRequest(
        "/service-provider-invitations",
        {
          method: "POST",
          body: JSON.stringify({
            service_provider_id:
              provider.id,
          }),
        }
      )

      setInvitedProviders((current) => [
        ...current,
        provider.id,
      ])

      setSuccess(
        `Invitation sent to ${provider.email}`
      )
    } catch (error) {
      console.error(error)
      setError(error.message)
    } finally {
      setSending(null)
    }
  }

  async function handleDelete(worker) {
    const confirmed = window.confirm(
      `Are you sure you want to deactivate "${worker.name}"?`
    )

    if (!confirmed) return

    try {
      await apiRequest(
        `/users/${worker.id}`,
        {
          method: "DELETE",
        }
      )

      setWorkers((current) =>
        current.filter(
          (item) => item.id !== worker.id
        )
      )
    } catch (error) {
      console.error(error)
      setError(error.message)
    }
  }

  async function handleDeleteProvider(provider) {
    const confirmed = window.confirm(
      `Are you sure you want to deactivate "${provider.name}"?`
    )

    if (!confirmed) return

    try {
      await apiRequest(
        `/service-providers/${provider.id}`,
        {
          method: "DELETE",
        }
      )

      setProviders((current) =>
        current.filter(
          (item) => item.id !== provider.id
        )
      )

      setSuccess(
        `${provider.name} was deactivated successfully`
      )
    } catch (error) {
      console.error(error)
      setError(error.message)
    }
  }

  const filteredWorkers = workers.filter(
    (worker) => {
      const term = search.toLowerCase()

      return (
        worker.name
          ?.toLowerCase()
          .includes(term) ||
        worker.email
          ?.toLowerCase()
          .includes(term) ||
        worker.speciality
          ?.toLowerCase()
          .includes(term)
      )
    }
  )

  const filteredProviders = providers.filter(
    (provider) => {
      const term = search.toLowerCase()

      return (
        provider.name
          ?.toLowerCase()
          .includes(term) ||
        provider.business_name
          ?.toLowerCase()
          .includes(term) ||
        provider.email
          ?.toLowerCase()
          .includes(term) ||
        provider.speciality
          ?.toLowerCase()
          .includes(term) ||
        provider.service_area
          ?.toLowerCase()
          .includes(term)
      )
    }
  )

  return (
    <div className="dashboard-page properties-page">
      <div className="properties-header">
        <div className="properties-title">
          <p className="eyebrow">
            Operations
          </p>

          <h1>Workers</h1>

          <p className="page-subtitle">
            Manage internal workers and external
            service providers
          </p>
        </div>

        <div
          className="properties-header-actions"
          style={{
            position: "relative",
          }}
        >
          <button
            className="primary-button"
            onClick={openAddMenu}
          >
            <Plus size={17} />
            Add
          </button>

          {showMenu && (
            <div
              className="dashboard-card"
              style={{
                position: "absolute",
                right: 0,
                top: "calc(100% + 8px)",
                width: 220,
                zIndex: 20,
                padding: 8,
              }}
            >
              <button
                className="secondary-button"
                style={{
                  width: "100%",
                  marginBottom: 8,
                }}
                onClick={openAddWorkerModal}
              >
                <Users size={16} />
                Add worker
              </button>

              <button
                className="secondary-button"
                style={{
                  width: "100%",
                }}
                onClick={openAddProviderModal}
              >
                <Mail size={16} />
                Add service provider
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="properties-toolbar">
        <div className="properties-search">
          <Search size={17} />

          <input
            value={search}
            onChange={(event) =>
              setSearch(event.target.value)
            }
            placeholder="Search workers and providers..."
          />
        </div>

        <span className="properties-count">
          {workers.length + providers.length}{" "}
          {workers.length + providers.length === 1
            ? "person"
            : "people"}
        </span>
      </div>

      {success && (
        <div className="dashboard-card">
          <div className="empty-state">
            <p>{success}</p>
          </div>
        </div>
      )}

      {!loading && error && (
        <div className="dashboard-card">
          <div className="empty-state">
            <h3>Unable to load workers</h3>

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
            <h3>Loading workers...</h3>
          </div>
        </div>
      )}

      {!loading &&
        !error &&
        filteredWorkers.length === 0 &&
        filteredProviders.length === 0 && (
          <div className="dashboard-card">
            <div className="empty-state">
              <div className="empty-icon">
                <Users size={21} />
              </div>

              <h3>
                No workers or providers yet
              </h3>

              <p>
                Add an internal worker or service
                provider to get started.
              </p>

              <button
                className="primary-button"
                onClick={openAddMenu}
              >
                <Plus size={17} />
                Add
              </button>
            </div>
          </div>
        )}

      {!loading &&
        !error &&
        filteredWorkers.length > 0 && (
          <>
            <div
              className="properties-title"
              style={{ marginBottom: 16 }}
            >
              <p className="eyebrow">
                Internal
              </p>

              <h2>Workers</h2>
            </div>

            <div className="properties-grid">
              {filteredWorkers.map((worker) => (
                <div
                  className="property-card"
                  key={`worker-${worker.id}`}
                >
                  <div className="property-card-top">
                    <div className="property-icon">
                      <Users size={20} />
                    </div>

                    <div className="property-actions">
                      <button
                        className="property-action"
                        onClick={() =>
                          openEditWorkerModal(
                            worker
                          )
                        }
                        title="Edit worker"
                      >
                        <Pencil size={16} />
                      </button>

                      <button
                        className="property-action delete"
                        onClick={() =>
                          handleDelete(worker)
                        }
                        title="Deactivate worker"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  <h3>{worker.name}</h3>

                  <p>{worker.email}</p>

                  <p>
                    <strong>
                      Speciality:
                    </strong>{" "}
                    {worker.speciality ||
                      "Not specified"}
                  </p>

                  <p>
                    <strong>Status:</strong>{" "}
                    Active
                  </p>
                </div>
              ))}
            </div>
          </>
        )}

      {!loading &&
        !error &&
        filteredProviders.length > 0 && (
          <>
            <div
              className="properties-title"
              style={{
                marginTop: 32,
                marginBottom: 16,
              }}
            >
              <p className="eyebrow">
                External
              </p>

              <h2>Service providers</h2>
            </div>

            <div className="properties-grid">
              {filteredProviders.map(
                (provider) => {
                  const invited =
                    invitedProviders.includes(
                      provider.id
                    )

                  const connected =
                    Boolean(
                      provider.user_id
                    )

                  return (
                    <div
                      className="property-card"
                      key={`provider-${provider.id}`}
                    >
                      <div className="property-card-top">
                        <div className="property-icon">
                          <Users size={20} />
                        </div>

                        <div className="property-actions">
                          <button
                            className="property-action"
                            onClick={() =>
                              openEditProviderModal(
                                provider
                              )
                            }
                            title="Edit service provider"
                          >
                            <Pencil size={16} />
                          </button>

                          <button
                            className="property-action delete"
                            onClick={() =>
                              handleDeleteProvider(
                                provider
                              )
                            }
                            title="Deactivate service provider"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>

                      <h3>
                        {provider.name}
                      </h3>

                      <p>
                        {provider.business_name ||
                          "No business name"}
                      </p>

                      <p>
                        {provider.email}
                      </p>

                      <p>
                        <strong>
                          Speciality:
                        </strong>{" "}
                        {provider.speciality ||
                          "Not specified"}
                      </p>

                      <p>
                        <strong>
                          Area:
                        </strong>{" "}
                        {provider.service_area ||
                          "Not specified"}
                      </p>

                      <p>
                        <strong>
                          Status:
                        </strong>{" "}
                        {connected
                          ? "Connected"
                          : invited
                            ? "Invitation sent"
                            : "Not invited"}
                      </p>

                      {!connected && (
                        <div className="modal-actions">
                          <button
                            className={
                              invited
                                ? "secondary-button"
                                : "primary-button"
                            }
                            disabled={
                              sending ===
                                provider.id ||
                              invited
                            }
                            onClick={() =>
                              sendInvitation(
                                provider
                              )
                            }
                          >
                            <Mail size={16} />

                            {sending ===
                            provider.id
                              ? "Sending..."
                              : invited
                                ? "Invitation sent"
                                : "Send invitation"}
                          </button>
                        </div>
                      )}
                    </div>
                  )
                }
              )}
            </div>
          </>
        )}

      {showWorkerModal && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target === event.currentTarget
            ) {
              closeWorkerModal()
            }
          }}
        >
          <div className="modal">
            <div className="modal-header">
              <div>
                <p className="eyebrow">
                  Internal
                </p>

                <h2>
                  {editingWorker
                    ? "Edit worker"
                    : "Add worker"}
                </h2>
              </div>

              <button
                className="property-action"
                onClick={closeWorkerModal}
                disabled={saving}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleWorkerSubmit}>
              <label>
                Worker name

                <input
                  value={name}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                  placeholder="e.g. John Smith"
                  disabled={saving}
                />
              </label>

              <label>
                Email

                <input
                  type="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  placeholder="e.g. john@example.com"
                  disabled={saving}
                />
              </label>

              <label>
                Password

                <input
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(
                      event.target.value
                    )
                  }
                  placeholder={
                    editingWorker
                      ? "Leave blank to keep current password"
                      : "Enter password"
                  }
                  disabled={saving}
                />
              </label>

              <label>
                Speciality

                <input
                  value={speciality}
                  onChange={(event) =>
                    setSpeciality(
                      event.target.value
                    )
                  }
                  placeholder="e.g. plumbing, electrical"
                  disabled={saving}
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
                  onClick={closeWorkerModal}
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
                    ? "Saving..."
                    : editingWorker
                      ? "Save changes"
                      : "Create worker"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showProviderModal && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (
              event.target === event.currentTarget
            ) {
              closeProviderModal()
            }
          }}
        >
          <div
            className="modal"
            style={{
              maxHeight: "90vh",
              overflowY: "auto",
            }}
          >
            <div className="modal-header">
              <div>
                <p className="eyebrow">
                  External
                </p>

                <h2>
                  {editingProvider
                    ? "Edit service provider"
                    : "Add service provider"}
                </h2>
              </div>

              <button
                className="property-action"
                onClick={closeProviderModal}
                disabled={saving}
              >
                <X size={18} />
              </button>
            </div>

            <form
              onSubmit={handleProviderSubmit}
            >
              <label>
                Provider name

                <input
                  value={providerName}
                  onChange={(event) =>
                    setProviderName(
                      event.target.value
                    )
                  }
                  placeholder="e.g. John Smith"
                  disabled={saving}
                />
              </label>

              <label>
                Business name

                <input
                  value={businessName}
                  onChange={(event) =>
                    setBusinessName(
                      event.target.value
                    )
                  }
                  placeholder="e.g. Smith Plumbing"
                  disabled={saving}
                />
              </label>

              <label>
                Email

                <input
                  type="email"
                  value={providerEmail}
                  onChange={(event) =>
                    setProviderEmail(
                      event.target.value
                    )
                  }
                  placeholder="e.g. john@example.com"
                  disabled={saving}
                />
              </label>

              <label>
                Phone

                <input
                  value={phone}
                  onChange={(event) =>
                    setPhone(
                      event.target.value
                    )
                  }
                  placeholder="e.g. 07700 900000"
                  disabled={saving}
                />
              </label>

              <label>
                Speciality

                <input
                  value={providerSpeciality}
                  onChange={(event) =>
                    setProviderSpeciality(
                      event.target.value
                    )
                  }
                  placeholder="e.g. plumbing"
                  disabled={saving}
                />
              </label>

              <label>
                Service area

                <input
                  value={serviceArea}
                  onChange={(event) =>
                    setServiceArea(
                      event.target.value
                    )
                  }
                  placeholder="e.g. Colchester"
                  disabled={saving}
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
                  onClick={closeProviderModal}
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
                    ? "Saving..."
                    : editingProvider
                      ? "Save changes"
                      : "Add provider"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}