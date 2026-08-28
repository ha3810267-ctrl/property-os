import { useEffect, useState } from "react"
import {
  Building2,
  Plus,
  Search,
  Pencil,
  Trash2,
  X,
} from "lucide-react"
import { apiRequest } from "../services/api"

export default function Properties() {
  const [properties, setProperties] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")

  const [showModal, setShowModal] = useState(false)
  const [editingProperty, setEditingProperty] = useState(null)

  const [name, setName] = useState("")
  const [address, setAddress] = useState("")
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState("")

  async function loadProperties() {
    try {
      setError("")

      const data = await apiRequest("/properties")

      setProperties(data)
    } catch (error) {
      console.error(error)
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProperties()
  }, [])

  function openAddModal() {
    setEditingProperty(null)
    setName("")
    setAddress("")
    setFormError("")
    setShowModal(true)
  }

  function openEditModal(property) {
    setEditingProperty(property)
    setName(property.name)
    setAddress(property.address)
    setFormError("")
    setShowModal(true)
  }

  function closeModal() {
    if (saving) return

    setShowModal(false)
    setEditingProperty(null)
    setName("")
    setAddress("")
    setFormError("")
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError("")

    if (!name.trim()) {
      setFormError("Property name is required")
      return
    }

    if (!address.trim()) {
      setFormError("Property address is required")
      return
    }

    setSaving(true)

    try {
      if (editingProperty) {
        const updatedProperty = await apiRequest(
          `/properties/${editingProperty.id}`,
          {
            method: "PUT",
            body: JSON.stringify({
              name: name.trim(),
              address: address.trim(),
            }),
          }
        )

        setProperties((current) =>
          current.map((property) =>
            property.id === updatedProperty.id
              ? updatedProperty
              : property
          )
        )
      } else {
        const newProperty = await apiRequest("/properties", {
          method: "POST",
          body: JSON.stringify({
            name: name.trim(),
            address: address.trim(),
          }),
        })

        setProperties((current) => [...current, newProperty])
      }

      closeModal()
    } catch (error) {
      console.error(error)
      setFormError(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(property) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${property.name}"?`
    )

    if (!confirmed) return

    try {
      await apiRequest(`/properties/${property.id}`, {
        method: "DELETE",
      })

      setProperties((current) =>
        current.filter((item) => item.id !== property.id)
      )
    } catch (error) {
      console.error(error)
      setError(error.message)
    }
  }

  const filteredProperties = properties.filter((property) => {
    const term = search.toLowerCase().trim()

    return (
      property.name.toLowerCase().includes(term) ||
      property.address.toLowerCase().includes(term)
    )
  })

  return (
    <div className="dashboard-page properties-page">
      <div className="properties-header">
        <div className="properties-title">
          <p className="eyebrow">Portfolio</p>

          <h1>Properties</h1>

          <p className="page-subtitle">
            Manage properties across your organisation
          </p>
        </div>

        <div className="properties-header-actions">
          <button
            className="primary-button"
            onClick={openAddModal}
          >
            <Plus size={17} />
            Add property
          </button>
        </div>
      </div>

      <div className="properties-toolbar">
        <div className="properties-search">
          <Search size={17} />

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search properties..."
          />
        </div>

        <span className="properties-count">
          {filteredProperties.length}{" "}
          {filteredProperties.length === 1
            ? "property"
            : "properties"}
        </span>
      </div>

      {!loading && error && (
        <div className="dashboard-card">
          <div className="empty-state">
            <h3>Unable to load properties</h3>

            <p>{error}</p>

            <button
              className="secondary-button"
              onClick={loadProperties}
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="dashboard-card">
          <div className="empty-state">
            <h3>Loading properties...</h3>
          </div>
        </div>
      )}

      {!loading &&
        !error &&
        filteredProperties.length === 0 && (
          <div className="dashboard-card">
            <div className="empty-state">
              <div className="empty-icon">
                <Building2 size={21} />
              </div>

              <h3>
                {properties.length === 0
                  ? "No properties yet"
                  : "No matching properties"}
              </h3>

              <p>
                {properties.length === 0
                  ? "Add your first property to start managing your portfolio."
                  : "Try a different search term."}
              </p>

              {properties.length === 0 && (
                <button
                  className="primary-button"
                  onClick={openAddModal}
                >
                  <Plus size={17} />
                  Add property
                </button>
              )}
            </div>
          </div>
        )}

      {!loading &&
        !error &&
        filteredProperties.length > 0 && (
          <div className="properties-grid">
            {filteredProperties.map((property) => (
              <div
                className="property-card"
                key={property.id}
              >
                <div className="property-card-top">
                  <div className="property-icon">
                    <Building2 size={20} />
                  </div>

                  <div className="property-actions">
                    <button
                      className="property-action"
                      onClick={() => openEditModal(property)}
                      title="Edit property"
                      aria-label={`Edit ${property.name}`}
                    >
                      <Pencil size={16} />
                    </button>

                    <button
                      className="property-action delete"
                      onClick={() => handleDelete(property)}
                      title="Delete property"
                      aria-label={`Delete ${property.name}`}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <h3>{property.name}</h3>

                <p>{property.address}</p>
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
                  {editingProperty ? "Property" : "Portfolio"}
                </p>

                <h2>
                  {editingProperty
                    ? "Edit property"
                    : "Add property"}
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
                Property name

                <input
                  value={name}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                  placeholder="e.g. 24 High Street"
                  disabled={saving}
                />
              </label>

              <label>
                Address

                <input
                  value={address}
                  onChange={(event) =>
                    setAddress(event.target.value)
                  }
                  placeholder="e.g. 24 High Street, Colchester"
                  disabled={saving}
                />
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
                    : editingProperty
                      ? "Save changes"
                      : "Create property"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}