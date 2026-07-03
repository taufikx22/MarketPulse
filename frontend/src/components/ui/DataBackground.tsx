'use client';

import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

export default function DataBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: Particle[] = [];
    const maxParticles = 90;
    const connectionDist = 160;

    const resizeCanvas = () => {
      canvas.width = canvas.parentElement?.offsetWidth || window.innerWidth;
      canvas.height = canvas.parentElement?.offsetHeight || window.innerHeight;
      initParticles();
    };

    const initParticles = () => {
      particles = [];
      for (let i = 0; i < maxParticles; i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 1.1, // Drifts noticeably faster
          vy: (Math.random() - 0.5) * 1.1,
          radius: Math.random() * 2.2 + 1.8, // Larger nodes
        });
      }
    };

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Determine current theme color for drawing
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const colorHex = isDark ? '255, 255, 255' : '12, 12, 14';
      const accentHex = '255, 95, 31'; // Coral Accent RGB

      // Draw Grid dots in background
      ctx.fillStyle = `rgba(${colorHex}, 0.05)`;
      const gridSize = 45;
      for (let x = 0; x < canvas.width; x += gridSize) {
        for (let y = 0; y < canvas.height; y += gridSize) {
          ctx.fillRect(x, y, 1, 1);
        }
      }

      // Update & Draw particles
      particles.forEach((p, idx) => {
        p.x += p.vx;
        p.y += p.vy;

        // Bounce borders
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        // Draw particle
        ctx.beginPath();
        // A few particles use the coral accent color
        if (idx % 4 === 0) { // 25% of particles are accent colored
          ctx.fillStyle = `rgba(${accentHex}, 0.95)`;
          ctx.arc(p.x, p.y, p.radius + 1.2, 0, Math.PI * 2);
        } else {
          ctx.fillStyle = `rgba(${colorHex}, 0.65)`;
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        }
        ctx.fill();

        // Draw lines to neighboring particles
        for (let j = idx + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < connectionDist) {
            const alpha = (1 - dist / connectionDist) * 0.48; // Raised connecting line alpha for strong visibility
            ctx.beginPath();
            if (idx % 4 === 0 || j % 4 === 0) {
              ctx.strokeStyle = `rgba(${accentHex}, ${alpha * 1.8})`;
            } else {
              ctx.strokeStyle = `rgba(${colorHex}, ${alpha})`;
            }
            ctx.lineWidth = 1.1; // Thicker lines
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    // Initialize
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
    draw();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 0,
        opacity: 0.8,
      }}
    />
  );
}
