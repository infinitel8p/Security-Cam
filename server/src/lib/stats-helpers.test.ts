import { describe, it, expect } from "vitest";

// Extracted pure functions from StatsPage for testing
// These mirror the logic in StatsPage.svelte

function usagePct(used: number, total: number): number {
  return total > 0 ? Math.round((used / total) * 100) : 0;
}

function tempColor(temp: number): string {
  if (temp >= 70) return "text-status-critical";
  if (temp >= 55) return "text-status-warning";
  return "text-status-ok";
}

function barColor(pct: number): string {
  if (pct >= 90) return "bg-status-critical";
  if (pct >= 75) return "bg-status-warning";
  return "bg-accent";
}

function formatUptime(seconds: number | undefined | null): string {
  if (seconds == null || isNaN(seconds)) return "-";
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function sparklinePoints(data: number[], max: number): string {
  if (data.length < 2) return "";
  const safeMax = max > 0 ? max : 1;
  const w = 100;
  const h = 24;
  const step = w / (data.length - 1);
  return data
    .map((v, i) => {
      const x = i * step;
      const y = h - (Math.min(v, safeMax) / safeMax) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || !isFinite(bytes) || bytes < 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

function num(v: number | null | undefined): number {
  return v != null && isFinite(v) ? v : 0;
}

describe("usagePct", () => {
  it("calculates percentage correctly", () => {
    expect(usagePct(50, 100)).toBe(50);
    expect(usagePct(3, 4)).toBe(75);
    expect(usagePct(256, 512)).toBe(50);
  });

  it("returns 0 when total is 0", () => {
    expect(usagePct(0, 0)).toBe(0);
    expect(usagePct(100, 0)).toBe(0);
  });

  it("rounds to nearest integer", () => {
    expect(usagePct(1, 3)).toBe(33);
    expect(usagePct(2, 3)).toBe(67);
  });
});

describe("tempColor", () => {
  it("returns ok for low temps", () => {
    expect(tempColor(40)).toBe("text-status-ok");
    expect(tempColor(54)).toBe("text-status-ok");
  });

  it("returns warning for moderate temps", () => {
    expect(tempColor(55)).toBe("text-status-warning");
    expect(tempColor(69)).toBe("text-status-warning");
  });

  it("returns critical for high temps", () => {
    expect(tempColor(70)).toBe("text-status-critical");
    expect(tempColor(85)).toBe("text-status-critical");
  });
});

describe("barColor", () => {
  it("returns accent for normal usage", () => {
    expect(barColor(0)).toBe("bg-accent");
    expect(barColor(74)).toBe("bg-accent");
  });

  it("returns warning for high usage", () => {
    expect(barColor(75)).toBe("bg-status-warning");
    expect(barColor(89)).toBe("bg-status-warning");
  });

  it("returns critical for very high usage", () => {
    expect(barColor(90)).toBe("bg-status-critical");
    expect(barColor(100)).toBe("bg-status-critical");
  });
});

describe("formatUptime", () => {
  it("returns '-' for null/undefined", () => {
    expect(formatUptime(null)).toBe("-");
    expect(formatUptime(undefined)).toBe("-");
    expect(formatUptime(NaN)).toBe("-");
  });

  it("formats minutes only", () => {
    expect(formatUptime(300)).toBe("5m");
    expect(formatUptime(0)).toBe("0m");
  });

  it("formats hours and minutes", () => {
    expect(formatUptime(3660)).toBe("1h 1m");
    expect(formatUptime(7200)).toBe("2h 0m");
  });

  it("formats days, hours and minutes", () => {
    expect(formatUptime(90060)).toBe("1d 1h 1m");
    expect(formatUptime(172800)).toBe("2d 0h 0m");
  });
});

describe("sparklinePoints", () => {
  it("returns empty string for less than 2 data points", () => {
    expect(sparklinePoints([], 100)).toBe("");
    expect(sparklinePoints([50], 100)).toBe("");
  });

  it("generates valid SVG points for data", () => {
    const points = sparklinePoints([0, 50, 100], 100);
    expect(points).toBeTruthy();
    const pairs = points.split(" ");
    expect(pairs).toHaveLength(3);
    pairs.forEach((p) => {
      expect(p).toMatch(/^\d+(\.\d+)?,\d+(\.\d+)?$/);
    });
  });

  it("maps 0 to bottom and max to top", () => {
    const points = sparklinePoints([0, 100], 100);
    const pairs = points.split(" ");
    // First point: value 0, x=0, y=24 (bottom)
    expect(pairs[0]).toBe("0.0,24.0");
    // Second point: value 100, x=100, y=0 (top)
    expect(pairs[1]).toBe("100.0,0.0");
  });

  it("fills full width regardless of data length", () => {
    // With 3 points, first should be at x=0, last at x=100
    const points = sparklinePoints([10, 20, 30], 100);
    const pairs = points.split(" ");
    expect(pairs[0]).toMatch(/^0\.0,/);
    expect(pairs[2]).toMatch(/^100\.0,/);
  });

  it("clamps values exceeding max", () => {
    const points = sparklinePoints([0, 200], 100);
    const pairs = points.split(" ");
    // 200 clamped to 100 → y should be 0 (top)
    expect(pairs[1]).toBe("100.0,0.0");
  });

  it("handles max=0 without division by zero", () => {
    const points = sparklinePoints([0, 0, 0], 0);
    expect(points).toBeTruthy();
    // All values should be at bottom (y=24) since all are 0
    const pairs = points.split(" ");
    expect(pairs).toHaveLength(3);
    pairs.forEach((p) => {
      expect(p).toMatch(/,24\.0$/);
    });
  });
});

describe("formatBytes", () => {
  it("formats bytes correctly", () => {
    expect(formatBytes(0)).toBe("0 B");
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(1024)).toBe("1.0 KB");
    expect(formatBytes(1024 * 1024)).toBe("1.0 MB");
    expect(formatBytes(1024 * 1024 * 1024)).toBe("1.00 GB");
  });

  it("handles null, undefined, NaN, negative", () => {
    expect(formatBytes(null)).toBe("0 B");
    expect(formatBytes(undefined)).toBe("0 B");
    expect(formatBytes(NaN)).toBe("0 B");
    expect(formatBytes(-100)).toBe("0 B");
    expect(formatBytes(Infinity)).toBe("0 B");
  });
});

describe("num", () => {
  it("returns number for valid values", () => {
    expect(num(42)).toBe(42);
    expect(num(0)).toBe(0);
    expect(num(-5)).toBe(-5);
  });

  it("returns 0 for invalid values", () => {
    expect(num(null)).toBe(0);
    expect(num(undefined)).toBe(0);
    expect(num(NaN)).toBe(0);
    expect(num(Infinity)).toBe(0);
    expect(num(-Infinity)).toBe(0);
  });
});
