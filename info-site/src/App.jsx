import "./App.css"

const APP_URL = "https://property-os-app.com"

function App() {
  return (
    <div className="site">
      {/* =========================
          NAVBAR
      ========================= */}

      <header className="navbar">
        <div className="nav-container">
          <a href="/" className="brand">
            <div className="brand-mark">P</div>
            <span>PropertyOS</span>
          </a>

          <nav className="nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How it works</a>
            <a href="#ai">AI</a>
          </nav>

          <a href={APP_URL} className="nav-button">
            Open PropertyOS
          </a>
        </div>
      </header>


      <main>
        {/* =========================
            HERO
        ========================= */}

        <section className="hero">
          <div className="hero-container">
            <div className="hero-content">
              <div className="eyebrow">
                AI-powered property management
              </div>

              <h1>
                Property management,
                <span> simplified.</span>
              </h1>

              <p className="hero-description">
                Manage properties, tenants, maintenance and workers
                in one simple platform — with AI helping you get
                maintenance requests to the right person.
              </p>

              <div className="hero-actions">
                <a href={APP_URL} className="primary-button">
                  Open PropertyOS
                  <span>→</span>
                </a>

                <a href="#features" className="secondary-button">
                  Explore features
                </a>
              </div>

              <div className="hero-note">
                ✓ One platform for your property operation
              </div>
            </div>


            {/* Product Preview */}

            <div className="hero-preview">
              <div className="browser-window">

                <div className="browser-top">
                  <div className="browser-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>

                  <div className="browser-address">
                    property-os-app.com
                  </div>
                </div>


                <div className="preview-content">

                  {/* Sidebar */}

                  <div className="preview-sidebar">
                    <div className="preview-brand">
                      <div className="preview-brand-mark">
                        P
                      </div>

                      <strong>
                        PropertyOS
                      </strong>
                    </div>

                    <div className="preview-nav active">
                      <span>▦</span>
                      Dashboard
                    </div>

                    <div className="preview-nav">
                      <span>□</span>
                      Properties
                    </div>

                    <div className="preview-nav">
                      <span>○</span>
                      Tenants
                    </div>

                    <div className="preview-nav">
                      <span>⚒</span>
                      Maintenance
                    </div>

                    <div className="preview-nav">
                      <span>◆</span>
                      Workers
                    </div>
                  </div>


                  {/* Main Preview */}

                  <div className="preview-main">

                    <div className="preview-heading">
                      <div>
                        <div className="preview-welcome">
                          Welcome back
                        </div>

                        <div className="preview-title">
                          Dashboard
                        </div>
                      </div>
                    </div>


                    {/* Stats */}

                    <div className="preview-stats">

                      <div className="preview-stat">
                        <div className="stat-icon">
                          □
                        </div>

                        <div>
                          <small>
                            Properties
                          </small>

                          <strong>
                            12
                          </strong>
                        </div>
                      </div>


                      <div className="preview-stat">
                        <div className="stat-icon">
                          ○
                        </div>

                        <div>
                          <small>
                            Tenants
                          </small>

                          <strong>
                            38
                          </strong>
                        </div>
                      </div>


                      <div className="preview-stat">
                        <div className="stat-icon">
                          ⚒
                        </div>

                        <div>
                          <small>
                            Open requests
                          </small>

                          <strong>
                            5
                          </strong>
                        </div>
                      </div>

                    </div>


                    {/* Maintenance Card */}

                    <div className="preview-card">

                      <div className="preview-card-header">
                        <div>
                          <small>
                            Recent maintenance
                          </small>

                          <strong>
                            Maintenance requests
                          </strong>
                        </div>

                        <span className="status-badge">
                          AI assisted
                        </span>
                      </div>


                      <div className="maintenance-row">

                        <div className="maintenance-icon">
                          ⚒
                        </div>

                        <div className="maintenance-info">
                          <strong>
                            Heating issue
                          </strong>

                          <span>
                            Flat 4 · 12 High Street
                          </span>
                        </div>

                        <div className="priority">
                          High
                        </div>

                      </div>


                      <div className="maintenance-row">

                        <div className="maintenance-icon">
                          ⚒
                        </div>

                        <div className="maintenance-info">
                          <strong>
                            Leaking tap
                          </strong>

                          <span>
                            Flat 8 · 24 Park Road
                          </span>
                        </div>

                        <div className="priority medium">
                          Medium
                        </div>

                      </div>


                      <div className="maintenance-row">

                        <div className="maintenance-icon">
                          ⚒
                        </div>

                        <div className="maintenance-info">
                          <strong>
                            Broken light
                          </strong>

                          <span>
                            Flat 2 · 8 Station Road
                          </span>
                        </div>

                        <div className="priority low">
                          Low
                        </div>

                      </div>

                    </div>

                  </div>
                </div>
              </div>
            </div>

          </div>
        </section>


        {/* =========================
            FEATURES
        ========================= */}

        <section id="features" className="section">
          <div className="section-container">

            <div className="section-heading">

              <div className="eyebrow">
                One platform
              </div>

              <h2>
                Everything your property operation needs.
              </h2>

              <p>
                Keep your properties, tenants, maintenance and
                workers organised from one place.
              </p>

            </div>


            <div className="features-grid">

              <div className="feature-card">
                <div className="feature-icon">
                  □
                </div>

                <h3>
                  Properties
                </h3>

                <p>
                  Keep your property portfolio organised and
                  access important information quickly.
                </p>
              </div>


              <div className="feature-card">
                <div className="feature-icon">
                  ○
                </div>

                <h3>
                  Tenants
                </h3>

                <p>
                  Manage tenants and connect them with the
                  properties they occupy.
                </p>
              </div>


              <div className="feature-card">
                <div className="feature-icon">
                  ⚒
                </div>

                <h3>
                  Maintenance
                </h3>

                <p>
                  Track maintenance requests from creation
                  through completion.
                </p>
              </div>


              <div className="feature-card">
                <div className="feature-icon">
                  ◆
                </div>

                <h3>
                  Workers
                </h3>

                <p>
                  Manage workers and make it easier to assign
                  the right person to each job.
                </p>
              </div>

            </div>

          </div>
        </section>


        {/* =========================
            AI SECTION
        ========================= */}

        <section id="ai" className="ai-section">

          <div className="ai-container">

            <div className="ai-content">

              <div className="eyebrow">
                Intelligent maintenance
              </div>

              <h2>
                The right person for every job.
              </h2>

              <p>
                PropertyOS analyses maintenance requests and
                helps get them to the right person — automatically
                when a suitable internal worker is available.
              </p>


              <div className="ai-list">

                <div>
                  <span>✓</span>
                  Analyse the maintenance request
                </div>

                <div>
                  <span>✓</span>
                  Identify the required trade
                </div>

                <div>
                  <span>✓</span>
                  Automatically assign a suitable internal worker
                </div>

                <div>
                  <span>✓</span>
                  Search for suitable external contractors when needed
                </div>

                <div>
                  <span>✓</span>
                  Rank external options for the manager to review
                </div>

                <div>
                  <span>✓</span>
                  Keep the manager in control
                </div>

              </div>

            </div>


            {/* AI Demo */}

            <div className="ai-demo">

              <div className="ai-demo-header">
                <span className="ai-dot"></span>

                AI maintenance workflow
              </div>


              {/* Request */}

              <div className="ai-message">

                <small>
                  Maintenance request
                </small>

                <p>
                  "The boiler isn't heating the radiators
                  and the property is getting cold."
                </p>

              </div>


              <div className="ai-arrow">
                ↓
              </div>


              {/* Analysis */}

              <div className="ai-result">

                <div className="result-row">
                  <span>
                    Category
                  </span>

                  <strong>
                    Heating
                  </strong>
                </div>


                <div className="result-row">
                  <span>
                    Priority
                  </span>

                  <strong>
                    High
                  </strong>
                </div>


                <div className="result-row">
                  <span>
                    Required trade
                  </span>

                  <strong>
                    Heating
                  </strong>
                </div>


                <div className="result-row">
                  <span>
                    Internal worker
                  </span>

                  <strong>
                    Heating specialist
                  </strong>
                </div>


                <div className="result-row">
                  <span>
                    Assignment
                  </span>

                  <strong className="success-text">
                    Automatically assigned
                  </strong>
                </div>

              </div>


              {/* External Search */}

              <div className="external-search-box">

                <div className="external-search-title">
                  No suitable internal worker?
                </div>

                <div className="external-search-text">
                  PropertyOS can search for suitable external
                  contractors and rank the best matches for
                  the manager to review.
                </div>


                <div className="contractor-results">

                  <div className="contractor-result">

                    <div>
                      <strong>
                        Heating specialist
                      </strong>

                      <span>
                        Local contractor · Highly rated
                      </span>
                    </div>

                    <b>
                      Best match
                    </b>

                  </div>


                  <div className="contractor-result">

                    <div>
                      <strong>
                        Gas & Heating Services
                      </strong>

                      <span>
                        Local contractor · Available
                      </span>
                    </div>

                    <b>
                      92%
                    </b>

                  </div>


                  <div className="contractor-result">

                    <div>
                      <strong>
                        City Heating Ltd
                      </strong>

                      <span>
                        Local contractor · Strong reviews
                      </span>
                    </div>

                    <b>
                      88%
                    </b>

                  </div>

                </div>


                <div className="manager-control">
                  <span>
                    Manager review
                  </span>

                  <strong>
                    Select contractor →
                  </strong>
                </div>

              </div>

            </div>

          </div>

        </section>


        {/* =========================
            WORKFLOW
        ========================= */}

        <section
          id="how-it-works"
          className="section workflow-section"
        >

          <div className="section-container">

            <div className="section-heading">

              <div className="eyebrow">
                Simple workflow
              </div>

              <h2>
                From maintenance request to resolution.
              </h2>

              <p>
                PropertyOS helps decide what needs to happen
                next while keeping the manager in control.
              </p>

            </div>


            <div className="workflow">

              <div className="workflow-step">

                <div className="step-number">
                  01
                </div>

                <h3>
                  Create
                </h3>

                <p>
                  A maintenance request is created and
                  recorded in PropertyOS.
                </p>

              </div>


              <div className="workflow-line"></div>


              <div className="workflow-step">

                <div className="step-number">
                  02
                </div>

                <h3>
                  Analyse
                </h3>

                <p>
                  AI identifies the maintenance category,
                  priority and required trade.
                </p>

              </div>


              <div className="workflow-line"></div>


              <div className="workflow-step">

                <div className="step-number">
                  03
                </div>

                <h3>
                  Assign internally
                </h3>

                <p>
                  If a suitable internal worker exists,
                  PropertyOS can automatically assign
                  the job to them.
                </p>

              </div>


              <div className="workflow-line"></div>


              <div className="workflow-step">

                <div className="step-number">
                  04
                </div>

                <h3>
                  Find externally
                </h3>

                <p>
                  If needed, PropertyOS searches for
                  suitable external contractors and
                  ranks the best matches.
                </p>

              </div>


              <div className="workflow-line"></div>


              <div className="workflow-step">

                <div className="step-number">
                  05
                </div>

                <h3>
                  Review & track
                </h3>

                <p>
                  The manager chooses the external option
                  when needed and keeps the job visible
                  through completion.
                </p>

              </div>

            </div>

          </div>

        </section>


        {/* =========================
            INTERNAL VS EXTERNAL
        ========================= */}

        <section className="section decision-section">

          <div className="section-container">

            <div className="section-heading">

              <div className="eyebrow">
                Built for real operations
              </div>

              <h2>
                Internal worker first. External when needed.
              </h2>

              <p>
                PropertyOS helps property managers use the
                resources they already have before finding
                suitable external help.
              </p>

            </div>


            <div className="decision-grid">

              <div className="decision-card internal-card">

                <div className="decision-label">
                  INTERNAL
                </div>

                <div className="decision-number">
                  01
                </div>

                <h3>
                  Use your own workers
                </h3>

                <p>
                  PropertyOS analyses the request and matches
                  it against suitable internal workers.
                </p>

                <div className="decision-points">

                  <div>
                    <span>✓</span>
                    Match by trade and speciality
                  </div>

                  <div>
                    <span>✓</span>
                    Automatically assign suitable workers
                  </div>

                  <div>
                    <span>✓</span>
                    Manager can stay in control
                  </div>

                </div>

              </div>


              <div className="decision-arrow">
                <span>OR</span>
              </div>


              <div className="decision-card external-card">

                <div className="decision-label">
                  EXTERNAL
                </div>

                <div className="decision-number">
                  02
                </div>

                <h3>
                  Find outside help
                </h3>

                <p>
                  When there isn't a suitable internal worker,
                  PropertyOS can search for external contractors
                  and surface the strongest matches.
                </p>

                <div className="decision-points">

                  <div>
                    <span>✓</span>
                    Search for relevant contractors
                  </div>

                  <div>
                    <span>✓</span>
                    Compare and rank suitable options
                  </div>

                  <div>
                    <span>✓</span>
                    Manager selects the final option
                  </div>

                </div>

              </div>

            </div>

          </div>

        </section>


        {/* =========================
            FINAL CTA
        ========================= */}

        <section className="cta-section">

          <div className="cta-container">

            <div className="eyebrow">
              Get started
            </div>

            <h2>
              Make property management simpler.
            </h2>

            <p>
              Bring your properties, tenants, maintenance
              workflow and workers together with PropertyOS.
            </p>

            <a
              href={APP_URL}
              className="primary-button large"
            >
              Open PropertyOS
              <span>→</span>
            </a>

          </div>

        </section>

      </main>


      {/* =========================
          FOOTER
      ========================= */}

      <footer className="footer">

        <div className="footer-container">

          <div className="footer-brand">

            <div className="brand-mark">
              P
            </div>

            <span>
              PropertyOS
            </span>

          </div>

          <div className="footer-text">
            Property management, simplified.
          </div>

        </div>

      </footer>

    </div>
  )
}

export default App