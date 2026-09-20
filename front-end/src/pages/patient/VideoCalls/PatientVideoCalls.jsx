import React, { useState } from "react";
import "./PatientVideoCalls.css";
import { Video } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getVideoCallByRoomId } from "../../../services/videoCallApi";

function PatientVideoCalls() {
  const navigate = useNavigate();

  const [roomId, setRoomId] = useState("");
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState("");

  const handleJoinMeeting = async (event) => {
    event.preventDefault();

    const cleanRoomId = roomId.trim();

    if (!cleanRoomId) {
      setError("Please enter a meeting ID.");
      return;
    }

    try {
      setJoining(true);
      setError("");

      await getVideoCallByRoomId(cleanRoomId);

      navigate(`/video-call/${cleanRoomId}`);
    } catch (err) {
      console.error(
        "Meeting validation failed:",
        err
      );

      setError(
        "This meeting does not exist or is no longer active."
      );
    } finally {
      setJoining(false);
    }
  };

  return (
    <div className="patient-video-calls">
      <header className="patient-video-calls-header">
        <span className="patient-video-calls-kicker">
          Video Consultation
        </span>

        <h1>Join Consultation</h1>

        <p>
          Enter the meeting ID provided by your pharmacy to join your consultation.
        </p>
      </header>

      <section className="patient-video-calls-card">
        <div className="patient-video-calls-card-header">
          <div className="patient-video-calls-icon">
            <Video size={21} />
          </div>

          <div>
            <h2>Meeting Access</h2>

            <p>
              Use the consultation ID shared with you.
            </p>
          </div>
        </div>

        <form
          className="patient-video-calls-form"
          onSubmit={handleJoinMeeting}
        >
          <div className="patient-video-calls-field">
            <label htmlFor="room-id">
              Meeting ID
            </label>

            <input
              id="room-id"
              type="text"
              value={roomId}
              onChange={(event) =>
                setRoomId(event.target.value)
              }
              placeholder="Enter meeting ID"
            />
          </div>

          {error && (
            <div className="patient-video-calls-error">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="patient-video-calls-submit"
            disabled={joining}
          >
            {joining
              ? "Checking Meeting..."
              : "Join Consultation"}
          </button>
        </form>
      </section>
    </div>
  );
}

export default PatientVideoCalls;
