import { useState } from "react"
import { Mail } from "lucide-react"
import { apiRequest } from "../services/api"

export default function Contact() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  })

  const [loading, setLoading] = useState(false)
  const [feedback, setFeedback] = useState(null)

  function handleChange(event) {
    const { name, value } = event.target

    setForm((current) => ({
      ...current,
      [name]: value,
    }))

    setFeedback(null)
  }

  async function handleSubmit(event) {
    event.preventDefault()

    setFeedback(null)
    setLoading(true)

    try {
      const response = await apiRequest("/contact", {
        method: "POST",
        body: JSON.stringify(form),
      })

      setFeedback({
        type: "success",
        message:
          response?.message ||
          "Your message has been sent successfully.",
      })

      setForm({
        name: "",
        email: "",
        subject: "",
        message: "",
      })
    } catch (error) {
      console.error(
        "Failed to send contact message:",
        error
      )

      setFeedback({
        type: "error",
        message:
          error?.message ||
          "Failed to send your message. Please try again.",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="dashboard-page contact-page">

      <div className="properties-header">

        <div className="properties-title">

          <p className="eyebrow">
            Support
          </p>

          <h1>
            Contact us
          </h1>

          <p className="page-subtitle">
            Have a question or need help with PropertyOS?
            Send us a message and we'll get back to you.
          </p>

        </div>

      </div>

      <div className="dashboard-card">

        <div className="card-header">

          <div>

            <p className="eyebrow">
              GET IN TOUCH
            </p>

            <h2>
              Send us a message
            </h2>

            <p className="card-subtitle">
              Fill in the form below and we'll get back
              to you as soon as possible.
            </p>

          </div>

          <Mail size={20} />

        </div>

        <form
          onSubmit={handleSubmit}
          className="contact-form"
        >

          <label>
            Your name

            <input
              name="name"
              type="text"
              autoComplete="name"
              placeholder="Enter your name"
              value={form.name}
              onChange={handleChange}
              maxLength={120}
              disabled={loading}
              required
            />
          </label>

          <label>
            Email address

            <input
              name="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={handleChange}
              maxLength={254}
              disabled={loading}
              required
            />
          </label>

          <label>
            Subject

            <input
              name="subject"
              type="text"
              placeholder="What can we help with?"
              value={form.subject}
              onChange={handleChange}
              maxLength={200}
              disabled={loading}
              required
            />
          </label>

          <label>
            Message

            <textarea
              name="message"
              placeholder="Tell us how we can help..."
              value={form.message}
              onChange={handleChange}
              rows={7}
              maxLength={5000}
              disabled={loading}
              required
            />
          </label>

          {feedback && (
            <div
              className={`contact-feedback ${feedback.type}`}
              role="status"
            >
              {feedback.message}
            </div>
          )}

          <div className="modal-actions">

            <button
              type="submit"
              className="primary-button"
              disabled={loading}
            >
              <Mail size={17} />

              {loading
                ? "Sending..."
                : "Send message"}
            </button>

          </div>

          <p className="contact-privacy">
            Your message will be sent privately to the
            PropertyOS team.
          </p>

        </form>

      </div>

    </div>
  )
}