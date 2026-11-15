// src/components/ErrorMessage.jsx
import React from 'react';

export default function ErrorMessage({ message }) {
  if (!message) return null;
  return <div className="text-red" style={{ padding: '0.5rem 0', marginBottom: '1rem' }}>{message}</div>;
}