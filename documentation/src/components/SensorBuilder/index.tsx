import { useState, type ReactNode } from 'react';
import styles from './styles.module.css';

interface SensorConfig {
  className: string;
  sensorType: string;
  name: string;
  defaultGpio: number;
  module: string;
  icon: string;
  hasCalibration: boolean;
}

const ICONS = ['magnet', 'eye', 'zap', 'rotate', 'hand', 'gate', 'circle', 'wrench'];

function sanitize(str: string): string {
  return str.replace(/[^a-zA-Z0-9\s]/g, '').trim();
}

function toSnakeCase(str: string): string {
  const clean = sanitize(str);
  return clean ? clean.replace(/\s+/g, '_').toLowerCase() : 'my_sensor';
}

function toPascalCase(str: string): string {
  const clean = sanitize(str);
  if (!clean) return 'MySensor';
  return clean
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join('');
}

/** Escape characters that would break Python string literals */
function pyStr(str: string): string {
  return str.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function clampGpio(val: number): number {
  if (Number.isNaN(val)) return 18;
  return Math.max(0, Math.min(27, Math.round(val)));
}

function generateCode(config: SensorConfig): string {
  const lines = [
    `# client/modules/sensors/${config.sensorType}.py`,
    `from .base import BaseSensor`,
    ``,
    ``,
    `class ${config.className}(BaseSensor):`,
    `    name = "${pyStr(config.name)}"`,
    `    sensor_type = "${config.sensorType}"`,
    `    default_gpio = ${config.defaultGpio}`,
    `    module = "${pyStr(config.module)}"`,
    `    description = "TODO: describe what this sensor does"`,
    `    icon = "${config.icon}"`,
    `    wiring = (`,
    `        {"pin": "VCC", "connect": "3V3 [pin 17]"},`,
    `        {"pin": "GND", "connect": "GND [pin 14]"},`,
    `        {"pin": "DO", "connect": "GPIO ${config.defaultGpio} [pin ??]"},`,
    `    )`,
  ];

  if (config.hasCalibration) {
    lines.push(
      `    calibration_schema = (`,
      `        {`,
      `            "key": "sensitivity",`,
      `            "name": "Sensitivity",`,
      `            "type": "range",`,
      `            "min": 1,`,
      `            "max": 100,`,
      `            "default": 50,`,
      `            "step": 1,`,
      `            "description": "How sensitive the sensor is",`,
      `            "labels": {"min": "Low", "max": "High"},`,
      `        },`,
      `    )`,
    );
  }

  lines.push(
    ``,
    `    def __init__(self, gpio=None, **kwargs):`,
    `        super().__init__(gpio, **kwargs)`,
  );

  if (config.hasCalibration) {
    lines.push(`        self._sensitivity = kwargs.get("sensitivity", 50)`);
  }

  lines.push(
    ``,
    `    def start(self, on_trigger, on_release):`,
    `        self._on_trigger = on_trigger`,
    `        self._on_release = on_release`,
    `        self._running = True`,
    `        # TODO: set up GPIO monitoring here`,
    ``,
    `    def stop(self):`,
    `        self._running = False`,
    `        # TODO: clean up GPIO resources`,
    ``,
    `    def read_value(self):`,
    `        return self._read_gpio(pull_up=True)`,
  );

  return lines.join('\n');
}

function generateRegistry(config: SensorConfig): string {
  return [
    `# Add to client/modules/sensors/__init__.py`,
    `from .${config.sensorType} import ${config.className}`,
    ``,
    `SENSOR_REGISTRY: dict[str, type] = {`,
    `    # ... existing sensors ...`,
    `    "${config.sensorType}": ${config.className},`,
    `}`,
  ].join('\n');
}

export default function SensorBuilder(): ReactNode {
  const [name, setName] = useState('My Sensor');
  const [gpio, setGpio] = useState(18);
  const [module, setModule] = useState('XY-100');
  const [icon, setIcon] = useState('zap');
  const [hasCalibration, setHasCalibration] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const safeGpio = clampGpio(gpio);
  const config: SensorConfig = {
    className: toPascalCase(name),
    sensorType: toSnakeCase(name),
    name: name || 'My Sensor',
    defaultGpio: safeGpio,
    module,
    icon,
    hasCalibration,
  };

  const code = generateCode(config);
  const registry = generateRegistry(config);

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Fallback for insecure contexts
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className={styles.container}>
      <div className={styles.form}>
        <div className={styles.field}>
          <label>Sensor name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Sensor"
          />
          <span className={styles.hint}>
            Class: <code>{config.className}</code> | Type: <code>{config.sensorType}</code>
          </span>
        </div>

        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label>Default GPIO (BCM)</label>
            <input
              type="number"
              min={0}
              max={27}
              value={gpio}
              onChange={(e) => setGpio(Number(e.target.value))}
            />
          </div>
          <div className={styles.field}>
            <label>Module ID</label>
            <input
              type="text"
              value={module}
              onChange={(e) => setModule(e.target.value)}
              placeholder="KY-XXX"
            />
          </div>
        </div>

        <div className={styles.field}>
          <label>Icon</label>
          <div className={styles.iconGrid}>
            {ICONS.map((ic) => (
              <button
                key={ic}
                className={`${styles.iconBtn} ${icon === ic ? styles.active : ''}`}
                onClick={() => setIcon(ic)}
                title={ic}
                aria-label={`Icon: ${ic}`}
                aria-pressed={icon === ic}
              >
                {ic}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.field}>
          <label className={styles.checkLabel}>
            <input
              type="checkbox"
              checked={hasCalibration}
              onChange={(e) => setHasCalibration(e.target.checked)}
            />
            Include calibration schema
          </label>
        </div>
      </div>

      <div className={styles.output}>
        <div className={styles.codeBlock}>
          <div className={styles.codeHeader}>
            <span>{config.sensorType}.py</span>
            <button
              className={`${styles.copyBtn} ${copied === 'sensor' ? styles.copyBtnSuccess : ''}`}
              onClick={() => copyToClipboard(code, 'sensor')}
            >
              {copied === 'sensor' ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre className={styles.code}><code>{code}</code></pre>
        </div>

        <div className={styles.codeBlock}>
          <div className={styles.codeHeader}>
            <span>__init__.py registration</span>
            <button
              className={`${styles.copyBtn} ${copied === 'registry' ? styles.copyBtnSuccess : ''}`}
              onClick={() => copyToClipboard(registry, 'registry')}
            >
              {copied === 'registry' ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <pre className={styles.code}><code>{registry}</code></pre>
        </div>
      </div>
    </div>
  );
}
