import { useState, useRef, useEffect, type ReactNode } from 'react';
import styles from './styles.module.css';

const PINS: [number, string, string][] = [
  [1, '3V3 Power', 'power3v3'],
  [2, '5V Power', 'power5v'],
  [3, 'GPIO 2 (I2C SDA)', 'i2c'],
  [4, '5V Power', 'power5v'],
  [5, 'GPIO 3 (I2C SCL)', 'i2c'],
  [6, 'Ground', 'gnd'],
  [7, 'GPIO 4', 'gpio'],
  [8, 'GPIO 14 (TX)', 'uart'],
  [9, 'Ground', 'gnd'],
  [10, 'GPIO 15 (RX)', 'uart'],
  [11, 'GPIO 17', 'gpio'],
  [12, 'GPIO 18 (PCM)', 'pcm'],
  [13, 'GPIO 27', 'gpio'],
  [14, 'Ground', 'gnd'],
  [15, 'GPIO 22', 'gpio'],
  [16, 'GPIO 23', 'gpio'],
  [17, '3V3 Power', 'power3v3'],
  [18, 'GPIO 24', 'gpio'],
  [19, 'GPIO 10 (MOSI)', 'spi'],
  [20, 'Ground', 'gnd'],
  [21, 'GPIO 9 (MISO)', 'spi'],
  [22, 'GPIO 25', 'gpio'],
  [23, 'GPIO 11 (SCLK)', 'spi'],
  [24, 'GPIO 8 (CE0)', 'spi'],
  [25, 'Ground', 'gnd'],
  [26, 'GPIO 7 (CE1)', 'spi'],
  [27, 'GPIO 0 (ID SD)', 'eeprom'],
  [28, 'GPIO 1 (ID SC)', 'eeprom'],
  [29, 'GPIO 5', 'gpio'],
  [30, 'Ground', 'gnd'],
  [31, 'GPIO 6', 'gpio'],
  [32, 'GPIO 12 (PWM0)', 'gpio'],
  [33, 'GPIO 13 (PWM1)', 'gpio'],
  [34, 'Ground', 'gnd'],
  [35, 'GPIO 19 (PCM)', 'pcm'],
  [36, 'GPIO 16', 'gpio'],
  [37, 'GPIO 26', 'gpio'],
  [38, 'GPIO 20 (PCM)', 'pcm'],
  [39, 'Ground', 'gnd'],
  [40, 'GPIO 21 (PCM)', 'pcm'],
];

interface SensorWiring {
  name: string;
  id: string;
  pins: { physical: number; wire: string; color: string }[];
}

const GND_COLOR = '#6b7280';

const SENSORS: SensorWiring[] = [
  { name: 'Reed Switch (KY-025)', id: 'reed', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 15, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Mini Reed (KY-021)', id: 'mini-reed', pins: [
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 38, wire: 'S', color: '#3b82f6' },
  ]},
  { name: 'Hall Magnetic (KY-003)', id: 'hall', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 33, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'PIR Motion (HC-SR501)', id: 'pir', pins: [
    { physical: 2, wire: 'VCC', color: '#ef4444' },
    { physical: 6, wire: 'GND', color: GND_COLOR },
    { physical: 11, wire: 'OUT', color: '#3b82f6' },
  ]},
  { name: 'Vibration (KY-002)', id: 'vibration', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 29, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Knock (KY-031)', id: 'knock', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 35, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Light Gate (KY-010)', id: 'light-gate', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 31, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Tilt Switch (KY-017)', id: 'tilt', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 37, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Touch (KY-036)', id: 'touch', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 36, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Hall Linear (KY-024)', id: 'hall-linear', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 32, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'IR Proximity (KY-032)', id: 'ir-proximity', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 18, wire: 'OUT', color: '#3b82f6' },
  ]},
  { name: 'Tilt Ball (KY-020)', id: 'tilt-ball', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 22, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Sound Big (KY-037)', id: 'sound-big', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 16, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Sound Small (KY-038)', id: 'sound-small', pins: [
    { physical: 17, wire: 'VCC', color: '#ef4444' },
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 24, wire: 'DO', color: '#3b82f6' },
  ]},
  { name: 'Button', id: 'button', pins: [
    { physical: 14, wire: 'GND', color: GND_COLOR },
    { physical: 13, wire: 'S', color: '#3b82f6' },
  ]},
];

const TYPE_COLORS: Record<string, string> = {
  power3v3: '#f59e0b', power5v: '#ef4444', gnd: '#6b7280',
  gpio: '#22c55e', spi: '#ec4899', i2c: '#3b82f6',
  uart: '#8b5cf6', pcm: '#06b6d4', eeprom: '#3b82f6',
};

function Pin({ pin, label, type, side, highlighted, wireColor }: {
  pin: number; label: string; type: string; side: 'left' | 'right';
  highlighted: boolean; wireColor: string | null;
}) {
  const baseColor = TYPE_COLORS[type] || '#666';
  const dotColor = highlighted && wireColor ? wireColor : baseColor;

  return (
    <div className={`${styles.pin} ${styles[side]} ${highlighted ? styles.highlighted : ''}`}>
      {side === 'left' && <span className={styles.pinLabel}>{label}</span>}
      <span
        className={styles.pinDot}
        style={{
          background: dotColor,
          boxShadow: highlighted
            ? `0 0 16px 4px ${dotColor}80, 0 0 6px 2px ${dotColor}50, 0 0 30px 6px ${dotColor}25`
            : `inset 0 1px 2px rgba(0,0,0,0.2)`,
        }}
      >
        {pin}
      </span>
      {side === 'right' && <span className={styles.pinLabel}>{label}</span>}
    </div>
  );
}

export default function GpioPinout(): ReactNode {
  const [activeSensor, setActiveSensor] = useState<string | null>('reed');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!dropdownOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [dropdownOpen]);

  const activeWiring = SENSORS.find((s) => s.id === activeSensor);
  const highlightedPins = new Map<number, string>();
  if (activeWiring) {
    for (const p of activeWiring.pins) {
      highlightedPins.set(p.physical, p.color);
    }
  }

  const rows: ReactNode[] = [];
  for (let i = 0; i < PINS.length; i += 2) {
    const [lp, ll, lt] = PINS[i];
    const [rp, rl, rt] = PINS[i + 1];
    rows.push(
      <div className={styles.pinRow} key={lp}>
        <Pin pin={lp} label={ll} type={lt} side="left"
          highlighted={highlightedPins.has(lp)} wireColor={highlightedPins.get(lp) || null} />
        <Pin pin={rp} label={rl} type={rt} side="right"
          highlighted={highlightedPins.has(rp)} wireColor={highlightedPins.get(rp) || null} />
      </div>,
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.dropdown} ref={dropdownRef}>
        <button
          className={styles.dropdownTrigger}
          onClick={() => setDropdownOpen(!dropdownOpen)}
          aria-expanded={dropdownOpen}
          aria-haspopup="listbox"
        >
          <span>{activeWiring ? activeWiring.name : 'Select a sensor...'}</span>
          <span className={`${styles.dropdownArrow} ${dropdownOpen ? styles.open : ''}`}>&#9662;</span>
        </button>
        {dropdownOpen && (
          <ul className={styles.dropdownMenu} role="listbox">
            {SENSORS.map((s) => (
              <li key={s.id} role="option" aria-selected={activeSensor === s.id}
                className={`${styles.dropdownItem} ${activeSensor === s.id ? styles.selected : ''}`}
                onClick={() => { setActiveSensor(activeSensor === s.id ? null : s.id); setDropdownOpen(false); }}
              >{s.name}</li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.boardOuter}>
        {/* PCB board */}
        <div className={`${styles.board} ${activeSensor ? styles.hasSelection : ''}`}>
          {/* Corner screw holes */}
          <div className={`${styles.screw} ${styles.screwTL}`} />
          <div className={`${styles.screw} ${styles.screwTR}`} />
          <div className={`${styles.screw} ${styles.screwBL}`} />
          <div className={`${styles.screw} ${styles.screwBR}`} />

          {/* Subtle grid texture */}
          <div className={styles.traces} aria-hidden="true" />

          {/* Pin header area */}
          <div className={styles.pinHeader}>
            {rows}
          </div>

          {/* Orientation hint */}
          <div className={styles.orientHint}>
            <span className={styles.orientArrow}>{'\u2190'}</span> HDMI port(s) on the left, GPIO on the right
          </div>
        </div>
      </div>

      {activeWiring && (
        <div className={styles.wiringInfo}>
          <strong>{activeWiring.name}</strong>
          <div className={styles.wiringPins}>
            {activeWiring.pins.map((p) => {
              const pinData = PINS.find(([num]) => num === p.physical);
              const piLabel = pinData ? pinData[1] : `Pin ${p.physical}`;
              return (
                <span key={p.physical} className={styles.wiringChip}
                  style={{ borderLeftColor: p.color }}>
                  <span className={styles.wireColorDot} style={{ background: p.color }} />
                  <code className={styles.wireName}>{p.wire}</code>
                  <span className={styles.wireArrow}>{'\u2192'}</span>
                  <code className={styles.wireName}>{piLabel}</code>
                  <span className={styles.wiringPinNum}>pin {p.physical}</span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      <div className={styles.legend}>
        {Object.entries({
          GPIO: 'gpio', SPI: 'spi', 'I\u00B2C': 'i2c', UART: 'uart',
          PCM: 'pcm', GND: 'gnd', '5V': 'power5v', '3.3V': 'power3v3',
        }).map(([name, type]) => (
          <span key={type} className={styles.legendItem}>
            <span className={styles.legendDot} style={{ background: TYPE_COLORS[type] }} />
            {name}
          </span>
        ))}
      </div>
    </div>
  );
}
