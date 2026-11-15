// src/pages/Signup.jsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Lock,
  Eye,
  EyeOff,
  Sparkles,
  IdCard,
  UserPlus,
  Moon,
  Sun,
  CheckCircle2,
  AlertCircle,
  Loader2,
  GraduationCap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { lookupStudent } from '../services/authService';
import ErrorMessage from '../components/ErrorMessage';

export default function Signup({ theme, toggleTheme }) {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [rollNo, setRollNo] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Real-time student lookup from DB records
  const [studentInfo, setStudentInfo] = useState(null);
  const [lookingUp, setLookingUp] = useState(false);

  useEffect(() => {
    const trimmed = rollNo.trim();
    if (!trimmed || trimmed.length < 3) {
      setStudentInfo(null);
      setLookingUp(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLookingUp(true);
      try {
        const res = await lookupStudent(trimmed);
        if (res?.data) {
          setStudentInfo(res.data);
          if (res.data.already_registered) {
            setError('An account for this roll number already exists. Please log in.');
          } else if (!res.data.found) {
            setError(`Roll number "${trimmed}" was not found in student records. Contact admin.`);
          } else {
            setError('');
          }
        }
      } catch (err) {
        setStudentInfo({
          found: false,
          message: err.message || 'Error looking up student record.',
        });
      } finally {
        setLookingUp(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [rollNo]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const trimmedRoll = rollNo.trim();

    if (!/^[A-Za-z0-9_-]{3,50}$/.test(trimmedRoll)) {
      setError('Roll No. must be 3–50 characters using letters, numbers, "-" or "_" only.');
      return;
    }

    if (studentInfo && !studentInfo.found) {
      setError(studentInfo.message || 'Roll number not found in enrolled student records.');
      return;
    }

    if (studentInfo?.already_registered) {
      setError('An account for this roll number already exists. Please sign in.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      // Backend automatically retrieves student_name and class_id from DB record
      await signup({
        username: trimmedRoll,
        password,
      });
      navigate('/view-attendance', { replace: true });
    } catch (err) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
        backgroundColor: 'var(--bg-color)',
        position: 'relative',
      }}
    >
      {toggleTheme && (
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            width: '40px',
            height: '40px',
            borderRadius: 'var(--radius-xs)',
            border: '1px solid var(--border-color)',
            backgroundColor: 'var(--card-bg)',
            color: 'var(--text-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 200ms ease',
          }}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
      )}

      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: '440px',
          padding: '2.25rem 2rem',
          borderRadius: '24px',
          boxShadow: 'var(--shadow-card)',
          border: '1px solid rgba(0, 0, 0, 0.08)',
        }}
      >
        {/* Brand / Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '14px',
              background: 'var(--apple-blue)',
              color: '#ffffff',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '0.75rem',
              boxShadow: '0 4px 12px rgba(0, 102, 204, 0.25)',
            }}
          >
            <Sparkles size={22} />
          </div>
          <h1
            style={{
              fontSize: '1.45rem',
              fontWeight: 700,
              margin: 0,
              color: 'var(--text-color)',
              letterSpacing: '-0.02em',
            }}
          >
            Student Sign Up
          </h1>
          <p
            style={{
              color: 'var(--text-secondary)',
              fontSize: '0.85rem',
              marginTop: '0.35rem',
            }}
          >
            Enter your Roll Number to activate your student portal
          </p>
        </div>

        {/* Tab Switcher */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '0.35rem',
            padding: '0.25rem',
            backgroundColor: 'var(--hover-bg)',
            borderRadius: '999px',
            marginBottom: '1.25rem',
            border: '1px solid var(--border-color)',
          }}
        >
          <Link
            to="/login"
            style={{
              textAlign: 'center',
              padding: '0.5rem',
              borderRadius: '999px',
              fontSize: '0.85rem',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              textDecoration: 'none',
              transition: 'all 200ms ease',
            }}
          >
            Sign In
          </Link>
          <div
            style={{
              textAlign: 'center',
              padding: '0.5rem',
              borderRadius: '999px',
              fontSize: '0.85rem',
              fontWeight: 600,
              backgroundColor: 'var(--card-bg)',
              color: 'var(--apple-blue)',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
            }}
          >
            Student Sign Up
          </div>
        </div>

        <ErrorMessage message={error} />

        <form onSubmit={handleSubmit}>
          {/* Roll Number Input */}
          <div style={{ marginBottom: '1rem' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                marginBottom: '0.35rem',
                color: 'var(--text-color)',
              }}
            >
              Roll Number (Student ID)
            </label>
            <div style={{ position: 'relative' }}>
              <IdCard
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-secondary)',
                }}
              />
              <input
                type="text"
                value={rollNo}
                onChange={(e) => setRollNo(e.target.value)}
                placeholder="e.g. 23053891"
                autoComplete="username"
                required
                style={{
                  width: '100%',
                  paddingLeft: '2.35rem',
                  paddingRight: lookingUp ? '2.5rem' : '1rem',
                  height: '42px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--border-color)',
                }}
              />
              {lookingUp && (
                <Loader2
                  size={16}
                  className="spin"
                  style={{
                    position: 'absolute',
                    right: '12px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--apple-blue)',
                  }}
                />
              )}
            </div>

            {/* Dynamic Verified Record Card */}
            {studentInfo?.found && !studentInfo?.already_registered && (
              <div
                style={{
                  marginTop: '0.55rem',
                  padding: '0.65rem 0.85rem',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(52, 199, 89, 0.1)',
                  border: '1px solid rgba(52, 199, 89, 0.25)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.5rem',
                  animation: 'fadeIn 200ms ease',
                }}
              >
                <CheckCircle2
                  size={16}
                  style={{ color: '#34c759', flexShrink: 0, marginTop: '2px' }}
                />
                <div style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
                  <div style={{ fontWeight: 700, color: 'var(--text-color)' }}>
                    {studentInfo.student_name}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.74rem' }}>
                    {studentInfo.class_name ? `Class: ${studentInfo.class_name}` : 'Enrolled Student'}
                    {studentInfo.department ? ` • ${studentInfo.department}` : ''}
                    {studentInfo.semester ? ` Sem ${studentInfo.semester}` : ''}
                  </div>
                </div>
              </div>
            )}

            {studentInfo?.already_registered && (
              <div
                style={{
                  marginTop: '0.55rem',
                  padding: '0.65rem 0.85rem',
                  borderRadius: '12px',
                  backgroundColor: 'rgba(255, 149, 0, 0.1)',
                  border: '1px solid rgba(255, 149, 0, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.78rem',
                  color: 'var(--text-color)',
                }}
              >
                <AlertCircle size={15} style={{ color: '#ff9500', flexShrink: 0 }} />
                <span>
                  Account already created.{' '}
                  <Link to="/login" style={{ color: 'var(--apple-blue)', fontWeight: 600 }}>
                    Sign in here
                  </Link>
                </span>
              </div>
            )}
          </div>

          {/* Password Input */}
          <div style={{ marginBottom: '1rem' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                marginBottom: '0.35rem',
                color: 'var(--text-color)',
              }}
            >
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-secondary)',
                }}
              />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                autoComplete="new-password"
                required
                style={{
                  width: '100%',
                  paddingLeft: '2.35rem',
                  paddingRight: '2.5rem',
                  height: '42px',
                  borderRadius: 'var(--radius-xs)',
                  border: '1px solid var(--border-color)',
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Confirm Password Input */}
          <div style={{ marginBottom: '1.35rem' }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.82rem',
                fontWeight: 600,
                marginBottom: '0.35rem',
                color: 'var(--text-color)',
              }}
            >
              Confirm Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={16}
                style={{
                  position: 'absolute',
                  left: '12px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-secondary)',
                }}
              />
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                autoComplete="new-password"
                required
                style={{
                  width: '100%',
                  paddingLeft: '2.35rem',
                  paddingRight: '2.5rem',
                  height: '42px',
                  borderRadius: 'var(--radius-xs)',
                  border:
                    confirmPassword && confirmPassword !== password
                      ? '1px solid #ff3b30'
                      : '1px solid var(--border-color)',
                }}
              />
            </div>
            {confirmPassword && confirmPassword !== password && (
              <div style={{ color: '#ff3b30', fontSize: '0.74rem', marginTop: '0.3rem' }}>
                Passwords do not match
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="btn"
            disabled={loading || lookingUp}
            style={{
              width: '100%',
              height: '44px',
              fontSize: '0.92rem',
              fontWeight: 600,
              gap: '0.45rem',
            }}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="spin" /> Activating Account...
              </>
            ) : (
              <>
                <UserPlus size={16} /> Sign Up as Student
              </>
            )}
          </button>
        </form>

        {/* Footer */}
        <div
          style={{
            marginTop: '1.25rem',
            paddingTop: '1rem',
            borderTop: '1px solid var(--border-color)',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
            textAlign: 'center',
          }}
        >
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--apple-blue)', fontWeight: 600 }}>
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
