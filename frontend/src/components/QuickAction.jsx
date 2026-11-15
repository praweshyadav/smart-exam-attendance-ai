// src/components/QuickAction.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function QuickAction({ title, description, path }) {
  const navigate = useNavigate();
  return (
    <div className="card quick-action-card card-hover" onClick={() => navigate(path)}>
      <h3 style={{ fontSize: '1.1rem', fontWeight: '600' }}>{title}</h3>
      <p style={{ marginTop: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{description}</p>
    </div>
  );
}