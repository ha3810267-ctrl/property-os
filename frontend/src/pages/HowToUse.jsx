
import {
  MapPin,
  ClipboardList,
  Search,
  RefreshCw,
  Mail,
  Clock,
  ShieldCheck,
  ArrowRight,
  CircleHelp,
} from "lucide-react"
import { useNavigate } from "react-router-dom"

const steps = [
  {
    number: "01",
    icon: MapPin,
    title: "Add a location",
    description:
      "Go to Locations and add the location where you need the service. You will use this location when creating your request.",
  },
  {
    number: "02",
    icon: ClipboardList,
    title: "Create a service request",
    description:
      "Go to Service Requests and create a request. Describe exactly what you need, including any useful details that will help a professional understand the job.",
  },
  {
    number: "03",
    icon: Search,
    title: "Find providers",
    description:
      "Open your request and click Find Providers. The button may become temporarily unavailable while Matchly searches for suitable professionals.",
  },
  {
    number: "04",
    icon: RefreshCw,
    title: "Wait, then refresh",
    description:
      "Wait until the Find Providers button becomes available (ungreyed) again. Then refresh the page to load and display the search results.",
  },
  {
    number: "05",
    icon: Mail,
    title: "Wait for a reply",
    description:
      "Providers may respond by email. You can see replies on your Dashboard and under the relevant provider inside your service request. Check both places for updates.",
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
            Follow these steps to find a suitable professional
            for the service you need.
          </p>
        </div>
      </div>

      <section className="how-to-intro">
        <div className="how-to-intro-icon">
          <CircleHelp size={24} />
        </div>
        <div>
          <h2>Simple from start to finish</h2>
          <p>
            Add your location, describe the job, find providers
            and keep track of replies. If nobody responds, we
            have a backup plan to help you.
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

                {step.number === "01" && (
                  <button
                    type="button"
                    className="how-to-action"
                    onClick={() => navigate("/locations")}
                  >
                    Go to Locations
                    <ArrowRight size={16} />
                  </button>
                )}

                {step.number === "02" && (
                  <button
                    type="button"
                    className="how-to-action"
                    onClick={() => navigate("/requests")}
                  >
                    Create a request
                    <ArrowRight size={16} />
                  </button>
                )}

                {step.number === "05" && (
                  <button
                    type="button"
                    className="how-to-action"
                    onClick={() => navigate("/")}
                  >
                    View Dashboard
                    <ArrowRight size={16} />
                  </button>
                )}
              </div>
            </article>
          )
        })}
      </section>

      <section className="how-to-support">
        <div className="how-to-support-heading">
          <div className="how-to-support-icon">
            <Clock size={24} />
          </div>
          <div>
            <p className="page-eyebrow">OUR SUPPORT PROMISE</p>
            <h2>No replies after two business days?</h2>
          </div>
        </div>

        <p>
          If you have not received any provider replies within
          two business days, contact us and we will step in to
          help you find a professional.
        </p>

        <div className="how-to-support-steps">
          <div className="how-to-support-step">
            <span>1</span>
            <div>
              <h3>Contact Matchly</h3>
              <p>
                Open Contact Us and tell us that you have not
                received any provider replies within two business
                days.
              </p>
            </div>
          </div>

          <div className="how-to-support-step">
            <span>2</span>
            <div>
              <h3>Include your account details</h3>
              <p>
                Tell us the name you signed up with and the email
                address you used to register. This helps us
                identify your account.
              </p>
            </div>
          </div>

          <div className="how-to-support-step">
            <span>3</span>
            <div>
              <h3>We find a provider for you</h3>
              <p>
                We will manually search for a suitable provider
                within the next business day after you contact us.
              </p>
            </div>
          </div>
        </div>

        <div className="how-to-refund">
          <ShieldCheck size={22} />
          <div>
            <h3>Your money is protected</h3>
            <p>
              In the highly unlikely event that we still cannot
              find you a provider, we will give you a full refund.
            </p>
          </div>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={() => navigate("/contact")}
        >
          Contact Us
          <ArrowRight size={16} />
        </button>
      </section>

      <section className="how-to-footer">
        <h2>Ready to find a provider?</h2>
        <p>
          Start by adding your location, then create your first
          service request.
        </p>
        <button
          type="button"
          className="primary-button"
          onClick={() => navigate("/locations")}
        >
          Get started
          <ArrowRight size={16} />
        </button>
      </section>
    </div>
  )
}
