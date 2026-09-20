import React, { useEffect, useRef, useState } from "react";
import { Hand, Mic, MicOff, PhoneOff, Video, VideoOff } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import "./VideoCallRoom.css";
import { useAuth } from "../../../context/AuthContext";
import { endPharmacyVideoCall } from "../../../services/videoCallApi";

function VideoCallRoom() {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const localVideoRef = useRef(null);
  const localStreamRef = useRef(null);
  const socketRef = useRef(null);
  const peerConnectionsRef = useRef({});

  const [remoteStreams, setRemoteStreams] = useState({});

  const [cameraEnabled, setCameraEnabled] = useState(true);
  const [microphoneEnabled, setMicrophoneEnabled] = useState(true);
  const [aslEnabled, setAslEnabled] = useState(false);
  const [aslTranscript] = useState("");
  const [cameraError, setCameraError] = useState("");
  const [mediaReady, setMediaReady] = useState(false);

  const handleLeaveCall = () => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    Object.values(peerConnectionsRef.current).forEach(
      (peerConnection) => {
        peerConnection.close();
      }
    );

    peerConnectionsRef.current = {};

    if (localStreamRef.current) {
      localStreamRef.current
        .getTracks()
        .forEach((track) => {
          track.stop();
        });

      localStreamRef.current = null;
    }

    setRemoteStreams({});
    setMediaReady(false);

    if (user?.role === "pharmacy") {
      navigate("/pharmacy/video-calls");
      return;
    }

    navigate("/patient/video-calls");
  };

  const handleEndConsultation = async () => {
    const confirmed = window.confirm(
      "End this consultation for everyone? Patients will not be able to rejoin."
    );

    if (!confirmed) {
      return;
    }

    try {
      await endPharmacyVideoCall(roomId);
      handleLeaveCall();
    } catch (err) {
      console.error("Failed to end consultation:", err);
      setCameraError(
        "Unable to end the consultation. Please try again."
      );
    }
  };

  const createPeerConnection = (participantId) => {
    const peerConnection = new RTCPeerConnection({
      iceServers: [
        {
          urls: "stun:stun.l.google.com:19302",
        },
      ],
    });

    if (localStreamRef.current) {
      localStreamRef.current
        .getTracks()
        .forEach((track) => {
          peerConnection.addTrack(
            track,
            localStreamRef.current
          );
        });
    }

    peerConnection.ontrack = (event) => {
      const remoteStream = event.streams[0];

      if (!remoteStream) {
        return;
      }

      setRemoteStreams((current) => ({
        ...current,
        [participantId]: remoteStream,
      }));
    };

    peerConnection.onicecandidate = (event) => {
      if (!event.candidate) {
        return;
      }

      if (socketRef.current?.readyState !== WebSocket.OPEN) {
        return;
      }

      socketRef.current.send(
        JSON.stringify({
          type: "ice_candidate",
          target: participantId,
          candidate: event.candidate,
        })
      );
    };

    peerConnectionsRef.current[participantId] =
      peerConnection;

    return peerConnection;
  };

  useEffect(() => {
    const startLocalMedia = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        });

        localStreamRef.current = stream;

        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }

        setCameraError("");
        setMediaReady(true);
      } catch (error) {
        console.error("Camera/microphone error:", error);

        setCameraError(
          "Could not access camera or microphone."
        );
      }
    };

    startLocalMedia();

    return () => {
      if (localStreamRef.current) {
        localStreamRef.current
          .getTracks()
          .forEach((track) => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (!mediaReady) {
      return;
    }

    const protocol =
      window.location.protocol === "https:"
        ? "wss"
        : "ws";

    const socket = new WebSocket(
      `${protocol}://127.0.0.1:8000/ws/video-call/${roomId}/`
    );

    socketRef.current = socket;

    socket.onopen = () => {
      console.log("Video call signaling connected");
    };

    socket.onmessage = async (event) => {
      const data = JSON.parse(event.data);

      console.log(
        "Video call signaling message:",
        JSON.stringify(data, null, 2)
      );

      if (data.type === "consultation_ended") {
        handleLeaveCall();
        return;
      }

      if (data.type === "webrtc_signal") {
        const senderId = data.sender;
        const message = data.message;

        if (message.type === "offer") {
          let peerConnection =
            peerConnectionsRef.current[senderId];

          if (!peerConnection) {
            peerConnection =
              createPeerConnection(senderId);
          }

          await peerConnection.setRemoteDescription(
            new RTCSessionDescription(message.sdp)
          );

          const answer =
            await peerConnection.createAnswer();

          await peerConnection.setLocalDescription(answer);

          socket.send(
            JSON.stringify({
              type: "answer",
              target: senderId,
              sdp: peerConnection.localDescription,
            })
          );
        }

        if (message.type === "answer") {
          const peerConnection =
            peerConnectionsRef.current[senderId];

          if (!peerConnection) {
            return;
          }

          await peerConnection.setRemoteDescription(
            new RTCSessionDescription(message.sdp)
          );
        }

        if (message.type === "ice_candidate") {
          let peerConnection =
            peerConnectionsRef.current[senderId];

          if (!peerConnection) {
            peerConnection =
              createPeerConnection(senderId);
          }

          if (message.candidate) {
            await peerConnection.addIceCandidate(
              new RTCIceCandidate(message.candidate)
            );
          }
        }
      }

      if (data.type === "participant_left") {
        const participantId = data.participant_id;

        const peerConnection =
          peerConnectionsRef.current[participantId];

        if (peerConnection) {
          peerConnection.close();
          delete peerConnectionsRef.current[participantId];
        }

        setRemoteStreams((current) => {
          const updated = { ...current };
          delete updated[participantId];
          return updated;
        });

        return;
      }

      if (data.type === "participant_joined") {
        const participantId = data.participant_id;

        if (peerConnectionsRef.current[participantId]) {
          return;
        }

        const peerConnection =
          createPeerConnection(participantId);

        const offer =
          await peerConnection.createOffer();

        await peerConnection.setLocalDescription(offer);

        socket.send(
          JSON.stringify({
            type: "offer",
            target: participantId,
            sdp: peerConnection.localDescription,
          })
        );
      }
    };

    socket.onerror = (error) => {
      console.error(
        "Video call WebSocket error:",
        error
      );
    };

    socket.onclose = () => {
      console.log("Video call signaling disconnected");
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [mediaReady, roomId]);

  const toggleCamera = () => {
    const videoTrack =
      localStreamRef.current?.getVideoTracks()[0];

    if (!videoTrack) {
      return;
    }

    videoTrack.enabled = !videoTrack.enabled;
    setCameraEnabled(videoTrack.enabled);
  };

  const toggleMicrophone = () => {
    const audioTrack =
      localStreamRef.current?.getAudioTracks()[0];

    if (!audioTrack) {
      return;
    }

    audioTrack.enabled = !audioTrack.enabled;
    setMicrophoneEnabled(audioTrack.enabled);
  };

  return (
    <div className="video-call-room">
      <header className="video-call-header">
        <div>
          <span className="video-call-kicker">
            Video Consultation
          </span>

          <h1>Consultation Room</h1>

          <p>
            Meeting ID: {roomId}
          </p>
        </div>
      </header>

      {cameraError && (
        <div className="video-call-error">
          {cameraError}
        </div>
      )}

      <section className="video-call-stage">
        <div className="video-tile">
          <video
            ref={localVideoRef}
            autoPlay
            playsInline
            muted
          />

          <div className="video-tile-label">
            You
          </div>
        </div>

        {Object.entries(remoteStreams).map(
          ([participantId, stream]) => (
            <div
              className="video-tile"
              key={participantId}
            >
              <video
                autoPlay
                playsInline
                ref={(videoElement) => {
                  if (
                    videoElement &&
                    videoElement.srcObject !== stream
                  ) {
                    videoElement.srcObject = stream;
                  }
                }}
              />

              <div className="video-tile-label">
                Participant
              </div>
            </div>
          )
        )}
      </section>

      <div className="call-controls">
        <button
          type="button"
          className={`call-control-button ${
            !microphoneEnabled ? "inactive" : ""
          }`}
          onClick={toggleMicrophone}
        >
          {microphoneEnabled ? (
            <Mic size={17} />
          ) : (
            <MicOff size={17} />
          )}

          <span>
            {microphoneEnabled ? "Mute" : "Unmute"}
          </span>
        </button>

        <button
          type="button"
          className={`call-control-button ${
            !cameraEnabled ? "inactive" : ""
          }`}
          onClick={toggleCamera}
        >
          {cameraEnabled ? (
            <Video size={17} />
          ) : (
            <VideoOff size={17} />
          )}

          <span>
            {cameraEnabled
              ? "Camera Off"
              : "Camera On"}
          </span>
        </button>

        <button
          type="button"
          className={`call-control-button ${
            aslEnabled ? "active" : ""
          }`}
          onClick={() =>
            setAslEnabled(!aslEnabled)
          }
        >
          <Hand size={17} />

          <span>
            {aslEnabled
              ? "ASL Mode On"
              : "ASL Mode"}
          </span>
        </button>

        {user?.role === "pharmacy" && (
          <button
            type="button"
            className="call-control-button call-control-end"
            onClick={handleEndConsultation}
          >
            <PhoneOff size={17} />

            <span>
              End Consultation
            </span>
          </button>
        )}

        <button
          type="button"
          className="call-control-button call-control-leave"
          onClick={handleLeaveCall}
        >
          <PhoneOff size={17} />

          <span>
            Leave Call
          </span>
        </button>
      </div>

      {aslEnabled && (
        <section className="asl-panel">
          <div className="asl-panel-header">
            <Hand size={18} />

            <div>
              <h2>ASL Live Translation</h2>

              <p>
                Recognized signs will appear here.
              </p>
            </div>
          </div>

          <div className="asl-transcript">
            {aslTranscript ||
              "Waiting for signs..."}
          </div>
        </section>
      )}
    </div>
  );
}

export default VideoCallRoom;








