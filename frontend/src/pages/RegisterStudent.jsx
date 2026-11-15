// src/pages/RegisterStudent.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { getClasses } from '../services/classService';
import { createStudent, getStudentById, getStudents, updateStudent } from '../services/studentService';
import { registerFace } from '../services/faceService';
import { useAuth } from '../context/AuthContext';

export default function RegisterStudent() {
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();

  const [classes, setClasses] = useState([]);
  const [existingStudents, setExistingStudents] = useState([]);
  const [selectedBranch, setSelectedBranch] = useState('');
  const [selectedSemester, setSelectedSemester] = useState('');
  const [formData, setFormData] = useState({
    student_id: '',
    student_name: '',
    class_id: '',
  });
  const [isExistingStudent, setIsExistingStudent] = useState(false);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [loadingClasses, setLoadingClasses] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [capturedPhotoUrl, setCapturedPhotoUrl] = useState('');
  const [cameraReady, setCameraReady] = useState(false);
  const [blinkHint, setBlinkHint] = useState('');

  const videoRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const isRegisteringRef = useRef(false);
  const blinkTimerRef = useRef(null);

  useEffect(() => {
    const loadInitial = async () => {
      try {
        setLoadingClasses(true);
        setError('');
        if (isAdmin) {
          const [clsRes, stRes] = await Promise.all([
            getClasses(),
            getStudents().catch(() => []),
          ]);
          setClasses(Array.isArray(clsRes) ? clsRes : clsRes?.classes || []);
          setExistingStudents(Array.isArray(stRes) ? stRes : stRes?.students || []);
        } else if (user?.username) {
          const [clsRes, selfRes] = await Promise.all([
            getClasses(),
            getStudentById(user.username).catch(() => null),
          ]);
          const classList = Array.isArray(clsRes) ? clsRes : clsRes?.classes || [];
          setClasses(classList);
          const selfStudent = selfRes?.student || selfRes;
          if (selfStudent?.student_id) {
            setIsExistingStudent(true);
            setFormData({
              student_id: selfStudent.student_id,
              student_name: selfStudent.student_name || user.full_name || '',
              class_id: selfStudent.class_id ? String(selfStudent.class_id) : '',
            });
            if (selfStudent.class_id) {
              const matchedCls = classList.find(c => String(c.class_id || c.id) === String(selfStudent.class_id));
              if (matchedCls) {
                setSelectedBranch(matchedCls.department || '');
                setSelectedSemester(matchedCls.semester ? String(matchedCls.semester) : '');
              }
            }
          } else {
            setFormData({ student_id: user.username, student_name: user.full_name || '', class_id: '' });
          }
        }
      } catch (err) {
        setError(`Failed to load classes: ${err.message}`);
      } finally {
        setLoadingClasses(false);
      }
    };
    loadInitial();
    return () => stopCamera();
  }, [isAdmin, user]);

  const filteredClasses = classes.filter(c => {
    const matchSemester = selectedSemester ? String(c.semester) === String(selectedSemester) : true;
    const matchBranch = selectedBranch
      ? String(c.department || '').trim().toUpperCase() === String(selectedBranch).trim().toUpperCase()
      : true;
    return matchSemester && matchBranch;
  });

  const handleIdChange = (val) => {
    if (!isAdmin) return;
    setFormData(prev => ({ ...prev, student_id: val }));
    const existing = existingStudents.find(
      s => String(s.student_id || s.id).toLowerCase() === val.trim().toLowerCase()
    );
    setIsExistingStudent(!!existing);
  };

  const handleStepOne = (e) => {
    e.preventDefault();
    if (!formData.student_id.trim() || !formData.student_name.trim() || !selectedBranch || !selectedSemester || !formData.class_id) {
      setError('Please fill in all student information fields.');
      return;
    }
    setError('');
    setStep(2);
    setTimeout(() => startCamera(), 150);
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      });
      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play().catch(() => {});
          setCameraReady(true);
          drawFaceGuide();
          // After 5 seconds, if no blink, show hint
          blinkTimerRef.current = setTimeout(() => {
            setBlinkHint('Blink your eyes naturally before capturing 👁️');
          }, 5000);
        };
      }
    } catch (err) {
      setError(`Camera access failed: ${err.message}`);
    }
  };

  const drawFaceGuide = () => {
    const canvas = overlayCanvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const w = canvas.width, h = canvas.height;
    // Draw oval face guide
    ctx.strokeStyle = '#0066cc';
    ctx.lineWidth = 3;
    ctx.setLineDash([8, 6]);
    ctx.beginPath();
    ctx.ellipse(w / 2, h / 2, 115, 148, 0, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.setLineDash([]);
    // Label
    ctx.fillStyle = 'rgba(0, 102, 204, 0.85)';
    ctx.font = 'bold 13px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Position face inside oval', w / 2, h / 2 + 175);
  };

  const stopCamera = () => {
    if (blinkTimerRef.current) { clearTimeout(blinkTimerRef.current); blinkTimerRef.current = null; }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(t => t.stop());
      mediaStreamRef.current = null;
    }
    setCameraReady(false);
  };

  const handleCapture = () => {
    const video = videoRef.current;
    if (!video || video.readyState < 2 || isRegisteringRef.current) return;
    isRegisteringRef.current = true;
    setLoading(true);
    setError('');
    setBlinkHint('');

    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) { isRegisteringRef.current = false; setLoading(false); return; }

    // Mirror to match camera preview
    ctx.save();
    ctx.translate(width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, width, height);
    ctx.restore();

    const photoDataUrl = canvas.toDataURL('image/jpeg', 0.88);

    canvas.toBlob(async (blob) => {
      if (!blob) { isRegisteringRef.current = false; setLoading(false); return; }
      const sid = formData.student_id.trim();
      const sname = formData.student_name.trim();
      const cid = Number(formData.class_id);
      try {
        await createStudent({ student_id: sid, student_name: sname, class_id: cid }).catch(async () => {
          await updateStudent(sid, { student_name: sname, class_id: cid }).catch(() => {});
        });
        await registerFace(sid, blob, true, null);
        stopCamera();
        setCapturedPhotoUrl(photoDataUrl);
        setSuccessMsg(`${sname} (${sid}) face registered successfully!`);
        setStep(3);
      } catch (err) {
        setError(`Registration failed: ${err.message}`);
        drawFaceGuide();
      } finally {
        isRegisteringRef.current = false;
        setLoading(false);
      }
    }, 'image/jpeg', 0.88);
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.4rem', color: 'var(--text-color)' }}>
        Register Student Face
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
        Enroll a student into the system with facial biometric capture.
      </p>

      <ErrorMessage message={error} />
      {loading && <Loading />}

      {/* Step 1 — Student Info */}
      {step === 1 && (
        <form onSubmit={handleStepOne} className="card" style={{ padding: '1.75rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1.25rem', color: 'var(--text-color)' }}>Student Information</h2>

          <label style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.3rem', display: 'block' }}>Roll / Student ID</label>
          <input
            type="text" placeholder="e.g. 23053877"
            value={formData.student_id}
            onChange={e => handleIdChange(e.target.value)}
            readOnly={!isAdmin}
            style={{ marginBottom: '0.9rem', opacity: !isAdmin ? 0.75 : 1 }}
            required
          />

          {isExistingStudent && (
            <div style={{ padding: '0.55rem 0.8rem', borderRadius: '6px', backgroundColor: 'var(--badge-info-bg)', color: 'var(--badge-info-text)', fontSize: '0.82rem', marginBottom: '0.9rem', border: '1px solid var(--border-color)' }}>
              ℹ️ Existing student found — will update face & class.
            </div>
          )}

          <label style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.3rem', display: 'block' }}>Student Name</label>
          <input
            type="text" placeholder="e.g. Dipendra"
            value={formData.student_name}
            onChange={e => setFormData({ ...formData, student_name: e.target.value })}
            style={{ marginBottom: '0.9rem' }} required
          />

          <label style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.3rem', display: 'block' }}>Branch (Department)</label>
          <select value={selectedBranch} onChange={e => { setSelectedBranch(e.target.value); setFormData(p => ({ ...p, class_id: '' })); }} style={{ marginBottom: '0.9rem' }} required>
            <option value="">-- Select Branch --</option>
            <option value="CSE">CSE (Computer Science & Engineering)</option>
            <option value="IT">IT (Information Technology)</option>
            <option value="ECE">ECE (Electronics & Communication)</option>
            <option value="ME">ME (Mechanical Engineering)</option>
            <option value="Civil">Civil Engineering</option>
          </select>

          <label style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.3rem', display: 'block' }}>Semester</label>
          <select value={selectedSemester} onChange={e => { setSelectedSemester(e.target.value); setFormData(p => ({ ...p, class_id: '' })); }} style={{ marginBottom: '0.9rem' }} required>
            <option value="">-- Select Semester --</option>
            {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
          </select>

          <label style={{ fontWeight: 600, fontSize: '0.88rem', marginBottom: '0.3rem', display: 'block' }}>Section</label>
          <select
            value={formData.class_id}
            onChange={e => setFormData({ ...formData, class_id: e.target.value })}
            style={{ marginBottom: '1.5rem' }}
            required disabled={loadingClasses || !selectedBranch || !selectedSemester}
          >
            <option value="">{!selectedBranch || !selectedSemester ? 'Select Branch & Semester first' : loadingClasses ? 'Loading...' : filteredClasses.length === 0 ? 'No sections found' : '-- Select Section --'}</option>
            {filteredClasses.map(c => (
              <option key={c.class_id || c.id} value={c.class_id || c.id}>{c.class_name} ({c.department || selectedBranch})</option>
            ))}
          </select>

          <button type="submit" className="btn" style={{ width: '100%', padding: '0.85rem', fontSize: '1rem', fontWeight: 700 }}
            disabled={loadingClasses || !selectedBranch || !selectedSemester || !formData.class_id || loading}>
            Next: Capture Face →
          </button>
        </form>
      )}

      {/* Step 2 — Camera Capture */}
      {step === 2 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-color)', margin: 0 }}>Face Capture</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginTop: '0.2rem' }}>
                Look straight into the camera and click capture
              </p>
            </div>
            <button type="button" className="btn btn-secondary" onClick={() => { stopCamera(); setStep(1); }} style={{ fontSize: '0.82rem', padding: '0.35rem 0.75rem' }}>
              ← Back
            </button>
          </div>

          {/* Student info summary */}
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', padding: '0.65rem 0.9rem', borderRadius: '6px', backgroundColor: 'var(--hover-bg)', border: '1px solid var(--border-color)', marginBottom: '1rem', fontSize: '0.83rem' }}>
            <span><strong>Name:</strong> {formData.student_name}</span>
            <span><strong>Roll:</strong> {formData.student_id}</span>
            <span><strong>Branch:</strong> {selectedBranch} Sem {selectedSemester}</span>
          </div>

          {/* Blink hint */}
          {blinkHint && (
            <div style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', backgroundColor: 'var(--badge-info-bg)', color: 'var(--badge-info-text)', fontSize: '0.82rem', marginBottom: '0.75rem', border: '1px solid var(--primary-purple)' }}>
              {blinkHint}
            </div>
          )}

          {/* Camera feed */}
          <div style={{ position: 'relative', width: '100%', borderRadius: '10px', overflow: 'hidden', backgroundColor: '#000', marginBottom: '1rem', aspectRatio: '4/3' }}>
            <video ref={videoRef} autoPlay playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)', display: 'block' }} />
            <canvas ref={overlayCanvasRef} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }} />
            {!cameraReady && (
              <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.6)', color: '#fff', fontSize: '0.9rem', fontWeight: 600 }}>
                Starting camera...
              </div>
            )}
          </div>

          <button
            type="button"
            className="btn"
            onClick={handleCapture}
            disabled={loading || !cameraReady}
            style={{ width: '100%', padding: '0.9rem', fontSize: '1rem', fontWeight: 700 }}
          >
            {loading ? '⏳ Processing...' : '📸 Capture Face & Register'}
          </button>
        </div>
      )}

      {/* Step 3 — Success */}
      {step === 3 && (
        <div className="card" style={{ padding: '2.5rem 1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>✅</div>
          <h2 style={{ color: 'var(--status-green)', fontSize: '1.25rem', fontWeight: 800, marginBottom: '0.5rem' }}>{successMsg}</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '1.5rem' }}>
            Face biometric saved. Ready for attendance!
          </p>
          {capturedPhotoUrl && (
            <div style={{ marginBottom: '1.5rem' }}>
              <img src={capturedPhotoUrl} alt="Captured" style={{ width: '120px', height: '120px', borderRadius: '50%', objectFit: 'cover', border: '3px solid var(--status-green)' }} />
            </div>
          )}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn" onClick={() => { setStep(1); setSelectedSemester(''); setSelectedBranch(''); setFormData({ student_id: '', student_name: '', class_id: '' }); setSuccessMsg(''); setError(''); setCapturedPhotoUrl(''); setBlinkHint(''); }}>
              + Register Another Student
            </button>
            <button className="btn" onClick={() => navigate('/take-attendance')}>Take Attendance →</button>
          </div>
        </div>
      )}
    </div>
  );
}
