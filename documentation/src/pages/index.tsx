import clsx from 'clsx';
import { useRef, useCallback, useEffect, useState } from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

// --- WebGL noise field (deepest layer) ---
const NOISE_VERT = `
attribute vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
`;

const NOISE_FRAG = `
precision mediump float;
uniform float u_time;
uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_dark;

// Simplex-style hash
vec3 mod289(vec3 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
vec2 mod289v2(vec2 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }

float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                     -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289v2(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
  m = m*m; m = m*m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_resolution;
  vec2 p = uv * 3.0;

  // Slow drift
  float t = u_time * 0.08;
  float n1 = snoise(p + vec2(t, t * 0.7)) * 0.5 + 0.5;
  float n2 = snoise(p * 2.0 + vec2(-t * 0.5, t * 0.3)) * 0.5 + 0.5;
  float n = n1 * 0.6 + n2 * 0.4;

  // Mouse proximity warp
  vec2 mouse = u_mouse / u_resolution;
  float md = distance(uv, mouse);
  float warp = smoothstep(0.35, 0.0, md) * 0.15;
  n += warp;

  // Dark mode: very subtle blue-tinted noise on dark bg
  // Light mode: very subtle white-tinted noise on blue bg
  float intensity = mix(0.025, 0.04, u_dark);
  vec3 tint = mix(vec3(1.0), vec3(0.3, 0.5, 1.0), u_dark);
  vec3 color = tint * n * intensity;

  float alpha = n * intensity * 8.0;
  gl_FragColor = vec4(tint * n, alpha);
}
`;

function useNoiseField(canvasRef: React.RefObject<HTMLCanvasElement | null>, mouseRef: React.RefObject<{x: number, y: number}>) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const glOpts = { alpha: true, premultipliedAlpha: false };
    const gl = canvas.getContext('webgl2', glOpts) || canvas.getContext('webgl', glOpts);
    if (!gl) return;
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.clearColor(0, 0, 0, 0);

    function createShader(g: WebGLRenderingContext, type: number, src: string) {
      const s = g.createShader(type)!;
      g.shaderSource(s, src);
      g.compileShader(s);
      return s;
    }

    const vs = createShader(gl, gl.VERTEX_SHADER, NOISE_VERT);
    const fs = createShader(gl, gl.FRAGMENT_SHADER, NOISE_FRAG);
    const prog = gl.createProgram()!;
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
    const aPos = gl.getAttribLocation(prog, 'a_pos');
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    const uTime = gl.getUniformLocation(prog, 'u_time');
    const uRes = gl.getUniformLocation(prog, 'u_resolution');
    const uMouse = gl.getUniformLocation(prog, 'u_mouse');
    const uDark = gl.getUniformLocation(prog, 'u_dark');

    let raf: number;
    let running = true;

    function resize() {
      const dpr = Math.min(devicePixelRatio, 1.5); // cap for perf
      canvas.width = canvas.clientWidth * dpr;
      canvas.height = canvas.clientHeight * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const startTime = performance.now();

    function render() {
      if (!running) return;
      const dark = document.documentElement.dataset.theme !== 'light' ? 1.0 : 0.0;
      const t = (performance.now() - startTime) / 1000;

      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.uniform1f(uTime, prefersReduced ? 0 : t);
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform2f(uMouse, (mouseRef.current?.x ?? 0.5) * canvas.width, (1 - (mouseRef.current?.y ?? 0.5)) * canvas.height);
      gl.uniform1f(uDark, dark);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      raf = requestAnimationFrame(render);
    }

    // Pause when off-screen
    const io = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { running = true; render(); }
      else { running = false; cancelAnimationFrame(raf); }
    });
    io.observe(canvas);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
      gl.deleteProgram(prog);
      gl.deleteShader(vs);
      gl.deleteShader(fs);
      gl.deleteBuffer(buf);
    };
  }, []);
}

// --- Canvas grid with reactive glow ---
function useReactiveGrid(canvasRef: React.RefObject<HTMLCanvasElement | null>, mouseRef: React.RefObject<{x: number, y: number}>, parallaxRef: React.RefObject<{x: number, y: number}>) {
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const CELL = 48;
    let raf: number;
    let running = true;

    function resize() {
      const dpr = Math.min(devicePixelRatio, 2);
      canvas.width = canvas.clientWidth * dpr;
      canvas.height = canvas.clientHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    function render() {
      if (!running) return;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      const dark = document.documentElement.dataset.theme !== 'light';
      const mx = (mouseRef.current?.x ?? -1) * w;
      const my = (mouseRef.current?.y ?? -1) * h;
      const px = prefersReduced ? 0 : (parallaxRef.current?.x ?? 0);
      const py = prefersReduced ? 0 : (parallaxRef.current?.y ?? 0);

      ctx.clearRect(0, 0, w, h);

      const baseAlpha = dark ? 0.035 : 0.08;
      const brightAlpha = dark ? 0.18 : 0.2;
      const glowRadius = 200;
      const dotRadius = 160;

      // Offset for parallax
      const ox = px % CELL;
      const oy = py % CELL;

      // Draw vertical lines
      for (let x = ox - CELL; x <= w + CELL; x += CELL) {
        const dist = mx >= 0 ? Math.abs(x - mx) : Infinity;
        const proximity = Math.max(0, 1 - dist / glowRadius);
        const alpha = baseAlpha + (brightAlpha - baseAlpha) * proximity;
        ctx.strokeStyle = dark
          ? `rgba(255, 255, 255, ${alpha})`
          : `rgba(255, 255, 255, ${alpha})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }

      // Draw horizontal lines
      for (let y = oy - CELL; y <= h + CELL; y += CELL) {
        const dist = my >= 0 ? Math.abs(y - my) : Infinity;
        const proximity = Math.max(0, 1 - dist / glowRadius);
        const alpha = baseAlpha + (brightAlpha - baseAlpha) * proximity;
        ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Draw intersection dots near cursor
      if (mx >= 0 && my >= 0) {
        for (let x = ox - CELL; x <= w + CELL; x += CELL) {
          for (let y = oy - CELL; y <= h + CELL; y += CELL) {
            const dist = Math.hypot(x - mx, y - my);
            if (dist < dotRadius) {
              const proximity = 1 - dist / dotRadius;
              const dotAlpha = proximity * (dark ? 0.5 : 0.4);
              const dotSize = 1.5 + proximity * 1.5;
              ctx.fillStyle = dark
                ? `rgba(77, 148, 255, ${dotAlpha})`
                : `rgba(255, 255, 255, ${dotAlpha})`;
              ctx.beginPath();
              ctx.arc(x, y, dotSize, 0, Math.PI * 2);
              ctx.fill();
            }
          }
        }
      }

      raf = requestAnimationFrame(render);
    }

    const io = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { running = true; render(); }
      else { running = false; cancelAnimationFrame(raf); }
    });
    io.observe(canvas);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
    };
  }, []);
}

// --- Main hero component ---
function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  const heroRef = useRef<HTMLElement>(null);
  const noiseCanvasRef = useRef<HTMLCanvasElement>(null);
  const gridCanvasRef = useRef<HTMLCanvasElement>(null);
  const mouseNorm = useRef({ x: 0.5, y: 0.5 });
  const parallax = useRef({ x: 0, y: 0 });
  const [mouseActive, setMouseActive] = useState(false);

  useNoiseField(noiseCanvasRef, mouseNorm);
  useReactiveGrid(gridCanvasRef, mouseNorm, parallax);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLElement>) => {
    const el = heroRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width;
    const ny = (e.clientY - rect.top) / rect.height;

    mouseNorm.current = { x: nx, y: ny };
    parallax.current = { x: (nx - 0.5) * 12, y: (ny - 0.5) * 12 };

    if (!mouseActive) setMouseActive(true);
  }, [mouseActive]);

  const handleMouseLeave = useCallback(() => {
    mouseNorm.current = { x: 0.5, y: 0.5 };
    parallax.current = { x: 0, y: 0 };
    setMouseActive(false);
  }, []);

  return (
    <header
      ref={heroRef}
      className={clsx('hero hero--primary', styles.heroBanner)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Layer 1: WebGL noise field */}
      <canvas ref={noiseCanvasRef} className={styles.noiseCanvas} />
      {/* Layer 2: Canvas reactive grid */}
      <canvas
        ref={gridCanvasRef}
        className={clsx(styles.gridCanvas, mouseActive && styles.gridCanvasActive)}
      />
      {/* Layer 3: conic border ring */}
      <div className={styles.heroBorderRing} />
      {/* Layer 4: scan-lines */}
      <div className={styles.heroScanlines} />
      {/* Layer 4: vignette */}
      <div className={styles.heroVignette} />
      {/* Layer 5: content */}
      <div className="container" style={{ position: 'relative', zIndex: 5 }}>
        <Heading as="h1" className={clsx('hero__title', styles.heroTitle)}>
          {siteConfig.title}
        </Heading>
        <hr className={styles.heroAccent} />
        <p className={clsx('hero__subtitle', styles.heroSubtitle)}>
          {siteConfig.tagline}
        </p>
        <div className={clsx(styles.buttons, styles.heroCta)}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            Get started with Security-Cam
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  return (
    <Layout
      title={`Documentation`}
      description="Security-Cam is a simple and easy to use security camera software."
    >
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
