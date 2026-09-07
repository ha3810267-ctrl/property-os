import { Link } from "react-router-dom"
import {
  ArrowRight,
  Sparkles,
  Building2,
  Users,
  Wrench,
  Brain,
  CheckCircle2,
  BarChart3,
  ShieldCheck,
} from "lucide-react"
import "./Landing.css"

export default function Landing() {
  return (
    <div className="landing-page">

      {/* NAVBAR */}
      <header className="landing-nav">
        <Link to="/" className="landing-brand">
          <div className="landing-brand-mark">P</div>
          <span>PropertyOS</span>
        </Link>

        <nav className="landing-nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>
          <a href="#tenants">For tenants</a>
        </nav>

        <div className="landing-nav-actions">
          <Link to="/login" className="landing-login">
            Log in
          </Link>

          <Link to="/login" className="landing-nav-cta">
            Get started
            <ArrowRight size={16} />
          </Link>
        </div>
      </header>


      {/* HERO */}
      <main>

        <section className="hero-section">
          <div className="hero-content">

            <div className="hero-badge">
              <Sparkles size={15} />
              AI-powered property management
            </div>

            <h1>
              Property management,
              <span> made simpler.</span>
            </h1>

            <p className="hero-description">
              PropertyOS brings properties, tenants, maintenance and workers
              together in one powerful platform — with AI helping you manage
              the work.
            </p>

            <div className="hero-actions">
              <Link to="/login" className="hero-primary">
                Get started
                <ArrowRight size={18} />
              </Link>

              <a href="#features" className="hero-secondary">
                Explore PropertyOS
              </a>
            </div>

            <div className="hero-note">
              <CheckCircle2 size={16} />
              One platform for your property operations
            </div>
          </div>

          {/* PRODUCT PREVIEW */}
          <div className="hero-preview-wrapper">
            <div className="hero-glow"></div>

            <div className="dashboard-preview">

              <div className="preview-sidebar">
                <div className="preview-logo">
                  <div>P</div>
                  PropertyOS
                </div>

                <div className="preview-nav active">
                  <BarChart3 size={14} />
                  Dashboard
                </div>

                <div className="preview-nav">
                  <Building2 size={14} />
                  Properties
                </div>

                <div className="preview-nav">
                  <Users size={14} />
                  Tenants
                </div>

                <div className="preview-nav">
                  <Wrench size={14} />
                  Maintenance
                </div>
              </div>

              <div className="preview-main">

                <div className="preview-header">
                  <div>
                    <small>Dashboard</small>
                    <h3>Good morning</h3>
                  </div>

                  <div className="preview-avatar">A</div>
                </div>

                <div className="preview-stats">
                  <div className="preview-stat">
                    <span>Properties</span>
                    <strong>24</strong>
                  </div>

                  <div className="preview-stat">
                    <span>Tenants</span>
                    <strong>47</strong>
                  </div>

                  <div className="preview-stat">
                    <span>Open issues</span>
                    <strong>8</strong>
                  </div>
                </div>

                <div className="preview-bottom">

                  <div className="preview-card">
                    <div className="preview-card-title">
                      <span>Recent maintenance</span>
                      <Wrench size={14} />
                    </div>

                    <div className="preview-maintenance">
                      <div className="maintenance-dot"></div>
                      <div>
                        <strong>Boiler issue</strong>
                        <small>High priority</small>
                      </div>
                      <span>Open</span>
                    </div>

                    <div className="preview-maintenance">
                      <div className="maintenance-dot"></div>
                      <div>
                        <strong>Leaking tap</strong>
                        <small>Normal priority</small>
                      </div>
                      <span>Assigned</span>
                    </div>
                  </div>

                  <div className="preview-ai">
                    <div className="ai-icon">
                      <Sparkles size={16} />
                    </div>

                    <div>
                      <strong>AI assignment</strong>
                      <p>
                        Matching maintenance requests with the right worker.
                      </p>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>
        </section>


        {/* TRUST / VALUE STRIP */}
        <section className="value-strip">
          <div>
            <strong>Manage</strong>
            <span>your properties</span>
          </div>

          <div>
            <strong>Connect</strong>
            <span>with your tenants</span>
          </div>

          <div>
            <strong>Automate</strong>
            <span>maintenance workflows</span>
          </div>

          <div>
            <strong>Track</strong>
            <span>everything in one place</span>
          </div>
        </section>


        {/* FEATURES */}
        <section className="features-section" id="features">

          <div className="section-heading">
            <div className="section-label">
              <Sparkles size={15} />
              Everything in one place
            </div>

            <h2>
              Run your property operations
              <span> without the chaos.</span>
            </h2>

            <p>
              PropertyOS gives property managers a central place to manage
              the day-to-day work that keeps properties running.
            </p>
          </div>


          <div className="feature-grid">

            <div className="feature-card feature-card-large">
              <div className="feature-icon">
                <Building2 size={21} />
              </div>

              <h3>Property management</h3>

              <p>
                Keep your properties organised and access important
                information from one central dashboard.
              </p>

              <div className="feature-mini-list">
                <span>
                  <CheckCircle2 size={15} />
                  Property records
                </span>

                <span>
                  <CheckCircle2 size={15} />
                  Organised portfolios
                </span>

                <span>
                  <CheckCircle2 size={15} />
                  Centralised information
                </span>
              </div>
            </div>


            <div className="feature-card">
              <div className="feature-icon">
                <Users size={21} />
              </div>

              <h3>Tenant management</h3>

              <p>
                Keep track of tenants and give them a simple way to interact
                with their property.
              </p>
            </div>


            <div className="feature-card">
              <div className="feature-icon">
                <Wrench size={21} />
              </div>

              <h3>Maintenance</h3>

              <p>
                Manage maintenance requests from the moment they're reported
                through to completion.
              </p>
            </div>


            <div className="feature-card">
              <div className="feature-icon ai-feature-icon">
                <Brain size={21} />
              </div>

              <h3>AI-powered workflows</h3>

              <p>
                Let AI analyse maintenance requests and help match work with
                the most suitable worker.
              </p>

              <div className="ai-tag">
                <Sparkles size={13} />
                Powered by AI
              </div>
            </div>


            <div className="feature-card">
              <div className="feature-icon">
                <BarChart3 size={21} />
              </div>

              <h3>Clear visibility</h3>

              <p>
                See what needs attention and keep your operations organised
                from a single dashboard.
              </p>
            </div>


            <div className="feature-card">
              <div className="feature-icon">
                <ShieldCheck size={21} />
              </div>

              <h3>Built for teams</h3>

              <p>
                Keep managers, workers and tenants working within one
                structured system.
              </p>
            </div>

          </div>
        </section>


        {/* HOW IT WORKS */}
        <section className="workflow-section" id="how-it-works">

          <div className="section-heading">
            <div className="section-label">
              <Sparkles size={15} />
              How it works
            </div>

            <h2>
              From problem to resolution,
              <span> in one workflow.</span>
            </h2>

            <p>
              PropertyOS helps turn maintenance requests into organised,
              actionable work.
            </p>
          </div>

          <div className="workflow-grid">

            <div className="workflow-step">
              <div className="step-number">01</div>
              <Wrench size={22} />

              <h3>A maintenance issue is reported</h3>

              <p>
                A tenant or manager records the problem inside PropertyOS.
              </p>
            </div>

            <div className="workflow-line"></div>

            <div className="workflow-step">
              <div className="step-number">02</div>
              <Brain size={22} />

              <h3>AI analyses the request</h3>

              <p>
                PropertyOS identifies the type and priority of the
                maintenance issue.
              </p>
            </div>

            <div className="workflow-line"></div>

            <div className="workflow-step">
              <div className="step-number">03</div>
              <Users size={22} />

              <h3>The right worker is assigned</h3>

              <p>
                AI helps match the request with the most relevant available
                worker.
              </p>
            </div>

          </div>
        </section>


        {/* TENANTS */}
        <section className="tenant-section" id="tenants">

          <div className="tenant-content">

            <div className="section-label">
              <Users size={15} />
              For tenants
            </div>

            <h2>
              Give tenants a
              <span> simpler experience.</span>
            </h2>

            <p>
              Tenants can create their own account and access a dedicated
              dashboard to interact with their property.
            </p>

            <div className="tenant-checks">
              <span>
                <CheckCircle2 size={17} />
                Dedicated tenant dashboard
              </span>

              <span>
                <CheckCircle2 size={17} />
                Report maintenance issues
              </span>

              <span>
                <CheckCircle2 size={17} />
                Track maintenance requests
              </span>
            </div>

            <Link to="/tenant-signup" className="tenant-button">
              Tenant signup
              <ArrowRight size={17} />
            </Link>

          </div>

          <div className="tenant-preview">
            <div className="tenant-preview-header">
              <div>
                <small>Tenant dashboard</small>
                <strong>My property</strong>
              </div>

              <div className="tenant-preview-avatar">T</div>
            </div>

            <div className="tenant-property">
              <div className="tenant-property-icon">
                <Building2 size={20} />
              </div>

              <div>
                <strong>My property</strong>
                <span>PropertyOS</span>
              </div>
            </div>

            <div className="tenant-request">
              <div className="request-icon">
                <Wrench size={17} />
              </div>

              <div>
                <strong>Maintenance request</strong>
                <span>Being handled</span>
              </div>

              <div className="request-status">
                In progress
              </div>
            </div>
          </div>

        </section>


        {/* FINAL CTA */}
        <section className="final-cta">

          <div className="final-cta-glow"></div>

          <div className="section-label">
            <Sparkles size={15} />
            PropertyOS
          </div>

          <h2>
            A better way to manage
            <span> property operations.</span>
          </h2>

          <p>
            Bring your properties, tenants, maintenance and workers together
            in one platform.
          </p>

          <Link to="/login" className="final-button">
            Get started
            <ArrowRight size={18} />
          </Link>

        </section>

      </main>


      {/* FOOTER */}
      <footer className="landing-footer">

        <div className="footer-brand">
          <div className="landing-brand-mark">P</div>
          <strong>PropertyOS</strong>
        </div>

        <div className="footer-links">
          <Link to="/login">Log in</Link>
          <Link to="/tenant-signup">Tenant signup</Link>
        </div>

        <span className="footer-copy">
          © 2026 PropertyOS
        </span>

      </footer>

    </div>
  )
}