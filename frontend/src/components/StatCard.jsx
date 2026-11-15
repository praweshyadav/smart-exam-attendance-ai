// src/components/StatCard.jsx
import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function StatCard({
  title, value, subtitle, icon: Icon,
  accentColor = '#0066cc', bgGradient, change,
  loading = false, onClick,
}) {
  if (loading) {
    return (
      <div className="stat-card skeleton-card">
        <div className="stat-skeleton-icon" />
        <div className="stat-skeleton-title" />
        <div className="stat-skeleton-value" />
      </div>
    );
  }

  const renderChangeBadge = () => {
    if (!change?.text) return null;
    if (change.type === 'increase') return <span className="stat-change-badge positive"><ArrowUpRight size={11} /> {change.text}</span>;
    if (change.type === 'decrease') return <span className="stat-change-badge negative"><ArrowDownRight size={11} /> {change.text}</span>;
    return <span className="stat-change-badge neutral">{change.text}</span>;
  };

  return (
    <div
      className="stat-card"
      style={{ '--card-accent': accentColor, cursor: onClick ? 'pointer' : 'default', transition: 'transform 0.15s, box-shadow 0.15s' }}
      onClick={onClick}
      onMouseEnter={e => { if (onClick) { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.1)'; } }}
      onMouseLeave={e => { if (onClick) { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; } }}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e => { if (e.key === 'Enter' || e.key === ' ') onClick(); }) : undefined}
    >
      <div className="stat-card-top">
        <span className="stat-card-title">{title}</span>
        <div className="stat-card-icon-box" style={{ background: bgGradient || `${accentColor}18`, color: accentColor }}>
          {Icon && <Icon size={18} />}
        </div>
      </div>
      <div className="stat-card-body">
        <div className="stat-card-value">{typeof value === 'number' ? value.toLocaleString() : value ?? '0'}</div>
        <div className="stat-card-bottom-row">
          <span className="stat-card-subtitle">{subtitle}</span>
          {renderChangeBadge()}
        </div>
      </div>
      <div className="stat-card-bottom-bar" style={{ backgroundColor: accentColor }} />
    </div>
  );
}
