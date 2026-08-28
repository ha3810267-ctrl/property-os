import { useEffect, useState } from "react"
import {
  Users,
  Plus,
  Search,
  Pencil,
  Trash2,
  X,
} from "lucide-react"
import { apiRequest } from "../services/api"

export default function Tenants() {
  const [tenants, setTenants] = useState([])
  const [properties, setProperties] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")

  const [showModal, setShowModal] = useState(false)
  const [editingTenant, setEditingTenant] = useState(null)

  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [propertyId, setPropertyId] = useState("")

  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState("")

  async function loadData() {
    try {
      setLoading(true)
      setError("")

      const [tenantData, propertyData] = await Promise.all([
        apiRequest("/tenants"),
        apiRequest("/properties"),
      ])

      setTenants(tenantData)
      setProperties(propertyData)
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

  function getPropertyName(propertyId) {
    const property = properties.find(
      (item) => item.id === propertyId
    )

    return property?.name || "Unknown property"
  }

  function openAddModal() {
    setEditingTenant(null)
    setName("")
    setEmail("")
    setPropertyId(properties[0]?.id?.toString() || "")
    setFormError("")
    setShowModal(true)
  }

  function openEditModal(tenant) {
    setEditingTenant(tenant)
    setName(tenant.name)
    setEmail(tenant.email)
    setPropertyId(tenant.property_id.toString())
    setFormError("")
    setShowModal(true)
  }

  function closeModal() {
    if (saving) return

    setShowModal(false)
    setEditingTenant(null)
    setName("")
    setEmail("")
    setPropertyId("")
    setFormError("")
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError("")

    if (!name.trim()) {
      setFormError("Tenant name is required")
      return
    }

    if (!email.trim()) {
      setFormError("Tenant email is required")
      return
    }

    if (!propertyId) {
      setFormError("Property is required")
      return
    }

    setSaving(true)

    try {
      const payload = {
        name: name.trim(),
        email: email.trim(),
        property_id: Number(propertyId),
      }

      if (editingTenant) {
        const updatedTenant = await apiRequest(
          `/tenants/${editingTenant.id}`,
          {
            method: "PUT",
            body: JSON.stringify(payload),
          }
        )

        setTenants((current) =>
          current.map((tenant) =>
            tenant.id === updatedTenant.id
              ? updatedTenant
              : tenant
          )
        )
      } else {
        const newTenant = await apiRequest("/tenants", {
          method: "POST",
          body: JSON.stringify(payload),
        })

        setTenants((current) => [...current, newTenant])
      }

      closeModal()
    } catch (error) {
      console.error(error)
      setFormError(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(tenant) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${tenant.name}"?`
    )

    if (!confirmed) return

    try {
      await apiRequest(`/tenants/${tenant.id}`, {
        method: "DELETE",
      })

      setTenants((current) =>
        current.filter((item) => item.id !== tenant.id)
      )
    } catch (error) {
      console.error(error)
      setError(error.message)
    }
  }

  const filteredTenants = tenants.filter((tenant) => {
    const term = search.toLowerCase().trim()

    return (
      tenant.name.toLowerCase().includes(term) ||
      tenant.email.toLowerCase().includes(term) ||
      String(tenant.id).includes(term) ||
      getPropertyName(tenant.property_id)
        .toLowerCase()
        .includes(term)
    )
  })

  return (
    <div className="dashboard-page properties-page">
      <div className="properties-header">
        <div className="properties-title">
          <p className="eyebrow">Portfolio</p>

          <h1>Tenants</h1>

          <p className="page-subtitle">
            Manage tenants across your properties
          </p>
        </div>

        <div className="properties-header-actions">
          <button
            className="primary-button"
            onClick={openAddModal}
            disabled={properties.length === 0}
          >
            <Plus size={17} />
            Add tenant
          </button>
        </div>
      </div>

      <div className="properties-toolbar">
        <div className="properties-search">
          <Search size={17} />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search tenants..."
          />
        </div>

        <span className="properties-count">
          {filteredTenants.length}{" "}
          {filteredTenants.length === 1 ? "tenant" : "tenants"}
        </span>
      </div>

      {!loading && error && (
        <div className="dashboard-card">
          <div className="empty-state">
            <h3>Unable to load tenants</h3>

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
            <h3>Loading tenants...</h3>
          </div>
        </div>
      )}

      {!loading &&
        !error &&
        filteredTenants.length === 0 && (
          <div className="dashboard-card">
            <div className="empty-state">
              <div className="empty-icon">
                <Users size={21} />
              </div>

              <h3>
                {tenants.length === 0
                  ? "No tenants yet"
                  : "No matching tenants"}
              </h3>

              <p>
                {tenants.length === 0
                  ? properties.length === 0
                    ? "Create a property before adding your first tenant."
                    : "Add your first tenant to start managing your residents."
                  : "Try a different search term."}
              </p>

              {tenants.length === 0 && properties.length > 0 && (
                <button
                  className="primary-button"
                  onClick={openAddModal}
                >
                  <Plus size={17} />
                  Add tenant
                </button>
              )}
            </div>
          </div>
        )}

      {!loading &&
        !error &&
        filteredTenants.length > 0 && (
          <div className="properties-grid">
            {filteredTenants.map((tenant) => (
              <div
                className="property-card"
                key={tenant.id}
              >
                <div className="property-card-top">
                  <div className="property-icon">
                    <Users size={20} />
                  </div>

                  <div className="property-actions">
                    <button
                      className="property-action"
                      onClick={() => openEditModal(tenant)}
                      title="Edit tenant"
                      aria-label={`Edit ${tenant.name}`}
                    >
                      <Pencil size={16} />
                    </button>

                    <button
                      className="property-action delete"
                      onClick={() => handleDelete(tenant)}
                      title="Delete tenant"
                      aria-label={`Delete ${tenant.name}`}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <h3>{tenant.name}</h3>

                <p>{tenant.email}</p>

                <p>{getPropertyName(tenant.property_id)}</p>

                <p>
                  <strong>Tenant ID:</strong> {tenant.id}
                </p>
              </div>
            ))}
          </div>
        )}

      {showModal && (
        <div
          className="modal-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeModal()
            }
          }}
        >
          <div className="modal">
            <div className="modal-header">
              <div>
                <p className="eyebrow">
                  {editingTenant ? "Tenant" : "Portfolio"}
                </p>

                <h2>
                  {editingTenant
                    ? "Edit tenant"
                    : "Add tenant"}
                </h2>
              </div>

              <button
                className="property-action"
                onClick={closeModal}
                disabled={saving}
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <label>
                Tenant name

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
                Property

                <select
                  value={propertyId}
                  onChange={(event) =>
                    setPropertyId(event.target.value)
                  }
                  disabled={saving}
                >
                  <option value="">Select a property</option>

                  {properties.map((property) => (
                    <option
                      key={property.id}
                      value={property.id}
                    >
                      {property.name}
                    </option>
                  ))}
                </select>
              </label>

              {formError && (
                <p className="form-error">{formError}</p>
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
                    ? "Saving..."
                    : editingTenant
                      ? "Save changes"
                      : "Create tenant"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}