import { type ReactNode, type ReactElement } from 'react';
import styles from './styles.module.css';

const WIRE_COLORS: Record<string, string> = {
  vcc: '#ef4444',
  '5v': '#ef4444',
  gnd: '#6b7280',
  do: '#3b82f6',
  out: '#3b82f6',
  s: '#3b82f6',
  pin1: '#3b82f6',
  pin2: '#6b7280',
};

function getColor(pin: string): string {
  const key = pin.toLowerCase().replace(/[^a-z0-9]/g, '');
  return WIRE_COLORS[key] || '#3b82f6';
}

/** Parse "GPIO 17 [pin 11]" into { label: "GPIO 17", pinNum: "pin 11" } */
function parseDest(to: string): { label: string; pinNum: string | null } {
  const match = to.match(/^(.+?)\s*\[(.+?)\]$/);
  if (match) return { label: match[1].trim(), pinNum: match[2].trim() };
  return { label: to, pinNum: null };
}

function WireRow({ pin, to }: { pin: string; to: string }): ReactElement {
  const color = getColor(pin);
  const dest = parseDest(to);
  return (
    <div className={styles.wireRow}>
      <span className={styles.wireDot} style={{ background: color, boxShadow: `0 0 6px ${color}40` }} />
      <strong className={styles.wirePin}>{pin}</strong>
      <span className={styles.wireLine}>
        <span className={styles.wireTrack} style={{ background: color }} />
        <span className={styles.wirePulse} style={{ background: `linear-gradient(90deg, transparent, ${color}, transparent)` }} />
        <span className={styles.wireArrowHead} style={{ borderLeftColor: color }} />
      </span>
      <span className={styles.destDot} style={{ background: color, boxShadow: `0 0 6px ${color}40` }} />
      <span className={styles.wireDest}>
        {dest.label}
        {dest.pinNum && <code className={styles.destPin}>{dest.pinNum}</code>}
      </span>
    </div>
  );
}

export function WireGroup({ children }: { children: ReactNode }): ReactElement {
  return (
    <div className={styles.wireGroup}>
      {children}
    </div>
  );
}

export default WireRow;
