// src/pages/TakeAttendance.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ShieldAlert, Camera, CheckCircle2, AlertTriangle } from 'lucide-react';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import {
  closeVerificationSessionById,
  completeVerification,
  createSession,
  endSession,
  processVerificationFrame,
  resetVerificationSession,
  startVerificationSession,
} from '../services/attendanceService';
import { getStudentById } from '../services/studentService';
import { getTodayDateString, getCurrentTimeString } from '../utils/date';
import { useAuth } from '../context/AuthContext';

function playSuccessChime() {
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    const ctx = new AudioContextClass();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.3);
  } catch {
    // Safely ignore if audio context requires user gesture
  }
}

export default function TakeAttendance() {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();

  const [sessionId, setSessionId] = useState(null);
  const [verificationSessionId, setVerificationSessionId] = useState(null);
  const [markedStudents, setMarkedStudents] = useState([]);
  const [selfMarkedRecord, setSelfMarkedRecord] = useState(null);
  const [studentFaceMissing, setStudentFaceMissing] = useState(false);

  const [lastMessage, setLastMessage] = useState('Camera initializing...');
  const [messageType, setMessageType] = useState('neutral'); // 'success', 'info', 'warn', 'error', 'neutral'
  const [challenge, setChallenge] = useState(null);
  const [spoofAlert, setSpoofAlert] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [facesInView, setFacesInView] = useState(0);
  const [perfStats, setPerfStats] = useState(null);

  const videoRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const offscreenCanvasRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const activeSessionIdRef = useRef(null);
  const activeVerificationIdRef = useRef(null);
  const loopTimeoutRef = useRef(null);
  const isVerifyingRef = useRef(false);
  const cooldownRef = useRef(false);
  const recentlyMarkedRef = useRef(new Map());
  const [videoAspect, setVideoAspect] = useState('4 / 3');

  // Weekend policy temporarily bypassed so attendance verification can be tested on any day
  const isSaturday = false;
  const isSunday = false;
  const isWeekend = false;
  const weekendLabel = '';

  // For students: check whether their face is already registered
  useEffect(() => {
    if (!isAdmin && user?.username) {
      getStudentById(user.username)
        .then((res) => {
          const st = res?.student || res;
          if (st && !st.face_registered) {
            setStudentFaceMissing(true);
          }
        })
        .catch(() => {});
    }
  }, [isAdmin, user]);

  useEffect(() => {
    return () => {
      stopSession();
    };
  }, []);

  const handleStartSession = async () => {
    setError('');
    setSpoofAlert('');
    if (isWeekend) {
      setError(`Attendance cannot be marked on weekends. ${weekendLabel}.`);
      return;
    }
    setLoading(true);

    try {
      const res = await createSession();
      const activeSessionId = res?.session?.session_id || res?.session_id || res?.id;
      if (!activeSessionId) {
        throw new Error('Failed to create attendance session: No Session ID returned.');
      }

      const verRes = await startVerificationSession(activeSessionId);
      const vsid = verRes?.verification_session_id;
      if (!vsid) {
        await endSession(activeSessionId).catch(() => {});
        throw new Error('Failed to start anti-spoof verification session.');
      }

      setSessionId(activeSessionId);
      setVerificationSessionId(vsid);
      activeSessionIdRef.current = activeSessionId;
      activeVerificationIdRef.current = vsid;
      cooldownRef.current = false;

      setMarkedStudents([]);
      setSelfMarkedRecord(null);
      setChallenge(verRes?.challenge || null);
      setLastMessage('Live anti-spoof verification active. Follow the on-screen challenge.');
      setMessageType('neutral');

      await startCamera();
      loopTimeoutRef.current = setTimeout(() => captureAndVerify(activeSessionId, vsid), 250);
    } catch (err) {
      setError(`Failed to start session: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }
    } catch (err) {
      setError('Camera access failed: ' + err.message);
    }
  };

  const drawFaceBox = (verification) => {
    const canvas = overlayCanvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const displayWidth = video.clientWidth || video.videoWidth || 640;
    const displayHeight = video.clientHeight || video.videoHeight || 480;
    if (canvas.width !== displayWidth) canvas.width = displayWidth;
    if (canvas.height !== displayHeight) canvas.height = displayHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const frameW = verification?.frame_width || 640;
    const frameH = verification?.frame_height || 480;
    const scaleX = canvas.width / frameW;
    const scaleY = canvas.height / frameH;

    // Multi-face support: draw bounding boxes for all detected faces in the frame
    const faces = verification?.results?.length
      ? verification.results
      : (verification?.bbox ? [verification] : []);

    faces.forEach((face) => {
      const bbox = face?.bbox;
      if (!bbox || bbox.length < 4) return;

      const [x1, y1, x2, y2] = bbox;
      const isSpoof = Boolean(face.spoof_detected);
      const isVerified = Boolean(face.verified);
      const isMatched = Boolean(face.face_matched || face.matched);

      let boxColor = '#d97706'; // Amber: scanning / unrecognized
      let labelText = 'Scanning...';

      if (isSpoof) {
        boxColor = '#dc2626'; // Red: spoof
        labelText = '⛔ Photo / Screen Detected';
      } else if (isVerified) {
        boxColor = '#16a34a'; // Green: verified genuine face
        const secText = face.class_name ? ` • ${face.class_name}` : '';
        labelText = `✓ ${face.student_name || face.student_id}${secText} (Present)`;
      } else if (isMatched) {
        boxColor = '#0284c7'; // Sky blue: recognized student, prompt to blink
        labelText = `👁️ ${face.student_name || face.student_id} • Blink Eyes`;
      }

      const drawX = x1 * scaleX;
      const drawY = y1 * scaleY;
      const drawW = (x2 - x1) * scaleX;
      const drawH = (y2 - y1) * scaleY;

      ctx.strokeStyle = boxColor;
      ctx.lineWidth = 3;
      ctx.strokeRect(drawX, drawY, drawW, drawH);

      ctx.fillStyle = boxColor;
      ctx.font = 'bold 12px Inter, -apple-system, sans-serif';
      const textWidth = ctx.measureText(labelText).width;
      const labelY = Math.max(0, drawY - 24);
      ctx.fillRect(drawX, labelY, textWidth + 14, 24);

      ctx.fillStyle = '#ffffff';
      ctx.fillText(labelText, drawX + 7, Math.max(16, drawY - 7));
    });
  };

  const clearCanvas = () => {
    const canvas = overlayCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const captureAndVerify = (activeSessionId, activeVsid) => {
    const video = videoRef.current;
    if (!video || video.readyState < 2 || isVerifyingRef.current || cooldownRef.current) {
      if (activeSessionIdRef.current === activeSessionId && cooldownRef.current) {
        loopTimeoutRef.current = setTimeout(() => captureAndVerify(activeSessionId, activeVsid), 250);
      }
      return;
    }
    if (activeSessionIdRef.current !== activeSessionId || activeVerificationIdRef.current !== activeVsid) {
      return;
    }

    isVerifyingRef.current = true;

    // High performance optimization: scale frame to max 640px to ensure instant transfer and inference
    const maxDim = 640;
    let width = video.videoWidth || 640;
    let height = video.videoHeight || 480;
    if (width > maxDim) {
      height = Math.round((height * maxDim) / width);
      width = maxDim;
    }

    if (!offscreenCanvasRef.current) {
      offscreenCanvasRef.current = document.createElement('canvas');
    }
    const canvas = offscreenCanvasRef.current;
    if (canvas.width !== width) canvas.width = width;
    if (canvas.height !== height) canvas.height = height;

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      isVerifyingRef.current = false;
      return;
    }

    // Mirror horizontally to match mirrored preview so visual directions align
    ctx.save();
    ctx.translate(width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, width, height);
    ctx.restore();

    // Fast JPEG encoding with 0.80 quality (20-35KB payload, instant transmission)
    canvas.toBlob(
      async (blob) => {
        if (
          !blob ||
          activeSessionIdRef.current !== activeSessionId ||
          activeVerificationIdRef.current !== activeVsid
        ) {
          isVerifyingRef.current = false;
          return;
        }

        const formData = new FormData();
        formData.append('image', blob, 'frame.jpg');

        try {
          const res = await processVerificationFrame(activeVsid, formData);
          if (res?.timing_ms) {
            setPerfStats(res.timing_ms);
          }

          const verification = res?.verification || {};
          const latestChallenge = res?.challenge || verification?.challenge || null;
          setChallenge(latestChallenge);
          setFacesInView(verification?.faces_count ?? (verification?.face_detected ? 1 : 0));

          if (!verification?.face_detected) {
            clearCanvas();
            setSpoofAlert('');
            setLastMessage('👤 Position face(s) in front of the camera.');
            setMessageType('neutral');
          } else {
            drawFaceBox(verification);

            // Multi-face support: find all verified live faces in frame
            const verifiedFaces = (verification.results || [verification]).filter(
              (f) => f.verified && f.student_id && !f.spoof_detected
            );

            if (verification.spoof_detected) {
              setSpoofAlert(verification.reason || 'Photo or screen spoof detected!');
              setLastMessage(`⛔ ${verification.reason}`);
              setMessageType('error');
            } else if (verifiedFaces.length > 0) {
              setSpoofAlert('');
              const now = Date.now();
              const newUnmarked = verifiedFaces.filter(
                (f) =>
                  !recentlyMarkedRef.current.has(f.student_id) ||
                  now - recentlyMarkedRef.current.get(f.student_id) > 8000
              );

              if (newUnmarked.length > 0) {
                // Record timestamp immediately so continuous frames do not flood duplicate requests
                newUnmarked.forEach((f) =>
                  recentlyMarkedRef.current.set(f.student_id, now)
                );

                const timeNow = getCurrentTimeString();
                const dateNow = getTodayDateString();
                const compForm = new FormData();
                compForm.append('attendance_date', dateNow);
                compForm.append('attendance_time', timeNow);

                const compRes = await completeVerification(activeVsid, compForm);
                const markedList = compRes?.marked_list?.length
                  ? compRes.marked_list
                  : (compRes?.attendance ? [compRes.attendance] : []);

                let newlyMarkedCount = 0;
                const newlyMarkedEntries = [];

                markedList.forEach((att) => {
                  const sid = att.student_id;
                  if (!sid) return;
                  const sname = att.student_name || sid;
                  const isMarked = att.attendance_marked;
                  if (isMarked) newlyMarkedCount++;

                  const entry = {
                    student_id: sid,
                    student_name: sname,
                    class_name: att.class_name || 'General',
                    department: att.department || '',
                    semester: att.semester || '',
                    time: timeNow,
                    date: dateNow,
                    similarity: att.similarity,
                    status: isMarked ? 'Present' : 'Already Marked',
                  };
                  newlyMarkedEntries.push(entry);
                });

                if (newlyMarkedCount > 0) {
                  playSuccessChime();
                  setMarkedStudents((prev) => {
                    const existingIds = new Set(prev.map((s) => s.student_id));
                    const toAdd = newlyMarkedEntries.filter((e) => !existingIds.has(e.student_id));
                    return [...toAdd, ...prev];
                  });
                  const names = newlyMarkedEntries
                    .filter((e) => e.status === 'Present')
                    .map((e) => e.student_name)
                    .join(', ');
                  setLastMessage(
                    `✅ Verified & Marked Attendance for ${newlyMarkedCount} student(s): ${names}`
                  );
                  setMessageType('success');
                } else if (newlyMarkedEntries.length > 0) {
                  const names = newlyMarkedEntries.map((e) => e.student_name).join(', ');
                  setLastMessage(`ℹ️ Attendance already recorded today for: ${names}`);
                  setMessageType('info');
                }

                if (!isAdmin) {
                  setTimeout(() => {
                    stopSession();
                  }, 1400);
                }
              } else {
                // All visible faces were already marked today; keep smooth continuous scanning
                const names = verifiedFaces
                  .map((e) => e.student_name || e.student_id)
                  .join(', ');
                setLastMessage(`✅ Attendance recorded for: ${names}`);
                setMessageType('success');
              }
            } else {
              setSpoofAlert('');
              setLastMessage(verification.reason || 'Scanning faces...');
              setMessageType(verification.face_matched ? 'info' : 'warn');
            }
          }
        } catch (err) {
          clearCanvas();
          setLastMessage(`Scanner status: ${err.message}`);
          setMessageType('warn');
        } finally {
          isVerifyingRef.current = false;
          if (
            activeSessionIdRef.current === activeSessionId &&
            activeVerificationIdRef.current === activeVsid &&
            !cooldownRef.current
          ) {
            loopTimeoutRef.current = setTimeout(
              () => captureAndVerify(activeSessionId, activeVsid),
              200
            );
          }
        }
      },
      'image/jpeg',
      0.80
    );
  };

  const stopSession = async () => {
    const sid = activeSessionIdRef.current || sessionId;
    const vsid = activeVerificationIdRef.current || verificationSessionId;

    activeSessionIdRef.current = null;
    activeVerificationIdRef.current = null;
    cooldownRef.current = false;
    recentlyMarkedRef.current.clear();

    if (loopTimeoutRef.current) {
      clearTimeout(loopTimeoutRef.current);
      loopTimeoutRef.current = null;
    }
    clearCanvas();

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    if (vsid) {
      await closeVerificationSessionById(vsid).catch(() => {});
    }
    if (sid) {
      await endSession(sid).catch(() => {});
    }

    setSessionId(null);
    setVerificationSessionId(null);
    setFacesInView(0);
    setPerfStats(null);
    setChallenge(null);
    setSpoofAlert('');
    isVerifyingRef.current = false;
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: 'var(--text-color)' }}>
            {isAdmin ? 'Real-Time Attendance' : 'Take My Attendance'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            {isAdmin
              ? 'Real-time facial attendance with instant eye-blink liveness verification. Photos and screens are blocked.'
              : `Logged in as Roll No. ${user?.username}. Look at the camera and blink naturally to mark your attendance.`}
          </p>
        </div>

        {sessionId && (
          <button
            className="btn btn-secondary text-red"
            onClick={stopSession}
            style={{ padding: '0.4rem 0.85rem', fontSize: '0.825rem', fontWeight: 600 }}
          >
            ⏹ End Session
          </button>
        )}
      </div>

      {studentFaceMissing && (
        <div
          className="card"
          style={{
            padding: '0.9rem 1.15rem',
            marginBottom: '1rem',
            borderLeft: '4px solid var(--status-amber)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.88rem' }}>
            <AlertTriangle size={18} style={{ color: 'var(--status-amber)' }} />
            <span>
              Your face biometric is not registered yet. Register your face before taking attendance.
            </span>
          </div>
          <button type="button" className="btn" onClick={() => navigate('/register')}>
            Register My Face ➔
          </button>
        </div>
      )}

      <ErrorMessage message={error} />
      {loading && <Loading />}

      {/* Self confirmation banner if student just marked attendance */}
      {!sessionId && selfMarkedRecord && (
        <div
          className="card"
          style={{
            maxWidth: '540px',
            margin: '1.25rem auto',
            padding: '1.35rem',
            borderLeft: '4px solid var(--status-green)',
            textAlign: 'center',
          }}
        >
          <CheckCircle2 size={36} style={{ color: 'var(--status-green)', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800 }}>
            Attendance Recorded for {selfMarkedRecord.student_name}
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.86rem', margin: '0.35rem 0 1rem' }}>
            Roll No: <strong>{selfMarkedRecord.student_id}</strong> • Date: {selfMarkedRecord.date} • Time:{' '}
            {selfMarkedRecord.time}
          </p>
          <button type="button" className="btn" onClick={() => navigate('/view-attendance')}>
            View My Attendance History ➔
          </button>
        </div>
      )}

      {/* Launch Card */}
      {!sessionId ? (
        <div
          className="card"
          style={{
            maxWidth: '540px',
            margin: '1.5rem auto',
            padding: '1.75rem',
            textAlign: 'center',
          }}
        >
          {isWeekend ? (
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '12px',
                padding: '1.25rem',
                marginBottom: '1.5rem',
              }}
            >
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>☕</div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ef4444', marginBottom: '0.4rem' }}>
                {weekendLabel}
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: 0, lineHeight: 1.5 }}>
                Attendance cannot be marked on weekends. Saturday and Sunday are designated academic holidays.
              </p>
            </div>
          ) : (
            <>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '16px',
                  backgroundColor: 'var(--purple-subtle)',
                  color: 'var(--primary-purple)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '0.85rem',
                }}
              >
                <Camera size={28} />
              </div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-color)' }}>
                Start Live Attendance Session
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.25rem', lineHeight: 1.5 }}>
                Real-time facial recognition with instant eye-blink liveness verification. Look at the camera and blink naturally to record attendance. Static photos and screens are strictly blocked.
              </p>
            </>
          )}

          <button
            type="button"
            className="btn"
            onClick={handleStartSession}
            disabled={loading || isWeekend}
            style={{
              width: '100%',
              padding: '0.85rem',
              fontSize: '1rem',
              fontWeight: 700,
              cursor: isWeekend ? 'not-allowed' : 'pointer',
              opacity: isWeekend ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
            }}
          >
            {isWeekend
              ? `⛔ Attendance Blocked (${weekendLabel})`
              : '▶ Start Live Attendance Session'}
          </button>
        </div>
      ) : (
        <div className="take-attendance-grid">
          {/* Left Column: Mirrored Camera Feed */}
          <div className="card" style={{ padding: '0.85rem' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '0.65rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: '#16a34a',
                  }}
                />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-color)' }}>
                  Live Camera
                </span>
              </div>
            </div>

            {/* Video Container */}
            <div
              style={{
                position: 'relative',
                width: '100%',
                borderRadius: '8px',
                overflow: 'hidden',
                backgroundColor: '#000000',
                marginBottom: '0.65rem',
                aspectRatio: videoAspect || '4 / 3',
              }}
            >
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                onLoadedMetadata={(e) => {
                  const v = e.target;
                  if (v?.videoWidth && v?.videoHeight) {
                    setVideoAspect(`${v.videoWidth} / ${v.videoHeight}`);
                  }
                }}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  display: 'block',
                  transform: 'scaleX(-1)',
                }}
              />
              <canvas
                ref={overlayCanvasRef}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none',
                }}
              />
            </div>

            {/* Single Clean Status Banner */}
            <div
              style={{
                padding: '0.65rem 0.9rem',
                borderRadius: '8px',
                fontSize: '0.85rem',
                fontWeight: 600,
                backgroundColor:
                  messageType === 'success'
                    ? 'var(--badge-present-bg)'
                    : messageType === 'error'
                    ? 'var(--badge-absent-bg)'
                    : messageType === 'info'
                    ? 'var(--badge-info-bg)'
                    : 'var(--hover-bg)',
                color:
                  messageType === 'success'
                    ? 'var(--badge-present-text)'
                    : messageType === 'error'
                    ? 'var(--badge-absent-text)'
                    : messageType === 'info'
                    ? 'var(--badge-info-text)'
                    : 'var(--text-secondary)',
                border: `1px solid ${
                  messageType === 'success'
                    ? 'var(--status-green)'
                    : messageType === 'error'
                    ? 'var(--status-red)'
                    : 'var(--border-color)'
                }`,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <span>{messageType === 'success' ? '✓' : messageType === 'error' ? '⛔' : messageType === 'info' ? '👁️' : '•'}</span>
              <span>{lastMessage || 'Position face in front of the camera.'}</span>
            </div>
          </div>

          {/* Right Column: Admin sees full roster; Student sees self-status ONLY */}
          <div className="card" style={{ padding: '0.85rem' }}>
            {isAdmin ? (
              <>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '0.65rem',
                  }}
                >
                  <div>
                    <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-color)' }}>
                      Marked Attendance Roster
                    </h2>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      Verified genuine faces recorded in this session
                    </span>
                  </div>
                  <span
                    style={{
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      padding: '0.25rem 0.65rem',
                      borderRadius: '12px',
                      backgroundColor: 'var(--badge-present-bg)',
                      color: 'var(--badge-present-text)',
                      border: '1px solid var(--status-green)',
                    }}
                  >
                    {markedStudents.length} Present
                  </span>
                </div>

                <div
                  style={{
                    maxHeight: '380px',
                    overflow: 'auto',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                  }}
                >
                  <table style={{ margin: 0, width: '100%', border: 'none' }}>
                    <thead>
                      <tr>
                        <th style={{ width: '38px', padding: '0.5rem 0.6rem' }}>#</th>
                        <th style={{ padding: '0.5rem 0.6rem' }}>Roll No.</th>
                        <th style={{ padding: '0.5rem 0.6rem' }}>Student Name</th>
                        <th style={{ padding: '0.5rem 0.6rem' }}>Section</th>
                        <th style={{ padding: '0.5rem 0.6rem' }}>Time</th>
                        <th style={{ width: '80px', padding: '0.5rem 0.6rem' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {markedStudents.length === 0 ? (
                        <tr>
                          <td
                            colSpan={6}
                            style={{
                              textAlign: 'center',
                              padding: '2.5rem 1rem',
                              color: 'var(--text-secondary)',
                              fontSize: '0.85rem',
                            }}
                          >
                            No students marked yet in this session. Position face in front of the camera and blink eyes to record attendance.
                          </td>
                        </tr>
                      ) : (
                        markedStudents.map((st, idx) => (
                          <tr key={`${st.student_id}-${idx}`}>
                            <td style={{ padding: '0.45rem 0.6rem', color: 'var(--text-secondary)' }}>
                              {idx + 1}
                            </td>
                            <td style={{ padding: '0.45rem 0.6rem', fontWeight: 700 }}>{st.student_id}</td>
                            <td style={{ padding: '0.45rem 0.6rem' }}>{st.student_name}</td>
                            <td style={{ padding: '0.45rem 0.6rem', fontSize: '0.8rem' }}>
                              {st.class_name || 'N/A'}
                            </td>
                            <td style={{ padding: '0.45rem 0.6rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                              {st.time}
                            </td>
                            <td style={{ padding: '0.45rem 0.6rem' }}>
                              <span
                                style={{
                                  padding: '0.2rem 0.5rem',
                                  borderRadius: '10px',
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  backgroundColor: 'var(--badge-present-bg)',
                                  color: 'var(--badge-present-text)',
                                }}
                              >
                                ✓ Present
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div>
                <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 0.35rem', color: 'var(--text-color)' }}>
                  My Verification Status
                </h2>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                  Only your own Roll No. (<strong>{user?.username}</strong>) can be marked in this session.
                </p>

                <div
                  style={{
                    padding: '1rem',
                    borderRadius: '8px',
                    backgroundColor: 'var(--hover-bg)',
                    border: '1px solid var(--border-color)',
                    marginBottom: '1rem',
                  }}
                >
                  <div style={{ fontSize: '0.82rem', marginBottom: '0.4rem' }}>
                    <strong>Student:</strong> {user?.full_name}
                  </div>
                  <div style={{ fontSize: '0.82rem', marginBottom: '0.4rem' }}>
                    <strong>Roll No:</strong> {user?.username}
                  </div>
                  <div style={{ fontSize: '0.82rem' }}>
                    <strong>Anti-Spoof Protection:</strong>{' '}
                    <span style={{ color: 'var(--status-green)', fontWeight: 700 }}>
                      Active (Blocks Photos &amp; Videos)
                    </span>
                  </div>
                </div>

                {selfMarkedRecord ? (
                  <div
                    style={{
                      padding: '1rem',
                      borderRadius: '8px',
                      backgroundColor: 'var(--badge-present-bg)',
                      color: 'var(--badge-present-text)',
                      border: '1px solid var(--status-green)',
                      fontWeight: 700,
                      fontSize: '0.88rem',
                    }}
                  >
                    ✓ Attendance recorded for {selfMarkedRecord.date} at {selfMarkedRecord.time}
                  </div>
                ) : (
                  <div style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    Look at the camera on the left and blink your eyes naturally. As soon as your live blink
                    is confirmed, your attendance will be automatically marked instantly.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
