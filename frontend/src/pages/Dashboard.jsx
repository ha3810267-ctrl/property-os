import {
  Building2,
  Users,
  Wrench,
  AlertTriangle,
  ArrowUpRight,
} from "lucide-react"

import { useEffect, useState } from "react"
import { apiRequest } from "../services/api"

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await apiRequest("/dashboard/stats")
        setStats(data)
      } catch (error) {
        console.error("Failed to load dashboard stats:", error)
      }
    }

    loadStats()
  }, [])

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Dashboard</h1>
          <p className="page-subtitle">
            Here’s what’s happening across your properties
          </p>
        </div>

        <button className="primary-button">
          + New maintenance request
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-top">
            <p>Properties</p>
            <Building2 size={18} />
          </div>
          <h2>{stats?.properties ?? "—"}</h2>
          <span>Total properties</span>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <p>Tenants</p>
            <Users size={18} />
          </div>
          <h2>{stats?.tenants ?? "—"}</h2>
          <span>Active tenants</span>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <p>Open maintenance</p>
            <Wrench size={18} />
          </div>
          <h2>{stats?.open_maintenance ?? "—"}</h2>
          <span>Requests needing attention</span>
        </div>

        <div className="stat-card">
          <div className="stat-card-top">
            <p>Urgent issues</p>
            <AlertTriangle size={18} />
          </div>
          <h2>{stats?.urgent_issues ?? "—"}</h2>
          <span>High priority requests</span>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-card">
          <div className="card-header">
            <div>
              <p className="eyebrow">Maintenance</p>
              <h2>Recent requests</h2>
            </div>

            <button className="text-button">
              View all <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="empty-state">
            <div className="empty-icon">
              <Wrench size={20} />
            </div>

            <h3>No recent requests</h3>

            <p>
              New maintenance requests will appear here when tenants report
              issues.
            </p>
          </div>
        </section>

        <section className="dashboard-card">
          <div className="card-header">
            <div>
              <p className="eyebrow">AI intelligence</p>
              <h2>Assignment activity</h2>
            </div>
          </div>

          <div className="ai-panel">
            <div className="ai-badge">AI</div>

            <div>
              <h3>Automatic task assignment</h3>

              <p>
                AI recommendations and manager overrides will appear here.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}