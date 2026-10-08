import { useState } from "react"
import { Mail } from "lucide-react"
import { apiRequest } from "../services/api"
import "./Contact.css"

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
    <div className="contact-page">
      <div className="page-header">
        <div>
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

      <div className="contact-layout">
        <section className="contact-info-card">
          <div className="contact-info-icon">
            <Mail size={22} />
          </div>

          <p className="eyebrow">
            GET IN TOUCH
          </p>

          <h2>
            We're here to help
          </h2>

          <p>
            Whether you have a question about PropertyOS,
            need help with your account, or want to give us
            feedback, send us a message and we'll get back
            to you.
          </p>
        </section>

        <section className="contact-form-card">
          <form
            className="contact-form"
            onSubmit={handleSubmit}
          >
            <div className="contact-field">
              <label htmlFor="contact-name">
                Your name
              </label>

              <input
                id="contact-name"
                name="name"
                type="text"
                autoComplete="name"
                placeholder="Enter your name"
                value={form.name}
                onChange={handleChange}
                maxLength={120}
                required
              />
            </div>

            <div className="contact-field">
              <label htmlFor="contact-email">
                Email address
              </label>

              <input
                id="contact-email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
                maxLength={254}
                required
              />
            </div>

            <div className="contact-field">
              <label htmlFor="contact-subject">
                Subject
              </label>

              <input
                id="contact-subject"
                name="subject"
                type="text"
                placeholder="What can we help with?"
                value={form.subject}
                onChange={handleChange}
                maxLength={200}
                required
              />
            </div>

            <div className="contact-field">
              <label htmlFor="contact-message">
                Message
              </label>

              <textarea
                id="contact-message"
                name="message"
                placeholder="Tell us how we can help..."
                value={form.message}
                onChange={handleChange}
                rows={7}
                maxLength={5000}
                required
              />
            </div>

            {feedback && (
              <div
                className={`contact-feedback ${feedback.type}`}
                role="status"
              >
                {feedback.message}
              </div>
            )}

            <button
              className="primary-button contact-submit"
              type="submit"
              disabled={loading}
            >
              <Mail size={17} />

              {loading
                ? "Sending..."
                : "Send message"}
            </button>

            <p className="contact-privacy">
              Your message will be sent privately to the
              PropertyOS team.
            </p>
          </form>
        </section>
      </div>
    </div>
  )
}