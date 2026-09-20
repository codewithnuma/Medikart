import React, { useEffect, useState } from "react";
import {
  CalendarPlus,
  Copy,
  ExternalLink,
  Video,
} from "lucide-react";
import { Link } from "react-router-dom";

import "./PharmacyVideoCalls.css";

import {
  createPharmacyVideoCall,
  getPharmacyVideoCalls,
} from "../../../services/pharmacyApi";

function PharmacyVideoCalls() {
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copiedMeetingId, setCopiedMeetingId] = useState("");

  const loadMeetings = async () => {
    try {
      const response = await getPharmacyVideoCalls();

      setMeetings(response.data);
      setError("");
    } catch (err) {
      console.error("Failed to load meetings:", err);

      setError(
        "Could not load video consultations."
      );
    }
  };

  useEffect(() => {
    loadMeetings();
  }, []);

  const handleCreateMeeting = async (event) => {
    event.preventDefault();

    if (!title.trim() || !subject.trim()) {
      setError(
        "Please enter both meeting title and subject."
      );

      return;
    }

    try {
      setLoading(true);
      setError("");

      await createPharmacyVideoCall({
        title: title.trim(),
        subject: subject.trim(),
      });

      setTitle("");
      setSubject("");

      await loadMeetings();
    } catch (err) {
      console.error(
        "Failed to create meeting:",
        err
      );

      setError(
        "Could not create the video consultation."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCopyMeetingId = async (meetingId) => {
    try {
      await navigator.clipboard.writeText(meetingId);
      setCopiedMeetingId(meetingId);

      setTimeout(() => {
        setCopiedMeetingId("");
      }, 1500);
    } catch (err) {
      console.error("Failed to copy meeting ID:", err);
    }
  };

  return (
    <div className="pharmacy-video-calls">
      <header className="pharmacy-video-calls-header">
        <div>
          <span className="pharmacy-video-calls-kicker">
            Video Consultation
          </span>

          <h1>Video Consultations</h1>

          <p>
            Create consultation rooms and manage your
            active video meetings.
          </p>
        </div>
      </header>

      {error && (
        <div className="pharmacy-video-calls-error">
          {error}
        </div>
      )}

      <section className="pharmacy-video-create-card">
        <div className="pharmacy-video-card-header">
          <div className="pharmacy-video-card-icon">
            <CalendarPlus size={21} />
          </div>

          <div>
            <h2>Create Consultation</h2>

            <p>
              Create a meeting and share its ID with
              the patient.
            </p>
          </div>
        </div>

        <form
          className="pharmacy-video-form"
          onSubmit={handleCreateMeeting}
        >
          <div className="pharmacy-video-field">
            <label htmlFor="meeting-title">
              Meeting Title
            </label>

            <input
              id="meeting-title"
              type="text"
              value={title}
              onChange={(event) =>
                setTitle(event.target.value)
              }
              placeholder="e.g. Diabetes Follow-up"
            />
          </div>

          <div className="pharmacy-video-field">
            <label htmlFor="meeting-subject">
              Meeting Subject
            </label>

            <textarea
              id="meeting-subject"
              value={subject}
              onChange={(event) =>
                setSubject(event.target.value)
              }
              placeholder="Briefly describe the purpose of this consultation"
              rows={4}
            />
          </div>

          <button
            type="submit"
            className="pharmacy-video-create-button"
            disabled={loading}
          >
            <Video size={17} />

            <span>
              {loading
                ? "Creating..."
                : "Create Meeting"}
            </span>
          </button>
        </form>
      </section>

      <section className="pharmacy-video-meetings-section">
        <div className="pharmacy-video-section-header">
          <div>
            <h2>Your Meetings</h2>

            <p>
              View and open your consultation rooms.
            </p>
          </div>

          <span className="pharmacy-video-meeting-count">
            {meetings.length}
          </span>
        </div>

        {meetings.length === 0 ? (
          <div className="pharmacy-video-empty">
            <Video size={28} />

            <strong>
              No consultations yet
            </strong>

            <span>
              Create your first meeting using the
              form above.
            </span>
          </div>
        ) : (
          <div className="pharmacy-video-meeting-grid">
            {meetings.map((meeting) => (
              <article
                className="pharmacy-video-meeting-card"
                key={meeting.id}
              >
                <div className="pharmacy-video-meeting-top">
                  <div>
                    <h3>
                      {meeting.title}
                    </h3>

                    <p>
                      {meeting.subject}
                    </p>
                  </div>

                  <span
                    className={`pharmacy-video-status ${
                      meeting.is_active
                        ? "active"
                        : "ended"
                    }`}
                  >
                    {meeting.is_active
                      ? "Active"
                      : "Ended"}
                  </span>
                </div>

                <div className="pharmacy-video-meeting-id">
                  <span>
                    Meeting ID
                  </span>

                  <div className="pharmacy-video-meeting-id-row">
                    <code>
                      {meeting.id}
                    </code>

                    <button
                      type="button"
                      className="pharmacy-video-copy-button"
                      onClick={() =>
                        handleCopyMeetingId(meeting.id)
                      }
                    >
                      <Copy size={14} />

                      <span>
                        {copiedMeetingId === meeting.id
                          ? "Copied"
                          : "Copy"}
                      </span>
                    </button>
                  </div>
                </div>

                <Link
                  className="pharmacy-video-open-button"
                  to={`/video-call/${meeting.id}`}
                >
                  <ExternalLink size={16} />

                  <span>
                    Open Meeting Room
                  </span>
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default PharmacyVideoCalls;


