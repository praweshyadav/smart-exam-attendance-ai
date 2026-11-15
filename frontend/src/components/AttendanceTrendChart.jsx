// src/components/AttendanceTrendChart.jsx
import React, { useState, useEffect, useMemo } from 'react';
import { Calendar, AlertCircle } from 'lucide-react';
import { getAttendanceTrend } from '../services/dashboardService';

export default function AttendanceTrendChart() {
  const [daysRange, setDaysRange] = useState(7);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [hoveredPoint, setHoveredPoint] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function fetchTrend() {
      setLoading(true);
      setError('');
      try {
        const res = await getAttendanceTrend(daysRange);
        if (isMounted) {
          setData(res.trend || []);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load attendance trend.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    fetchTrend();
    return () => {
      isMounted = false;
    };
  }, [daysRange]);

  const chartWidth = 600;
  const chartHeight = 150;
  const paddingX = 35;
  const paddingY = 16;

  const innerWidth = chartWidth - paddingX * 2;
  const innerHeight = chartHeight - paddingY * 2;

  const points = useMemo(() => {
    if (!data || data.length === 0) return [];
    if (data.length === 1) {
      const x = paddingX + innerWidth / 2;
      const y = paddingY + innerHeight - (data[0].percentage / 100) * innerHeight;
      return [{ ...data[0], x, y }];
    }
    return data.map((item, idx) => {
      const x = paddingX + (idx / (data.length - 1)) * innerWidth;
      const y = paddingY + innerHeight - (Math.min(100, Math.max(0, item.percentage)) / 100) * innerHeight;
      return { ...item, x, y };
    });
  }, [data, innerWidth, innerHeight]);

  const { linePath, areaPath } = useMemo(() => {
    if (points.length === 0) return { linePath: '', areaPath: '' };
    if (points.length === 1) {
      const p = points[0];
      return {
        linePath: `M ${p.x - 20} ${p.y} L ${p.x + 20} ${p.y}`,
        areaPath: `M ${p.x - 20} ${chartHeight - paddingY} L ${p.x - 20} ${p.y} L ${p.x + 20} ${p.y} L ${p.x + 20} ${chartHeight - paddingY} Z`,
      };
    }

    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = i > 0 ? points[i - 1] : points[i];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = i !== points.length - 2 ? points[i + 2] : p2;

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
    }

    const groundY = chartHeight - paddingY;
    const aPath = `${d} L ${points[points.length - 1].x} ${groundY} L ${points[0].x} ${groundY} Z`;

    return { linePath: d, areaPath: aPath };
  }, [points, chartHeight, paddingY]);

  return (
    <div className="card dashboard-chart-card compact-chart-card">
      <div className="chart-header">
        <div className="chart-header-left">
          <div className="chart-title-row">
            <h3 className="chart-title">Attendance Trend</h3>
            <span className="chart-tag">Working Days</span>
          </div>
        </div>

        <div className="chart-range-selector">
          <button
            className={`range-btn ${daysRange === 7 ? 'active' : ''}`}
            onClick={() => setDaysRange(7)}
          >
            7 Days
          </button>
          <button
            className={`range-btn ${daysRange === 30 ? 'active' : ''}`}
            onClick={() => setDaysRange(30)}
          >
            30 Days
          </button>
        </div>
      </div>

      <div className="chart-body compact-chart-body">
        {loading ? (
          <div className="chart-skeleton compact-skeleton" />
        ) : error ? (
          <div className="chart-error">
            <AlertCircle size={18} className="text-rose-500" />
            <p>{error}</p>
          </div>
        ) : data.length === 0 ? (
          <div className="chart-empty compact-empty">
            <Calendar size={24} className="chart-empty-icon" />
            <p>No attendance records in this range.</p>
          </div>
        ) : (
          <div className="svg-chart-container">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="attendance-trend-svg compact-svg"
            >
              <defs>
                <linearGradient id="purpleGradientCompact" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#0066cc" stopOpacity="0.28" />
                  <stop offset="85%" stopColor="#0066cc" stopOpacity="0.02" />
                  <stop offset="100%" stopColor="#0066cc" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines & Labels */}
              {[0, 50, 100].map((val) => {
                const y = paddingY + innerHeight - (val / 100) * innerHeight;
                return (
                  <g key={val} className="chart-grid-group">
                    <line
                      x1={paddingX}
                      y1={y}
                      x2={chartWidth - paddingX}
                      y2={y}
                      className="chart-grid-line"
                    />
                    <text
                      x={paddingX - 8}
                      y={y + 3}
                      className="chart-y-label"
                      textAnchor="end"
                    >
                      {val}%
                    </text>
                  </g>
                );
              })}

              {/* Area fill */}
              {areaPath && (
                <path
                  d={areaPath}
                  fill="url(#purpleGradientCompact)"
                  className="chart-area-fill"
                />
              )}

              {/* Line */}
              {linePath && (
                <path
                  d={linePath}
                  fill="none"
                  stroke="#0066cc"
                  strokeWidth="2.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="chart-line-stroke"
                />
              )}

              {/* Data points */}
              {points.map((pt, idx) => {
                const shouldShowLabel =
                  points.length <= 7 ||
                  idx % Math.ceil(points.length / 6) === 0 ||
                  idx === points.length - 1;

                return (
                  <g key={idx} className="chart-point-group">
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r={hoveredPoint?.date === pt.date ? 5.5 : 3.8}
                      fill="#FFFFFF"
                      stroke="#0066cc"
                      strokeWidth="2.5"
                      className="chart-data-circle"
                      onMouseEnter={() => setHoveredPoint(pt)}
                      onMouseLeave={() => setHoveredPoint(null)}
                      onTouchStart={() => setHoveredPoint(pt)}
                    />
                    {shouldShowLabel && (
                      <text
                        x={pt.x}
                        y={chartHeight - paddingY + 13}
                        className="chart-x-label"
                        textAnchor="middle"
                      >
                        {pt.day}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>

            {hoveredPoint && (
              <div
                className="chart-floating-tooltip compact-tooltip"
                style={{
                  left: `${(hoveredPoint.x / chartWidth) * 100}%`,
                  top: `${(hoveredPoint.y / chartHeight) * 100}%`,
                }}
              >
                <div className="tooltip-header">
                  <span className="tooltip-date">{hoveredPoint.date}</span>
                  <span className="tooltip-badge">{hoveredPoint.percentage}%</span>
                </div>
                <div className="tooltip-details">
                  <span>{hoveredPoint.present} / {hoveredPoint.totalEligible} Present</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
