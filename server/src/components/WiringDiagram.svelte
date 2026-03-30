<script lang="ts">
  /**
   * Programmatic SVG wiring diagram.
   *
   * Reads the sensor's `wiring` metadata and draws:
   *  - A cropped view of the Pi GPIO header (only rows near active pins)
   *  - A sensor module with labeled pins
   *  - Color-coded wires connecting them
   *  - A color legend
   *
   * The connect strings follow the format: "GPIO 22 [pin 15]", "3V3 [pin 17]", "GND [pin 14]", "5V [pin 2]"
   */

  interface WiringRow {
    pin: string;
    connect: string;
  }

  interface Props {
    wiring: WiringRow[];
    sensorName: string;
    module: string;
  }

  let { wiring, sensorName, module }: Props = $props();

  // ── Pi GPIO 40-pin header layout (BCM) ──
  const PIN_MAP: Record<number, { type: "gpio"; bcm: number } | { type: "3v3" } | { type: "5v" } | { type: "gnd" } | { type: "id" }> = {
    1:  { type: "3v3" },   2:  { type: "5v" },
    3:  { type: "gpio", bcm: 2 },   4:  { type: "5v" },
    5:  { type: "gpio", bcm: 3 },   6:  { type: "gnd" },
    7:  { type: "gpio", bcm: 4 },   8:  { type: "gpio", bcm: 14 },
    9:  { type: "gnd" },  10: { type: "gpio", bcm: 15 },
    11: { type: "gpio", bcm: 17 }, 12: { type: "gpio", bcm: 18 },
    13: { type: "gpio", bcm: 27 }, 14: { type: "gnd" },
    15: { type: "gpio", bcm: 22 }, 16: { type: "gpio", bcm: 23 },
    17: { type: "3v3" },  18: { type: "gpio", bcm: 24 },
    19: { type: "gpio", bcm: 10 }, 20: { type: "gnd" },
    21: { type: "gpio", bcm: 9 },  22: { type: "gpio", bcm: 25 },
    23: { type: "gpio", bcm: 11 }, 24: { type: "gpio", bcm: 8 },
    25: { type: "gnd" },  26: { type: "gpio", bcm: 7 },
    27: { type: "id" },   28: { type: "id" },
    29: { type: "gpio", bcm: 5 },  30: { type: "gnd" },
    31: { type: "gpio", bcm: 6 },  32: { type: "gpio", bcm: 12 },
    33: { type: "gpio", bcm: 13 }, 34: { type: "gnd" },
    35: { type: "gpio", bcm: 19 }, 36: { type: "gpio", bcm: 16 },
    37: { type: "gpio", bcm: 26 }, 38: { type: "gpio", bcm: 20 },
    39: { type: "gnd" },  40: { type: "gpio", bcm: 21 },
  };

  function pinColor(physPin: number): string {
    const info = PIN_MAP[physPin];
    if (!info) return "#555";
    switch (info.type) {
      case "3v3": return "#f59e0b";
      case "5v": return "#ef4444";
      case "gnd": return "#374151";
      case "gpio": return "#22c55e";
      case "id": return "#6b7280";
      default: return "#555";
    }
  }

  function pinLabel(physPin: number): string {
    const info = PIN_MAP[physPin];
    if (!info) return "";
    switch (info.type) {
      case "3v3": return "3V3";
      case "5v": return "5V";
      case "gnd": return "GND";
      case "gpio": return `GPIO ${info.bcm}`;
      case "id": return "ID";
      default: return "";
    }
  }

  const WIRE_COLORS: Record<string, string> = {
    "3v3": "#f59e0b",
    "5v": "#ef4444",
    "gnd": "#64748b",
    "gpio": "#4d94ff",
  };

  const WIRE_LABELS: Record<string, string> = {
    "3v3": "3.3V Power",
    "5v": "5V Power",
    "gnd": "Ground",
    "gpio": "Signal",
  };

  function parseConnect(connect: string): { physPin: number; type: string } | null {
    const pinMatch = connect.match(/\[pin\s+(\d+)\]/);
    if (!pinMatch) return null;
    const physPin = parseInt(pinMatch[1]);
    if (connect.startsWith("3V3") || connect.startsWith("3.3V")) return { physPin, type: "3v3" };
    if (connect.startsWith("5V")) return { physPin, type: "5v" };
    if (connect.startsWith("GND")) return { physPin, type: "gnd" };
    return { physPin, type: "gpio" };
  }

  // ── Layout constants ──
  const PIN_R = 5;
  const PIN_SPACING = 16;
  const COL_GAP = 16;
  const CONTEXT_ROWS = 2; // extra rows above/below active range

  function physPinRow(physPin: number): number {
    return Math.floor((physPin - 1) / 2);
  }

  interface Wire {
    sensorPin: string;
    physPin: number;
    type: string;
    color: string;
    row: number;
  }

  // Parse all wires and determine the visible row range
  let wires = $derived((() => {
    const result: Wire[] = [];
    wiring.forEach((row) => {
      const p = parseConnect(row.connect);
      if (!p) return;
      result.push({
        sensorPin: row.pin,
        physPin: p.physPin,
        type: p.type,
        color: WIRE_COLORS[p.type] ?? WIRE_COLORS.gpio,
        row: physPinRow(p.physPin),
      });
    });
    return result;
  })());

  // Visible row range (cropped to active pins + context)
  let minRow = $derived(wires.length > 0 ? Math.max(0, Math.min(...wires.map(w => w.row)) - CONTEXT_ROWS) : 0);
  let maxRow = $derived(wires.length > 0 ? Math.min(19, Math.max(...wires.map(w => w.row)) + CONTEXT_ROWS) : 19);
  let visibleRows = $derived(maxRow - minRow + 1);

  // Positions within the cropped view
  const PAD_TOP = 32;
  const PAD_LEFT = 16;
  const HEADER_X = PAD_LEFT + 42;

  function pinPos(physPin: number): { x: number; y: number } {
    const row = physPinRow(physPin) - minRow;
    const col = (physPin - 1) % 2;
    return {
      x: HEADER_X + col * COL_GAP,
      y: PAD_TOP + row * PIN_SPACING,
    };
  }

  // Sensor module position
  const SENSOR_X = 195;
  const SENSOR_PIN_X = SENSOR_X + 10;

  // Position sensor pins vertically centered around average Pi pin Y
  let sensorPins = $derived((() => {
    if (wires.length === 0) return [];
    const piYs = wires.map(w => pinPos(w.physPin).y);
    const avgY = piYs.reduce((a, b) => a + b, 0) / piYs.length;
    const spacing = 26;
    const totalH = (wires.length - 1) * spacing;
    const startY = avgY - totalH / 2;
    return wires.map((w, i) => ({
      ...w,
      piPos: pinPos(w.physPin),
      sensorY: Math.max(PAD_TOP, startY + i * spacing),
    }));
  })());

  // SVG dimensions
  const SVG_W = 310;
  let svgH = $derived(PAD_TOP + visibleRows * PIN_SPACING + 28);
  let piBoxH = $derived(visibleRows * PIN_SPACING + 16);

  // Sensor module box
  let sBoxTop = $derived(sensorPins.length > 0 ? sensorPins[0].sensorY - 16 : PAD_TOP);
  let sBoxBot = $derived(sensorPins.length > 0 ? sensorPins[sensorPins.length - 1].sensorY + 16 : PAD_TOP + 60);

  // Unique wire types for legend
  let legendTypes = $derived([...new Set(wires.map(w => w.type))]);
</script>

<div class="flex flex-col items-center gap-2">
  <svg
    viewBox="0 0 {SVG_W} {svgH}"
    class="w-full max-w-[340px]"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="Wiring diagram: {sensorName} connected to Raspberry Pi GPIO"
  >
    <!-- Pi board -->
    <rect
      x={PAD_LEFT} y={PAD_TOP - 20}
      width={COL_GAP + PIN_R * 2 + 56} height={piBoxH + 24}
      rx="8"
      class="fill-surface-elevated/60 stroke-border-default"
      stroke-width="1"
    />
    <text
      x={HEADER_X + COL_GAP / 2} y={PAD_TOP - 8}
      text-anchor="middle"
      class="fill-text-muted"
      font-size="7.5" font-weight="700" letter-spacing="0.04em" font-family="Inter, sans-serif"
    >RASPBERRY PI</text>

    <!-- Visible GPIO pins -->
    {#each { length: visibleRows * 2 } as _, vi}
      {@const displayRow = vi >> 1}
      {@const col = vi & 1}
      {@const physPin = (minRow + displayRow) * 2 + col + 1}
      {#if physPin >= 1 && physPin <= 40}
        {@const pos = pinPos(physPin)}
        {@const isActive = sensorPins.some(w => w.physPin === physPin)}
        <!-- Pin circle -->
        <circle
          cx={pos.x} cy={pos.y} r={PIN_R}
          fill={pinColor(physPin)}
          opacity={isActive ? 1 : 0.18}
        />
        {#if isActive}
          <!-- Highlight ring -->
          <circle
            cx={pos.x} cy={pos.y} r={PIN_R + 2}
            fill="none"
            stroke={pinColor(physPin)}
            stroke-width="1"
            opacity="0.35"
          />
          <!-- Label to the left of the header -->
          <text
            x={PAD_LEFT + 4} y={pos.y + 3}
            class="fill-text-secondary"
            font-size="6.5" font-weight="600" font-family="Inter, sans-serif"
          >{pinLabel(physPin)}</text>
        {/if}
      {/if}
    {/each}

    <!-- Cropped indicator dots (top / bottom) -->
    {#if minRow > 0}
      <circle cx={HEADER_X} cy={PAD_TOP - 16} r="1.5" class="fill-text-muted" opacity="0.4" />
      <circle cx={HEADER_X + COL_GAP} cy={PAD_TOP - 16} r="1.5" class="fill-text-muted" opacity="0.4" />
    {/if}
    {#if maxRow < 19}
      {@const botY = PAD_TOP + visibleRows * PIN_SPACING + 4}
      <circle cx={HEADER_X} cy={botY} r="1.5" class="fill-text-muted" opacity="0.4" />
      <circle cx={HEADER_X + COL_GAP} cy={botY} r="1.5" class="fill-text-muted" opacity="0.4" />
    {/if}

    <!-- Sensor module -->
    <rect
      x={SENSOR_X} y={sBoxTop}
      width="100" height={sBoxBot - sBoxTop}
      rx="8"
      class="fill-surface-elevated/60 stroke-border-default"
      stroke-width="1"
    />
    <text
      x={SENSOR_X + 50} y={sBoxTop + 11}
      text-anchor="middle"
      class="fill-text-muted"
      font-size="7" font-weight="700" letter-spacing="0.03em" font-family="Inter, sans-serif"
    >{module || sensorName}</text>

    <!-- Wires -->
    {#each sensorPins as sp}
      {@const sx = sp.piPos.x + PIN_R + 3}
      {@const sy = sp.piPos.y}
      {@const ex = SENSOR_PIN_X}
      {@const ey = sp.sensorY}
      {@const cp1 = sx + 36}
      {@const cp2 = ex - 36}
      <!-- Wire shadow for depth -->
      <path
        d="M {sx} {sy} C {cp1} {sy}, {cp2} {ey}, {ex} {ey}"
        fill="none" stroke="black" stroke-width="4" stroke-linecap="round" opacity="0.08"
      />
      <!-- Wire -->
      <path
        d="M {sx} {sy} C {cp1} {sy}, {cp2} {ey}, {ex} {ey}"
        fill="none" stroke={sp.color} stroke-width="2.5" stroke-linecap="round" opacity="0.85"
      />
      <!-- Sensor pin dot -->
      <circle cx={ex} cy={ey} r="4" fill={sp.color} opacity="0.9" />
      <circle cx={ex} cy={ey} r="2" fill="white" opacity="0.5" />
      <!-- Sensor pin label -->
      <text
        x={ex + 10} y={ey + 3}
        class="fill-text-primary"
        font-size="7.5" font-weight="600" font-family="Inter, sans-serif"
      >{sp.sensorPin}</text>
    {/each}
  </svg>

  <!-- Color legend -->
  {#if legendTypes.length > 0}
    <div class="flex flex-wrap justify-center gap-x-4 gap-y-1">
      {#each legendTypes as lt}
        <div class="flex items-center gap-1.5">
          <span class="inline-block h-2 w-4 rounded-full" style="background:{WIRE_COLORS[lt]}; opacity:0.85"></span>
          <span class="text-[0.625rem] font-medium text-text-muted">{WIRE_LABELS[lt] ?? lt}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>
