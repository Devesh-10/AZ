import React, { useEffect, useState, useCallback } from 'react';
import { connections } from '../data/mapData';
import '../styles/FlowConnections.css';

interface Point {
  x: number;
  y: number;
}

interface ArrowPath {
  path: string;
  color: string;
  arrowPath: string;
}

const FlowConnections: React.FC = () => {
  const [arrows, setArrows] = useState<ArrowPath[]>([]);

  const calculateArrows = useCallback(() => {
    const newArrows: ArrowPath[] = [];
    const mapCanvas = document.querySelector('.map-canvas');

    if (!mapCanvas) return;

    const canvasRect = mapCanvas.getBoundingClientRect();
    const scrollLeft = mapCanvas.scrollLeft;

    connections.forEach((connection) => {
      const fromEl = document.getElementById(connection.from);
      const toEl = document.getElementById(connection.to);

      if (fromEl && toEl) {
        const fromRect = fromEl.getBoundingClientRect();
        const toRect = toEl.getBoundingClientRect();

        // Calculate positions relative to the map canvas
        const start: Point = {
          x: fromRect.right - canvasRect.left + scrollLeft,
          y: fromRect.top + fromRect.height / 2 - canvasRect.top,
        };

        const end: Point = {
          x: toRect.left - canvasRect.left + scrollLeft,
          y: toRect.top + toRect.height / 2 - canvasRect.top,
        };

        // Calculate control points for bezier curve
        const midX = (start.x + end.x) / 2;
        const controlPoint1: Point = { x: midX, y: start.y };
        const controlPoint2: Point = { x: midX, y: end.y };

        // Create bezier curve path
        const path = `M ${start.x} ${start.y} C ${controlPoint1.x} ${controlPoint1.y}, ${controlPoint2.x} ${controlPoint2.y}, ${end.x} ${end.y}`;

        // Create arrowhead
        const arrowSize = 8;
        const angle = Math.atan2(end.y - controlPoint2.y, end.x - controlPoint2.x);
        const arrowPath = `
          M ${end.x} ${end.y}
          L ${end.x - arrowSize * Math.cos(angle - Math.PI / 6)} ${end.y - arrowSize * Math.sin(angle - Math.PI / 6)}
          M ${end.x} ${end.y}
          L ${end.x - arrowSize * Math.cos(angle + Math.PI / 6)} ${end.y - arrowSize * Math.sin(angle + Math.PI / 6)}
        `;

        newArrows.push({
          path,
          color: connection.color,
          arrowPath,
        });
      }
    });

    setArrows(newArrows);
  }, []);

  useEffect(() => {
    // Initial calculation with delay to ensure DOM is ready
    const timer = setTimeout(calculateArrows, 100);

    // Recalculate on window resize
    window.addEventListener('resize', calculateArrows);

    // Recalculate on scroll
    const mapCanvas = document.querySelector('.map-canvas');
    if (mapCanvas) {
      mapCanvas.addEventListener('scroll', calculateArrows);
    }

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', calculateArrows);
      if (mapCanvas) {
        mapCanvas.removeEventListener('scroll', calculateArrows);
      }
    };
  }, [calculateArrows]);

  return (
    <svg className="flow-connections">
      {arrows.map((arrow, index) => (
        <g key={index}>
          <path
            d={arrow.path}
            stroke={arrow.color}
            strokeWidth="2"
            fill="none"
          />
          <path
            d={arrow.arrowPath}
            stroke={arrow.color}
            strokeWidth="2"
            fill="none"
          />
        </g>
      ))}
    </svg>
  );
};

export default FlowConnections;
