
import {
  MapPin,
  ClipboardList,
  Search,
  Star,
  Mail,
  ArrowRight,
  Lightbulb,
} from "lucide-react"
import { useNavigate } from "react-router-dom"

const steps = [
  {
    number: "01",
    icon: MapPin,
    title: "Add your locations",
    description:
      "Save the locations where you need services. You can select a saved location when creating a request.",
    action: "Manage locations",
    path: "/locations",
  },
  {
    number: "02",
    icon: ClipboardList,
    title: "Describe what you need",
    description:
      "Create a service request and explain the job. Include useful details so professionals can understand what you need.",
    action: "Create a request",
    path: "/requests",
  },
  {
    number: "03",
    icon: Search,
    title: "Find professionals",
    description:
      "Open your request and start a provider search. Matchly looks for potentially suitable professionals based on your request.",
    action: "View requests",
    path: "/requests",
  },
  {
    number: "04",
    icon: Star,
    title: "Review your matches",
    description:
      "Compare suggested professionals and the details available. Check their suitability before deciding who to contact.",
  },
  {
    number: "05",
    icon: Mail,
    title: "Check replies",
    description:
      "Review email responses associated with your request when available, then decide how you want to proceed.",
  },
]

export default function HowToUse() {
  const navigate = useNavigate()

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <p className="page-eyebrow">MATCHLY GUIDE</p>
          <h1>How to use Matchly</h1>
          <p className="page-description">
            Find your way around Matchly, from creating a request
            to reviewing potential service providers.
          </p>
        </div>
      </div>

      <section className="how-to-intro">
        <div className="how-to-intro-icon">
          <Lightbulb size={24} />
        </div>
        <div>
          <h2>Getting started</h2>
          <p>
            Follow these five steps to organise your requests
            and discover professionals who may be able to help.
          </p>
        </div>
      </section>

      <section className="how-to-steps">
        {steps.map((step) => {
          const Icon = step.icon

          return (
            <article className="how-to-step" key={step.number}>
              <div className="how-to-step-number">
                {step.number}
              </div>

              <div className="how-to-step-icon">
                <Icon size={22} />
              </div>

              <div className="how-to-step-content">
                <h2>{step.title}</h2>
                <p>{step.description}</p>

                {step.action && (
                  <button
                    type="button"
                    className="how-to-action"
                    onClick={() => navigate(step.path)}
                  >
                    {step.action}
                    <ArrowRight size={16} />
                  </button>
                )}
              </div>
            </article>
          )
        })}
      </section>

      <section className="how-to-footer">
        <h2>Ready to get started?</h2>
        <p>
          Head to your service requests to create a request
          or continue working on an existing one.
        </p>

        <button
          type="button"
          className="primary-button"
          onClick={() => navigate("/requests")}
        >
          Go to service requests
          <ArrowRight size={16} />
        </button>
      </section>
    </div>
  )
}
