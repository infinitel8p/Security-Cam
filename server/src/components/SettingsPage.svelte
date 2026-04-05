<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { getBackendUrl } from "../lib/api";
  import { setToken } from "../lib/auth";
  import { apiFetch } from "../lib/fetch";
  import { sseClient } from "../lib/sse";
  import { checkNow as checkForUpdateNow, subscribe as subscribeUpdate, clearUpdate, type UpdateState } from "../lib/update-badge";
  import toast from "svelte-5-french-toast";
  import DeviceList from "./DeviceList.svelte";
  import CameraSettings from "./CameraSettings.svelte";
  import ImageQualitySettings from "./ImageQualitySettings.svelte";
  import DirectoryPicker from "./DirectoryPicker.svelte";
  import SensorSettings from "./SensorSettings.svelte";
  import Icon from "./Icon.svelte";
  import ToggleSpring from "./ToggleSpring.svelte";
  import deviceDesktopIcon from "../icons/device-desktop.svg?raw";
  import fileTextIcon from "../icons/file-text.svg?raw";
  import shieldIcon from "../icons/shield.svg?raw";
  import sunIcon from "../icons/sun.svg?raw";
  import moonIcon from "../icons/moon.svg?raw";
  import chevronRightIcon from "../icons/chevron-right.svg?raw";
  import { initLocale, getLocale, setLocale, type Locale } from "../i18n";
  import { t } from "../i18n";

  interface Device {
    name: string;
    address: string;
  }

  let btDevices = $state<Device[]>([]);
  let wifiDevices = $state<Device[]>([]);
  let rotation = $state(0);
  let rotationMode = $state("display");
  let streamWidth = $state(1296);
  let streamHeight = $state(972);
  let streamFPS = $state(30);
  let saveLocation = $state("");
  let ispBrightness = $state(0);
  let ispContrast = $state(1);
  let ispSaturation = $state(1);
  let ispSharpness = $state(1);
  let ispEv = $state(0);
  let ispAwb = $state("auto");
  let ispExposure = $state("normal");
  let ispDenoise = $state("off");
  let ispMetering = $state("centre");
  let scanLinesEnabled = $state(true);
  let captivePortalEnabled = $state(true);
  let nightVisionEnabled = $state(true);
  let nightVisionThreshold = $state(25);
  let nightVisionSaving = $state(false);
  let storageLimitEnabled = $state(false);
  let storageLimitPercent = $state(85);
  let storageDiskPercent = $state(0);
  let storageSaving = $state(false);
  let timelapseEnabled = $state(false);
  let timelapseInterval = $state(5);
  let timelapseFps = $state(24);
  let timelapseResolution = $state("640x480");
  let timelapseSaving = $state(false);
  let timelapseFrameCount = $state(0);
  let sdWrittenGb = $state<number | null>(null);
  let sdName = $state<string | null>(null);
  let sdDate = $state<string | null>(null);
  let loading = $state(true);
  let error = $state(false);
  let activeSection = $state("appearance");

  // Device online/offline status: { bt: { "AA:BB:...": true }, wifi: { "AA:BB:...": false } }
  let deviceStatuses = $state<{ bt: Record<string, boolean>; wifi: Record<string, boolean> }>({ bt: {}, wifi: {} });
  let unsubPresence: (() => void) | null = null;

  const sectionIds = ["appearance", "camera", "storage", "devices", "sensors", "security", "system"];

  // Nav active state color (unified accent)
  const sectionColor = "text-accent";

  let scrollLock = false; // Prevents observer from overriding programmatic scroll

  function scrollToSection(id: string) {
    const el = document.getElementById(`settings-${id}`);
    if (el) {
      scrollLock = true;
      activeSection = id;
      history.replaceState(null, "", `#${id}`);
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      // Release lock after scroll settles
      setTimeout(() => { scrollLock = false; }, 800);
    }
  }

  let observer: IntersectionObserver | null = null;

  function setupObserver() {
    observer = new IntersectionObserver(
      (entries) => {
        if (scrollLock) return;
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const id = entry.target.id.replace("settings-", "");
            activeSection = id;
            history.replaceState(null, "", `#${id}`);
          }
        }
      },
      { rootMargin: "-10% 0px -70% 0px" }
    );
    for (const id of sectionIds) {
      const el = document.getElementById(`settings-${id}`);
      if (el) observer.observe(el);
    }
  }

  async function fetchDeviceStatuses() {
    try {
      const res = await apiFetch(`${getBackendUrl()}/devices/status`);
      if (res.ok) deviceStatuses = await res.json();
    } catch {
      // Silent fail - status is supplementary
    }
  }

  onDestroy(() => {
    unsubPresence?.();
    unsubUpdate?.();
    if (observer) observer.disconnect();
    if (regenTimeout) clearTimeout(regenTimeout);
  });

  type ThemeMode = "system" | "light" | "dark";
  let theme: ThemeMode = $state("system");
  let locale: Locale = $state("en");

  function changeLocale(l: Locale) {
    locale = l;
    setLocale(l);
    document.documentElement.lang = l;
    toast.success(t("toast.languageChanged"));
    // Reload to apply translations everywhere
    setTimeout(() => location.reload(), 400);
  }

  function setTheme(m: ThemeMode) {
    theme = m;
    if (m === "system") {
      localStorage.removeItem("theme");
    } else {
      localStorage.setItem("theme", m);
    }
    const isLight =
      m === "light" ||
      (m === "system" && window.matchMedia("(prefers-color-scheme: light)").matches);
    document.documentElement.classList.toggle("light", isLight);
    toast.success(t("toast.themeChanged"));
  }

  async function fetchSettings() {
    loading = true;
    error = false;
    try {
      const base = getBackendUrl();
      // Fire all requests in parallel - settings is critical, others are supplementary
      const [res, tlRes, storageRes, sysRes] = await Promise.all([
        apiFetch(`${base}/settings`),
        apiFetch(`${base}/timelapse/status`).catch(() => null),
        apiFetch(`${base}/storage/status`).catch(() => null),
        apiFetch(`${base}/system_info`).catch(() => null),
      ]);
      if (!res.ok) throw new Error();
      const settings = await res.json();
      btDevices = settings.TARGET_BT_ADDRESSES ?? [];
      wifiDevices = settings.TARGET_AP_MAC_ADDRESSES ?? [];
      rotation = Number(settings.RotationAngle) || 0;
      rotationMode = settings.RotationMode ?? "display";
      streamWidth = settings.StreamWidth ?? 1296;
      streamHeight = settings.StreamHeight ?? 972;
      streamFPS = settings.StreamFPS ?? 30;
      saveLocation = settings.VideoSaveLocation ?? "/home/pi/Videos";
      scanLinesEnabled = settings.ScanLines !== false;
      const cp = settings.CaptivePortal ?? {};
      captivePortalEnabled = cp.enabled !== false;
      const nv = settings.NightVision ?? {};
      nightVisionEnabled = nv.enabled !== false;
      nightVisionThreshold = nv.threshold_percent ?? 25;
      const au = settings.Auth ?? {};
      authEnabled = au.enabled ?? false;
      authToken = au.token ?? "";
      const sl = settings.StorageLimit ?? {};
      storageLimitEnabled = sl.enabled ?? false;
      storageLimitPercent = sl.max_percent ?? 85;
      const isp = settings.ISP ?? {};
      ispBrightness = isp.brightness ?? 0;
      ispContrast = isp.contrast ?? 1;
      ispSaturation = isp.saturation ?? 1;
      ispSharpness = isp.sharpness ?? 1;
      ispEv = isp.ev ?? 0;
      ispAwb = isp.awb ?? "auto";
      ispExposure = isp.exposure ?? "normal";
      ispDenoise = isp.denoise ?? "off";
      ispMetering = isp.metering ?? "centre";
      const tl = settings.Timelapse ?? {};
      timelapseEnabled = tl.enabled ?? false;
      timelapseInterval = tl.interval_minutes ?? 5;
      timelapseFps = tl.fps ?? 24;
      timelapseResolution = tl.resolution ?? "640x480";

      if (tlRes?.ok) {
        const tlStatus = await tlRes.json();
        timelapseFrameCount = tlStatus.today_frame_count ?? 0;
      }
      if (storageRes?.ok) {
        const st = await storageRes.json();
        storageDiskPercent = st.disk_percent ?? 0;
      }
      if (sysRes?.ok) {
        const sys = await sysRes.json();
        const sd = sys.sd_health;
        if (sd) {
          sdWrittenGb = sd.written_since_boot_gb ?? null;
          sdName = sd.name ?? null;
          sdDate = sd.manufacturing_date ?? null;
        }
      }
    } catch {
      error = true;
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    initLocale();
    locale = getLocale();
    const saved = localStorage.getItem("theme") as ThemeMode | null;
    theme = saved === "light" || saved === "dark" ? saved : "system";
    // Subscribe to shared update state
    unsubUpdate = subscribeUpdate((state) => { updateResult = state.lastChecked ? state : null; });
    // Fire settings + device statuses in parallel (independent requests)
    fetchSettings();
    fetchDeviceStatuses();
    const sse = sseClient();
    sse.registerFallback({
      event: "presence_change",
      endpoint: "/devices/status",
      interval: 15_000,
      transform: (json) => json,
    });
    unsubPresence = sse.on("presence_change", (ev) => {
      // Update the specific device status in-place
      const key = ev.transport === "bluetooth" ? "bt" : "wifi";
      deviceStatuses = {
        ...deviceStatuses,
        [key]: { ...deviceStatuses[key], [ev.address.toUpperCase()]: ev.online },
      };
    });

    // Track which section is visible for nav highlighting
    requestAnimationFrame(() => {
      setupObserver();

      // Scroll to section if URL has a hash (e.g. /settings#camera)
      const hash = window.location.hash.replace("#", "");
      if (hash && sectionIds.includes(hash)) {
        scrollToSection(hash);
      }
    });
  });

  function saveStorageLimit() {
    storageSaving = true;
    const enabled = storageLimitEnabled;

    toast.promise(
      (async () => {
        const res = await apiFetch(`${getBackendUrl()}/storage/configure`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            enabled: storageLimitEnabled,
            max_percent: storageLimitPercent,
          }),
        });
        if (!res.ok) throw new Error();
        return enabled;
      })(),
      {
        loading: t("status.saving"),
        success: (on) => on ? t("toast.autoDeleteEnabled") : t("toast.autoDeleteDisabled"),
        error: t("toast.saveFailed"),
      },
    ).finally(() => { storageSaving = false; });
  }

  function saveTimelapse() {
    timelapseSaving = true;
    const enabled = timelapseEnabled;

    toast.promise(
      (async () => {
        const res = await apiFetch(`${getBackendUrl()}/timelapse/configure`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            enabled: timelapseEnabled,
            interval_minutes: timelapseInterval,
            fps: timelapseFps,
            resolution: timelapseResolution,
          }),
        });
        if (!res.ok) throw new Error();
        return enabled;
      })(),
      {
        loading: t("status.saving"),
        success: (on) => on ? t("toast.timelapseEnabled") : t("toast.timelapseDisabled"),
        error: t("toast.saveFailed"),
      },
    ).finally(() => { timelapseSaving = false; });
  }

  async function addBtDevice(device: Device) {
    const res = await apiFetch(`${getBackendUrl()}/devices/bt/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(device),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || "Failed to add device");
    }
    if (!btDevices.some(d => d.address.toLowerCase() === device.address.toLowerCase())) {
      btDevices = [...btDevices, device];
    }
  }

  async function removeBtDevice(address: string) {
    await apiFetch(`${getBackendUrl()}/devices/bt/remove`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address }),
    });
    btDevices = btDevices.filter(d => d.address.toLowerCase() !== address.toLowerCase());
  }

  async function addWifiDevice(device: Device) {
    const res = await apiFetch(`${getBackendUrl()}/devices/wifi/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(device),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.error || "Failed to add device");
    }
    if (!wifiDevices.some(d => d.address.toLowerCase() === device.address.toLowerCase())) {
      wifiDevices = [...wifiDevices, device];
    }
  }

  // --- Update check (shared state from update-badge.ts) ---
  let updateChecking = $state(false);
  let updateResult = $state<UpdateState | null>(null);
  let updateAvailable = $derived(updateResult?.available ?? false);
  let updateConfirm = $state(false);
  let updateTimeout: ReturnType<typeof setTimeout> | null = null;
  let unsubUpdate: (() => void) | null = null;

  async function checkForUpdates() {
    updateChecking = true;
    try {
      const result = await checkForUpdateNow();
      if (result.error) {
        toast.error(result.error);
      } else if (result.available) {
        toast(t("toast.updatesFound", { n: result.commits_behind }));
      } else {
        toast(t("toast.noUpdates"));
      }
    } catch {
      toast.error(t("toast.updateCheckFailed"));
    } finally {
      updateChecking = false;
    }
  }

  function confirmUpdate() {
    updateConfirm = true;
    if (updateTimeout) clearTimeout(updateTimeout);
    updateTimeout = setTimeout(() => { updateConfirm = false; }, 5000);
  }

  async function doUpdate() {
    updateConfirm = false;
    clearUpdate();
    doRestart();
  }

  let restartConfirm = $state(false);
  let rebootConfirm = $state(false);
  let restartTimeout: ReturnType<typeof setTimeout> | null = null;
  let rebootTimeout: ReturnType<typeof setTimeout> | null = null;

  function confirmRestart() {
    restartConfirm = true;
    if (restartTimeout) clearTimeout(restartTimeout);
    restartTimeout = setTimeout(() => { restartConfirm = false; }, 5000);
  }

  function confirmReboot() {
    rebootConfirm = true;
    if (rebootTimeout) clearTimeout(rebootTimeout);
    rebootTimeout = setTimeout(() => { rebootConfirm = false; }, 5000);
  }

  async function doRestart() {
    restartConfirm = false;
    clearUpdate();
    toast(t("toast.restarting"), { icon: "🔄" });
    try {
      await apiFetch(`${getBackendUrl()}/system/restart`, { method: "POST" });
    } catch {
      // Expected - the service will restart and kill this connection
    }
  }

  async function doReboot() {
    rebootConfirm = false;
    clearUpdate();
    toast(t("toast.rebooting"), { icon: "🔄" });
    try {
      await apiFetch(`${getBackendUrl()}/system/reboot`, { method: "POST" });
    } catch {
      // Expected - the device will reboot and kill this connection
    }
  }

  let captivePortalSaving = false;
  function toggleCaptivePortal() {
    if (captivePortalSaving) return;
    captivePortalSaving = true;
    captivePortalEnabled = !captivePortalEnabled;
    const enabled = captivePortalEnabled;

    toast.promise(
      (async () => {
        const res = await apiFetch(`${getBackendUrl()}/captive-portal`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled }),
        });
        if (!res.ok) throw new Error();
        return enabled;
      })(),
      {
        loading: t("status.saving"),
        success: (on) => on ? t("toast.captivePortalEnabled") : t("toast.captivePortalDisabled"),
        error: () => {
          captivePortalEnabled = !enabled;
          return t("toast.saveFailed");
        },
      },
    ).finally(() => { captivePortalSaving = false; });
  }

  function toggleNightVision() {
    nightVisionEnabled = !nightVisionEnabled;
    saveNightVision();
  }

  function saveNightVision() {
    nightVisionSaving = true;
    const enabled = nightVisionEnabled;
    const threshold = nightVisionThreshold;

    toast.promise(
      (async () => {
        const res = await apiFetch(`${getBackendUrl()}/settings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            NightVision: { enabled, threshold_percent: threshold },
          }),
        });
        if (!res.ok) throw new Error();
        return enabled;
      })(),
      {
        loading: t("status.saving"),
        success: (on) => on ? t("toast.nightVisionEnabled") : t("toast.nightVisionDisabled"),
        error: () => {
          nightVisionEnabled = !enabled;
          return t("toast.saveFailed");
        },
      },
    ).finally(() => { nightVisionSaving = false; });
  }

  // --- Settings backup ---
  const MAX_IMPORT_SIZE = 256 * 1024; // 256 KB - settings files are small
  const SENSITIVE_KEYS = new Set(["token", "password_hash"]);
  let exporting = $state(false);
  let importing = $state(false);
  let importLoading = $state(false);
  let importPreview: { incoming: Record<string, any>; body: string; changes: { key: string; from: any; to: any }[] } | null = $state(null);

  async function exportSettings() {
    if (exporting) return;
    exporting = true;
    try {
      const res = await apiFetch(`${getBackendUrl()}/settings/export`);
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "settings-backup.json";
      a.click();
      URL.revokeObjectURL(url);
      toast.success(t("toast.settingsExported"));
    } catch {
      toast.error(t("toast.saveFailed"));
    }
    exporting = false;
  }

  function diffSettings(current: Record<string, any>, incoming: Record<string, any>): { key: string; from: any; to: any }[] {
    const changes: { key: string; from: any; to: any }[] = [];
    for (const key of Object.keys(incoming)) {
      const curVal = current[key];
      const incVal = incoming[key];
      if (JSON.stringify(curVal) === JSON.stringify(incVal)) continue;

      // Flatten one level for plain objects (not arrays)
      if (incVal && typeof incVal === "object" && !Array.isArray(incVal) && curVal && typeof curVal === "object" && !Array.isArray(curVal)) {
        const allSubKeys = new Set([...Object.keys(curVal), ...Object.keys(incVal)]);
        for (const sub of allSubKeys) {
          if (JSON.stringify(curVal[sub]) !== JSON.stringify(incVal[sub])) {
            changes.push({ key: `${key}.${sub}`, from: curVal[sub], to: incVal[sub] });
          }
        }
      } else {
        changes.push({ key, from: curVal, to: incVal });
      }
    }
    return changes;
  }

  function triggerImport() {
    if (importLoading) return;
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json,application/json";
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;
      if (file.size > MAX_IMPORT_SIZE) {
        toast.error(t("toast.settingsFileTooLarge"));
        return;
      }
      importLoading = true;
      try {
        const text = await file.text();
        let parsed: any;
        try {
          parsed = JSON.parse(text);
        } catch {
          throw new Error(t("toast.settingsInvalidJson"));
        }
        if (typeof parsed !== "object" || Array.isArray(parsed)) {
          throw new Error(t("toast.settingsInvalidJson"));
        }
        // Fetch current settings to compute diff
        const curRes = await apiFetch(`${getBackendUrl()}/settings`);
        if (!curRes.ok) throw new Error(t("toast.settingsImportFailed"));
        const current = await curRes.json();
        // GET /settings strips password_hash for security, so exclude it
        // from the diff to avoid false positives when importing a full backup
        if (parsed.Auth) {
          const { password_hash: _, ...rest } = parsed.Auth;
          parsed = { ...parsed, Auth: rest };
        }
        const changes = diffSettings(current, parsed);
        importPreview = { incoming: parsed, body: text, changes };
      } catch (err: any) {
        toast.error(err?.message || t("toast.settingsImportFailed"));
      }
      importLoading = false;
    };
    input.click();
  }

  function dismissPreview() {
    if (importing) return;
    importPreview = null;
  }

  async function confirmImport() {
    if (!importPreview || importing) return;
    importing = true;
    try {
      const res = await apiFetch(`${getBackendUrl()}/settings/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: importPreview.body,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || t("toast.settingsImportFailed"));
      }
      importPreview = null;
      toast.success(t("toast.settingsImported"));
      setTimeout(() => location.reload(), 600);
    } catch (err: any) {
      toast.error(err?.message || t("toast.settingsImportFailed"));
    }
    importing = false;
  }

  function isDeviceList(val: any): val is { address: string; name?: string }[] {
    return Array.isArray(val) && val.length > 0 && typeof val[0]?.address === "string";
  }

  function formatValue(val: any, key?: string): string {
    if (val === undefined) return "-";
    const leafKey = key?.split(".").pop() ?? "";
    if (SENSITIVE_KEYS.has(leafKey)) return "***";
    if (Array.isArray(val) && val.length === 0) return "-";
    if (typeof val === "object") return JSON.stringify(val);
    return String(val);
  }


  // --- Auth settings ---
  let authEnabled = $state(false);
  let authToken = $state("");
  let authSaving = false;
  let regenConfirm = $state(false);
  let regenTimeout: ReturnType<typeof setTimeout> | null = null;

  // Password change
  let currentPassword = $state("");
  let newPassword = $state("");
  let confirmPassword = $state("");
  let passwordSaving = $state(false);

  function toggleAuth() {
    if (authSaving) return;
    authSaving = true;
    authEnabled = !authEnabled;
    const enabled = authEnabled;

    toast.promise(
      (async () => {
        const res = await apiFetch(`${getBackendUrl()}/settings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ Auth: { enabled } }),
        });
        if (!res.ok) throw new Error();
        // Store the token so future requests are authenticated
        if (enabled) {
          if (!authToken) {
            // Token not yet loaded - fetch it before auth takes effect
            const sr = await apiFetch(`${getBackendUrl()}/settings`);
            if (sr.ok) {
              const s = await sr.json();
              authToken = s.Auth?.token ?? "";
            }
          }
          if (authToken) setToken(authToken);
        }
        return enabled;
      })(),
      {
        loading: t("status.saving"),
        success: (on) => on ? t("toast.authEnabled") : t("toast.authDisabled"),
        error: () => {
          authEnabled = !enabled;
          return t("toast.saveFailed");
        },
      },
    ).finally(() => { authSaving = false; });
  }

  async function copyToken() {
    try {
      await navigator.clipboard.writeText(authToken);
      toast(t("toast.tokenCopied"));
    } catch {
      toast.error(t("toast.saveFailed"));
    }
  }

  function confirmRegen() {
    regenConfirm = true;
    if (regenTimeout) clearTimeout(regenTimeout);
    regenTimeout = setTimeout(() => { regenConfirm = false; }, 5000);
  }

  async function doRegen() {
    regenConfirm = false;
    try {
      const res = await apiFetch(`${getBackendUrl()}/auth/regenerate`, { method: "POST" });
      if (!res.ok) throw new Error();
      const data = await res.json();
      authToken = data.token;
      setToken(data.token);
      toast(t("toast.tokenRegenerated"));
    } catch {
      toast.error(t("toast.saveFailed"));
    }
  }

  async function changePassword() {
    if (passwordSaving) return;
    if (newPassword !== confirmPassword) {
      toast.error(t("toast.passwordMismatch"));
      return;
    }
    if (newPassword.length < 4) {
      toast.error(t("toast.passwordTooShort"));
      return;
    }
    passwordSaving = true;
    try {
      const res = await apiFetch(`${getBackendUrl()}/auth/set-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current: currentPassword, new: newPassword }),
      });
      if (res.ok) {
        toast.success(t("toast.passwordChanged"));
        currentPassword = "";
        newPassword = "";
        confirmPassword = "";
      } else {
        const data = await res.json().catch(() => ({}));
        toast.error(data.error || t("toast.saveFailed"));
      }
    } catch {
      toast.error(t("toast.saveFailed"));
    }
    passwordSaving = false;
  }

  let scanLinesSaving = false;
  function toggleScanLines() {
    if (scanLinesSaving) return;
    scanLinesSaving = true;
    scanLinesEnabled = !scanLinesEnabled;
    const enabled = scanLinesEnabled;

    toast.promise(
      (async () => {
        const res = await apiFetch(`${getBackendUrl()}/settings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ScanLines: enabled }),
        });
        if (!res.ok) throw new Error();
        return enabled;
      })(),
      {
        loading: t("status.saving"),
        success: (on) => on ? t("toast.scanLinesEnabled") : t("toast.scanLinesDisabled"),
        error: () => {
          scanLinesEnabled = !enabled;
          return t("toast.saveFailed");
        },
      },
    ).finally(() => { scanLinesSaving = false; });
  }

  async function removeWifiDevice(address: string) {
    await apiFetch(`${getBackendUrl()}/devices/wifi/remove`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address }),
    });
    wifiDevices = wifiDevices.filter(d => d.address.toLowerCase() !== address.toLowerCase());
  }
</script>

{#snippet navItem(id: string, label: string, badge?: boolean)}
  <button
    onclick={() => scrollToSection(id)}
    class="group relative w-full text-left px-3.5 py-2 text-[0.8125rem] transition-all duration-200
      {activeSection === id
        ? `${sectionColor} font-semibold`
        : 'text-text-muted font-medium hover:text-text-secondary'}"
  >
    <span
      class="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 rounded-full bg-accent transition-all duration-300
        {activeSection === id ? 'h-4 opacity-100' : 'h-0 opacity-0'}"
    ></span>
    {label}
    {#if badge}
      <span class="ml-1.5 inline-block h-2 w-2 rounded-full bg-accent"></span>
    {/if}
  </button>
{/snippet}

{#snippet mobileNavItem(id: string, label: string, badge?: boolean)}
  <button
    onclick={() => scrollToSection(id)}
    class="relative shrink-0 px-3 pt-2 pb-2.5 text-xs font-medium whitespace-nowrap transition-all duration-200
      {activeSection === id
        ? `${sectionColor} font-semibold`
        : 'text-text-muted hover:text-text-secondary'}"
  >
    {label}
    {#if badge}
      <span class="ml-1 inline-block h-1.5 w-1.5 rounded-full bg-accent"></span>
    {/if}
    <span
      class="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 rounded-full bg-accent transition-all duration-300
        {activeSection === id
          ? 'w-5 opacity-100'
          : 'w-0 opacity-0'}"
    ></span>
  </button>
{/snippet}

{#if loading}
  <div class="mt-5 space-y-4">
    {#each Array(4) as _, i}
      <div class="card px-5 py-6 animate-in" style="animation-delay: {i * 60}ms">
        <div class="skeleton h-4 w-32"></div>
        <div class="skeleton mt-4 h-8 w-48"></div>
      </div>
    {/each}
  </div>
{:else if error}
  <div class="mt-5 card flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
    <p class="text-sm text-text-muted">{t("error.settings")}</p>
    <button onclick={fetchSettings} class="text-[0.8125rem] font-medium text-accent hover:text-accent-hover">{t("btn.retry")}</button>
  </div>
{:else}
  <!-- Mobile section nav -->
  <nav class="mt-5 -mx-4 sm:-mx-6 px-4 sm:px-6 overflow-x-auto scrollbar-hide border-b border-border-subtle lg:hidden">
    <div class="flex gap-0.5">
      {@render mobileNavItem("appearance", t("section.appearance"))}
      {@render mobileNavItem("camera", t("section.camera"))}
      {@render mobileNavItem("storage", t("section.storage"))}
      {@render mobileNavItem("devices", t("section.devices"))}
      {@render mobileNavItem("sensors", t("section.triggerSensors"))}
      {@render mobileNavItem("security", t("section.security"))}
      {@render mobileNavItem("system", t("section.system"), updateAvailable)}
    </div>
  </nav>

  <div class="mt-2 flex gap-8 lg:gap-10 items-start lg:mt-6">
    <!-- Sidebar nav -->
    <nav class="hidden lg:block sticky top-6 self-start w-44 shrink-0">
      <div class="flex flex-col gap-0.5">
        {@render navItem("appearance", t("section.appearance"))}
        {@render navItem("camera", t("section.camera"))}
        {@render navItem("storage", t("section.storage"))}
        {@render navItem("devices", t("section.devices"))}
        {@render navItem("sensors", t("section.triggerSensors"))}
        {@render navItem("security", t("section.security"))}
        {@render navItem("system", t("section.system"), updateAvailable)}
      </div>
    </nav>

    <!-- Content -->
    <div class="min-w-0 flex-1">
      <!-- Appearance -->
      <section id="settings-appearance" class="scroll-mt-16 lg:scroll-mt-8 space-y-3">
        <div class="flex items-center gap-2.5">
          <span class="h-3.5 w-0.5 rounded-full bg-accent"></span>
          <h2 class="text-xs font-semibold uppercase tracking-widest text-text-secondary">{t("section.appearance")}</h2>
        </div>
        <div class="card overflow-hidden">
          <div class="px-4 py-3.5 sm:px-5 sm:py-4">
            <div class="grid grid-cols-3 gap-2">
              <button
                onclick={() => setTheme("system")}
                class="btn-press flex flex-col items-center gap-2.5 rounded-xl border px-3 py-4 transition-all duration-200
                  {theme === 'system' ? 'border-accent/40 bg-accent-muted text-accent shadow-[var(--shadow-glow)] scale-[1.03]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
              >
                <Icon icon={deviceDesktopIcon} class="h-5 w-5" />
                <span class="text-[0.6875rem] font-semibold">{t("theme.system")}</span>
              </button>
              <button
                onclick={() => setTheme("light")}
                class="btn-press flex flex-col items-center gap-2.5 rounded-xl border px-3 py-4 transition-all duration-200
                  {theme === 'light' ? 'border-accent/40 bg-accent-muted text-accent shadow-[var(--shadow-glow)] scale-[1.03]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
              >
                <Icon icon={sunIcon} class="h-5 w-5" />
                <span class="text-[0.6875rem] font-semibold">{t("theme.light")}</span>
              </button>
              <button
                onclick={() => setTheme("dark")}
                class="btn-press flex flex-col items-center gap-2.5 rounded-xl border px-3 py-4 transition-all duration-200
                  {theme === 'dark' ? 'border-accent/40 bg-accent-muted text-accent shadow-[var(--shadow-glow)] scale-[1.03]' : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
              >
                <Icon icon={moonIcon} class="h-5 w-5" />
                <span class="text-[0.6875rem] font-semibold">{t("theme.dark")}</span>
              </button>
            </div>
          </div>
          <div class="border-t border-border-subtle px-4 py-3.5 sm:px-5 sm:py-4">
            <p class="mb-2 text-sm font-medium text-text-primary">{t("language.label")}</p>
            <div class="grid grid-cols-3 gap-1.5 sm:grid-cols-5">
              {#each ["en", "de", "fr", "es", "it"] as lang}
                <button
                  onclick={() => changeLocale(lang as import("../i18n").Locale)}
                  class="rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors text-center
                    {locale === lang
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-border-default bg-surface-base text-text-muted hover:border-border-strong hover:text-text-secondary'}"
                >
                  {t(`language.${lang}`)}
                </button>
              {/each}
            </div>
          </div>
          <div class="border-t border-border-subtle px-4 py-3.5 sm:px-5 sm:py-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.scanLines")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.scanLines")}</p>
              </div>
              <ToggleSpring checked={scanLinesEnabled} onToggle={toggleScanLines} label={t("label.scanLines")} />
            </div>
          </div>
          <div class="border-t border-border-subtle px-4 py-3.5 sm:px-5 sm:py-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.captivePortal")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.captivePortal")}</p>
              </div>
              <ToggleSpring checked={captivePortalEnabled} onToggle={toggleCaptivePortal} label={t("label.captivePortal")} />
            </div>
          </div>
        </div>
      </section>

      <!-- Camera -->
      <section id="settings-camera" class="scroll-mt-16 lg:scroll-mt-8 mt-10 space-y-3">
        <div class="flex items-center gap-2.5">
          <span class="h-3.5 w-0.5 rounded-full bg-accent"></span>
          <h2 class="text-xs font-semibold uppercase tracking-widest text-text-secondary">{t("section.camera")}</h2>
        </div>
        <CameraSettings
          currentAngle={rotation}
          currentMode={rotationMode}
          {streamWidth}
          {streamHeight}
          {streamFPS}
        />
        <ImageQualitySettings
          brightness={ispBrightness}
          contrast={ispContrast}
          saturation={ispSaturation}
          sharpness={ispSharpness}
          ev={ispEv}
          awb={ispAwb}
          exposure={ispExposure}
          denoise={ispDenoise}
          metering={ispMetering}
        />

        <!-- Night Vision -->
        <div class="card overflow-hidden">
          <div class="px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.nightVision")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.nightVision")}</p>
              </div>
              <ToggleSpring checked={nightVisionEnabled} onToggle={toggleNightVision} label={t("label.nightVision")} />
            </div>

            {#if nightVisionEnabled}
              <div class="mt-4 space-y-3 animate-slide-down">
                <div>
                  <div class="flex items-center justify-between mb-1.5">
                    <label class="text-xs font-medium text-text-secondary" for="nv-threshold">{t("label.nightVisionThreshold")}</label>
                    <span class="rounded-md bg-surface-elevated px-2 py-0.5 text-[0.6875rem] font-semibold tabular-nums text-text-primary">{nightVisionThreshold}%</span>
                  </div>
                  <div class="flex items-center gap-2.5">
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0 text-right">5%</span>
                    <input
                      id="nv-threshold"
                      type="range"
                      min="5"
                      max="80"
                      step="5"
                      bind:value={nightVisionThreshold}
                      aria-label={t("label.nightVisionThreshold")}
                      class="range-slider flex-1"
                    />
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0">80%</span>
                  </div>
                  <p class="mt-1 text-[0.6875rem] text-text-muted">{t("help.nightVisionThreshold")}</p>
                </div>

                <button
                  class="btn-press rounded-lg bg-accent/10 px-4 py-2 text-xs font-semibold text-accent transition-colors hover:bg-accent/18 disabled:opacity-50"
                  onclick={saveNightVision}
                  disabled={nightVisionSaving}
                >
                  {nightVisionSaving ? t("btn.saving") : t("btn.save")}
                </button>
              </div>
            {/if}
          </div>
        </div>
      </section>

      <!-- Storage -->
      <section id="settings-storage" class="scroll-mt-16 lg:scroll-mt-8 mt-10 space-y-3">
        <div class="flex items-center gap-2.5">
          <span class="h-3.5 w-0.5 rounded-full bg-accent"></span>
          <h2 class="text-xs font-semibold uppercase tracking-widest text-text-secondary">{t("section.storage")}</h2>
        </div>
        <DirectoryPicker current={saveLocation} />

        {#if sdName || sdWrittenGb != null}
          <p class="px-1 text-[0.6875rem] tabular-nums text-text-muted">
            {sdName ?? "SD"}{#if sdDate}{" "}· {sdDate}{/if}{#if sdWrittenGb != null}{" "}· {sdWrittenGb.toFixed(1)} GB {t("label.writtenSinceBoot").toLowerCase()}{/if}
          </p>
        {/if}

        <!-- Auto-delete -->
        <div class="card overflow-hidden">
          <div class="px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.autoDelete")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.autoDelete")}</p>
              </div>
              <ToggleSpring
                checked={storageLimitEnabled}
                onToggle={() => { storageLimitEnabled = !storageLimitEnabled; saveStorageLimit(); }}
                label={t("label.autoDelete")}
              />
            </div>

            {#if storageLimitEnabled}
              <div class="mt-4 space-y-3 animate-slide-down">
                <div>
                  <div class="flex items-center justify-between mb-1.5">
                    <label class="text-xs font-medium text-text-secondary" for="storage-limit">{t("label.storageThreshold")}</label>
                    <span class="rounded-md bg-surface-elevated px-2 py-0.5 text-[0.6875rem] font-semibold tabular-nums text-text-primary">{storageLimitPercent}%</span>
                  </div>
                  <div class="flex items-center gap-2.5">
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0 text-right">10%</span>
                    <input
                      id="storage-limit"
                      type="range"
                      min="10"
                      max="95"
                      step="5"
                      bind:value={storageLimitPercent}
                      aria-label={t("label.storageThreshold")}
                      class="range-slider flex-1"
                    />
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0">95%</span>
                  </div>
                  <p class="mt-1 text-[0.6875rem] text-text-muted">{t("help.storageThreshold")}</p>
                </div>

                <!-- Disk usage bar -->
                {#if storageDiskPercent > 0}
                  <div class="rounded-lg border border-border-default bg-surface-base px-3 py-2.5">
                    <div class="flex items-center justify-between mb-1.5">
                      <span class="text-[0.6875rem] font-medium text-text-secondary">{t("label.currentUsage")}</span>
                      <span class="text-[0.6875rem] font-semibold tabular-nums {storageDiskPercent > storageLimitPercent ? 'text-status-critical' : 'text-text-primary'}">{storageDiskPercent}%</span>
                    </div>
                    <div class="h-1.5 w-full rounded-full bg-surface-elevated overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all duration-500 {storageDiskPercent > storageLimitPercent ? 'bg-status-critical' : storageDiskPercent > storageLimitPercent - 10 ? 'bg-status-warning' : 'bg-accent'}"
                        style="width: {storageDiskPercent}%"
                      ></div>
                    </div>
                    <!-- Threshold marker -->
                    <div class="relative h-0">
                      <div class="absolute -top-1.5 h-1.5 w-px bg-text-muted/50" style="left: {storageLimitPercent}%"></div>
                    </div>
                  </div>
                {/if}

                <div class="flex justify-end">
                  <button
                    onclick={saveStorageLimit}
                    disabled={storageSaving}
                    class="btn-press rounded-lg bg-accent px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50"
                  >
                    {storageSaving ? t("btn.saving") : t("btn.save")}
                  </button>
                </div>
              </div>
            {/if}
          </div>
        </div>

        <!-- Timelapse -->
        <div class="card overflow-hidden">
          <div class="px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.timelapse")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.timelapse")}</p>
              </div>
              <ToggleSpring
                checked={timelapseEnabled}
                onToggle={() => { timelapseEnabled = !timelapseEnabled; saveTimelapse(); }}
                label={t("label.timelapse")}
              />
            </div>

            {#if timelapseEnabled}
              <div class="mt-4 space-y-3 animate-slide-down">
                <!-- Status indicator -->
                {#if timelapseFrameCount > 0}
                  <div class="flex items-center gap-2 rounded-lg border border-border-default bg-surface-base px-3 py-2">
                    <span class="h-1.5 w-1.5 rounded-full bg-status-ok animate-pulse"></span>
                    <span class="text-[0.75rem] font-medium text-text-secondary">
                      {t("label.timelapseCapturing", { n: String(timelapseFrameCount) })}
                    </span>
                  </div>
                {/if}

                <div>
                  <div class="flex items-center justify-between mb-1.5">
                    <label class="text-xs font-medium text-text-secondary" for="tl-interval">{t("label.timelapseInterval")}</label>
                    <span class="rounded-md bg-surface-elevated px-2 py-0.5 text-[0.6875rem] font-semibold tabular-nums text-text-primary">{timelapseInterval} min</span>
                  </div>
                  <div class="flex items-center gap-2.5">
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0 text-right">1</span>
                    <input
                      id="tl-interval"
                      type="range"
                      min="1"
                      max="60"
                      step="1"
                      bind:value={timelapseInterval}
                      aria-label={t("label.timelapseInterval")}
                      class="range-slider flex-1"
                    />
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0">60</span>
                  </div>
                  <p class="mt-1 text-[0.6875rem] text-text-muted">{t("help.timelapseInterval")}</p>
                </div>

                <div>
                  <div class="flex items-center justify-between mb-1.5">
                    <label class="text-xs font-medium text-text-secondary" for="tl-fps">{t("label.timelapseFps")}</label>
                    <span class="rounded-md bg-surface-elevated px-2 py-0.5 text-[0.6875rem] font-semibold tabular-nums text-text-primary">{timelapseFps} fps</span>
                  </div>
                  <div class="flex items-center gap-2.5">
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0 text-right">1</span>
                    <input
                      id="tl-fps"
                      type="range"
                      min="1"
                      max="60"
                      step="1"
                      bind:value={timelapseFps}
                      aria-label={t("label.timelapseFps")}
                      class="range-slider flex-1"
                    />
                    <span class="text-[0.625rem] text-text-muted w-8 shrink-0">60</span>
                  </div>
                </div>

                <div>
                  <label class="text-xs font-medium text-text-secondary" for="tl-res">{t("label.timelapseResolution")}</label>
                  <select
                    id="tl-res"
                    bind:value={timelapseResolution}
                    class="mt-1 block h-9 w-full rounded-lg border border-border-subtle bg-surface-overlay px-2.5 text-[0.8125rem] text-text-primary outline-none transition-colors focus:border-accent/50 focus:ring-1 focus:ring-accent/25"
                  >
                    <option value="original">Original</option>
                    <option value="640:480">640 x 480</option>
                    <option value="320:240">320 x 240</option>
                  </select>
                </div>

                <div class="flex justify-end">
                  <button
                    onclick={saveTimelapse}
                    disabled={timelapseSaving}
                    class="btn-press rounded-lg bg-accent px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-accent/90 disabled:opacity-50"
                  >
                    {timelapseSaving ? t("btn.saving") : t("btn.save")}
                  </button>
                </div>
              </div>
            {/if}
          </div>
        </div>
      </section>

      <!-- Devices -->
      <section id="settings-devices" class="scroll-mt-16 lg:scroll-mt-8 mt-12 space-y-3">
        <div class="flex items-center gap-2.5">
          <span class="h-3.5 w-0.5 rounded-full bg-accent"></span>
          <h2 class="text-xs font-semibold uppercase tracking-widest text-text-secondary">{t("section.devices")}</h2>
        </div>
        <div class="space-y-3">
          <DeviceList
            title={t("label.bluetoothDevices")}
            icon="bluetooth"
            devices={btDevices}
            onAdd={addBtDevice}
            onRemove={removeBtDevice}
            scanEndpoint="/bt/scan"
            scanResultKey="devices"
            scanDuration={25}
            statuses={deviceStatuses.bt}
          />
          <DeviceList
            title={t("label.wifiDevices")}
            icon="wifi"
            devices={wifiDevices}
            onAdd={addWifiDevice}
            onRemove={removeWifiDevice}
            scanEndpoint="/wifi/stations"
            scanResultKey="stations"
            scanDuration={5}
            statuses={deviceStatuses.wifi}
          />
        </div>
      </section>

      <!-- Recording Sensors -->
      <section id="settings-sensors" class="scroll-mt-16 lg:scroll-mt-8 mt-12 space-y-3">
        <div class="flex items-center gap-2.5">
          <span class="h-3.5 w-0.5 rounded-full bg-accent"></span>
          <h2 class="text-xs font-semibold uppercase tracking-widest text-text-secondary">{t("section.triggerSensors")}</h2>
        </div>
        <SensorSettings />
      </section>

      <!-- Security -->
      <section id="settings-security" class="scroll-mt-16 lg:scroll-mt-8 mt-12 space-y-3">
        <div class="flex items-center gap-2.5">
          <span class="h-3.5 w-0.5 rounded-full bg-accent"></span>
          <h2 class="text-xs font-semibold uppercase tracking-widest text-text-secondary">{t("section.security")}</h2>
        </div>
        <div class="card overflow-hidden {authEnabled ? 'ring-1 ring-accent/15' : ''} transition-all duration-500">
          <!-- Auth toggle with shield icon -->
          <div class="px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between gap-4">
              <div class="flex items-start gap-3">
                <div class="mt-0.5 flex shrink-0 items-center justify-center transition-all duration-300 {authEnabled ? 'h-10 w-10 rounded-[14px] bg-accent/15 border border-accent/25 text-accent shadow-[0_0_16px_-4px_rgba(77,148,255,0.2)]' : 'h-9 w-9 rounded-xl bg-surface-elevated border border-border-default text-text-muted'}">
                  <Icon icon={shieldIcon} class="{authEnabled ? 'h-[20px] w-[20px]' : 'h-[18px] w-[18px]'} transition-all duration-300" />
                </div>
                <div>
                  <p class="text-sm font-medium text-text-primary">{t("label.authEnabled")}</p>
                  <p class="mt-0.5 text-xs text-text-muted">{t("help.authEnabled")}</p>
                </div>
              </div>
              <ToggleSpring checked={authEnabled} onToggle={toggleAuth} label={t("label.authEnabled")} />
            </div>
          </div>
          <!-- Password change (visible when auth enabled) -->
          {#if authEnabled}
            <div class="border-t border-border-subtle px-4 py-4 sm:px-5 sm:py-5 space-y-3">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.changePassword")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.changePassword")}</p>
              </div>
              <div class="space-y-2">
                <input
                  type="password"
                  bind:value={currentPassword}
                  placeholder={t("label.currentPassword")}
                  maxlength={128}
                  autocomplete="current-password"
                  aria-label={t("label.currentPassword")}
                  class="w-full rounded-lg bg-surface-elevated border border-border-subtle px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted/70 outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent-muted"
                />
                <input
                  type="password"
                  bind:value={newPassword}
                  placeholder={t("label.newPassword")}
                  maxlength={128}
                  autocomplete="new-password"
                  aria-label={t("label.newPassword")}
                  class="w-full rounded-lg bg-surface-elevated border border-border-subtle px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted/70 outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent-muted"
                />
                <input
                  type="password"
                  bind:value={confirmPassword}
                  placeholder={t("label.confirmPassword")}
                  maxlength={128}
                  autocomplete="new-password"
                  aria-label={t("label.confirmPassword")}
                  class="w-full rounded-lg bg-surface-elevated border border-border-subtle px-3.5 py-2.5 text-sm text-text-primary placeholder:text-text-muted/70 outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-accent-muted"
                />
              </div>
              <button
                onclick={changePassword}
                disabled={passwordSaving || !currentPassword || !newPassword || !confirmPassword}
                class="btn-press rounded-lg border border-border-default px-3.5 py-2 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {t("btn.changePassword")}
              </button>
            </div>
          {/if}
          <!-- API token display (visible when auth enabled and token exists) -->
          {#if authEnabled && authToken}
            <div class="border-t border-border-subtle px-4 py-4 sm:px-5 sm:py-5 space-y-3">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.apiToken")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.apiToken")}</p>
              </div>
              <div class="flex items-center gap-2">
                <div class="flex-1 min-w-0 relative group">
                  <code class="block w-full truncate rounded-lg bg-surface-elevated border border-border-subtle px-3.5 py-2.5 text-xs font-mono text-text-secondary select-all tracking-wide">{authToken}</code>
                </div>
                <button
                  onclick={copyToken}
                  class="btn-press shrink-0 rounded-lg border border-border-default px-3.5 py-2.5 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary"
                >
                  {t("btn.copyToken")}
                </button>
              </div>
              <div class="flex items-center justify-between pt-1">
                <p class="text-xs text-text-muted">{t("help.regenerateToken")}</p>
                {#if regenConfirm}
                  <div class="flex gap-2 animate-slide-down">
                    <button onclick={() => { regenConfirm = false; }} class="btn-press rounded-lg border border-border-default px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text-secondary transition-colors">{t("btn.cancel")}</button>
                    <button onclick={doRegen} class="btn-press rounded-lg bg-status-warning px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-status-warning/90">{t("btn.confirmRegen")}</button>
                  </div>
                {:else}
                  <button onclick={confirmRegen} class="btn-press shrink-0 rounded-lg border border-border-default px-3 py-1.5 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary">{t("btn.regenerateToken")}</button>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      </section>

      <!-- System -->
      <section id="settings-system" class="scroll-mt-16 lg:scroll-mt-8 mt-12 space-y-3">
        <div class="flex items-center gap-2.5">
          <span class="h-3.5 w-0.5 rounded-full bg-accent"></span>
          <h2 class="text-xs font-semibold uppercase tracking-widest text-text-secondary">{t("section.system")}</h2>
        </div>
        <div class="card overflow-hidden">
          <!-- Settings Backup -->
          <div class="px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between gap-4">
              <div class="min-w-0">
                <p class="text-sm font-medium text-text-primary">{t("label.settingsBackup")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.settingsBackup")}</p>
              </div>
              <div class="flex gap-2 shrink-0">
                <button
                  onclick={exportSettings}
                  disabled={exporting}
                  class="btn-press rounded-lg border border-border-default px-4 py-2 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {t("btn.export")}
                </button>
                <button
                  onclick={triggerImport}
                  disabled={importing || importLoading}
                  class="btn-press rounded-lg border border-border-default px-4 py-2 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {importLoading ? t("btn.importing") : t("btn.import")}
                </button>
              </div>
            </div>
          </div>
          <!-- Software Update -->
          <div class="border-t border-border-subtle px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between gap-4">
              <div class="min-w-0">
                <p class="text-sm font-medium text-text-primary">{t("label.softwareUpdate")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.softwareUpdate")}</p>
              </div>
              <button
                onclick={checkForUpdates}
                disabled={updateChecking}
                class="btn-press shrink-0 rounded-lg border border-border-default px-4 py-2 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {updateChecking ? t("btn.checking") : t("btn.checkForUpdates")}
              </button>
            </div>
            {#if updateResult}
              <div class="mt-3 rounded-lg bg-surface-elevated px-3.5 py-3 space-y-2 animate-slide-down">
                {#if updateResult.error && !updateResult.available}
                  <p class="text-xs text-status-warning">{updateResult.error}</p>
                {:else if updateResult.available}
                  <div class="flex items-center justify-between">
                    <p class="text-xs font-medium text-status-ok">{t("label.commitsAvailable", { n: updateResult.commits_behind })}</p>
                    {#if updateConfirm}
                      <div class="flex gap-2 animate-slide-down">
                        <button onclick={() => { updateConfirm = false; }} class="btn-press rounded-lg border border-border-default px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text-secondary transition-colors">{t("btn.cancel")}</button>
                        <button onclick={doUpdate} class="btn-press rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-accent-hover">{t("btn.confirmUpdate")}</button>
                      </div>
                    {:else}
                      <button onclick={confirmUpdate} class="btn-press shrink-0 rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-accent-hover">{t("btn.updateNow")}</button>
                    {/if}
                  </div>
                  {#if updateResult.summary}
                    <pre class="text-[0.6875rem] leading-relaxed text-text-secondary font-mono whitespace-pre-wrap max-h-32 overflow-y-auto">{updateResult.summary}</pre>
                  {/if}
                {:else}
                  <p class="text-xs text-text-muted">{t("label.upToDate")}</p>
                {/if}
                {#if updateResult.lastChecked}
                  <p class="text-[0.625rem] text-text-muted/60">{t("label.lastChecked")}: {new Date(updateResult.lastChecked).toLocaleTimeString()}</p>
                {/if}
              </div>
            {/if}
          </div>
          <!-- Restart Services -->
          <div class="border-t border-border-subtle px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.restartServices")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.restartServices")}</p>
              </div>
              {#if restartConfirm}
                <div class="flex gap-2 animate-slide-down">
                  <button onclick={() => { restartConfirm = false; }} class="btn-press rounded-lg border border-border-default px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text-secondary transition-colors">{t("btn.cancel")}</button>
                  <button onclick={doRestart} class="btn-press rounded-lg bg-status-warning px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-status-warning/90">{t("btn.confirmRestart")}</button>
                </div>
              {:else}
                <button onclick={confirmRestart} class="btn-press shrink-0 rounded-lg border border-border-default px-4 py-2 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary">{t("btn.restart")}</button>
              {/if}
            </div>
          </div>
          <div class="border-t border-border-subtle px-4 py-4 sm:px-5 sm:py-5">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-text-primary">{t("label.rebootDevice")}</p>
                <p class="mt-0.5 text-xs text-text-muted">{t("help.rebootDevice")}</p>
              </div>
              {#if rebootConfirm}
                <div class="flex gap-2 animate-slide-down">
                  <button onclick={() => { rebootConfirm = false; }} class="btn-press rounded-lg border border-border-default px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text-secondary transition-colors">{t("btn.cancel")}</button>
                  <button onclick={doReboot} class="btn-press rounded-lg bg-status-critical px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-status-critical/90">{t("btn.confirmReboot")}</button>
                </div>
              {:else}
                <button onclick={confirmReboot} class="btn-press shrink-0 rounded-lg border border-border-default px-4 py-2 text-xs font-semibold text-text-secondary transition-colors hover:border-border-strong hover:text-text-primary">{t("btn.reboot")}</button>
              {/if}
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>

  <!-- Import Preview Modal -->
  {#if importPreview}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="animate-overlay fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      tabindex="-1"
      onkeydown={(e) => { if (e.key === "Escape") dismissPreview(); }}
    >
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <div class="absolute inset-0" onclick={dismissPreview}></div>
      <div class="animate-dialog relative w-full max-w-md rounded-2xl border border-border-subtle bg-surface-raised p-5 shadow-[var(--shadow-lg)]">
        <!-- Header -->
        <div class="flex h-9 w-9 items-center justify-center rounded-lg bg-accent-muted">
          <Icon icon={fileTextIcon} class="h-4.5 w-4.5 text-accent" />
        </div>
        <h3 class="mt-3 text-sm font-semibold text-text-primary">{t("label.importPreview")}</h3>

        {#if importPreview.changes.length === 0}
          <p class="mt-1 text-[0.8125rem] leading-relaxed text-text-secondary">{t("help.importNoChanges")}</p>
        {:else}
          <p class="mt-1 text-[0.8125rem] leading-relaxed text-text-secondary">{t("help.importChanges", { count: String(importPreview.changes.length) })}</p>

          <!-- Change list -->
          <div class="mt-4 max-h-72 space-y-1.5 overflow-y-auto pr-1">
            {#each importPreview.changes as change, i}
              <div
                class="animate-in rounded-lg border border-border-subtle bg-surface-overlay px-3.5 py-2.5"
                style="animation-delay: {Math.min(60 + i * 40, 400)}ms"
              >
                <p class="text-xs font-semibold tracking-wide text-text-primary">{change.key}</p>
                {#if isDeviceList(change.from) || isDeviceList(change.to)}
                  <div class="mt-1.5 grid grid-cols-[1fr_auto_1fr] items-start gap-2 text-[0.6875rem]">
                    <div class="space-y-1">
                      {#if isDeviceList(change.from)}
                        {#each change.from as device}
                          <div class="rounded bg-surface-elevated px-2 py-1 font-mono text-text-muted">
                            <span class="block truncate">{device.name || device.address}</span>
                            {#if device.name}<span class="block truncate text-[0.625rem] text-text-muted/60">{device.address}</span>{/if}
                          </div>
                        {/each}
                      {:else}
                        <span class="block rounded bg-surface-elevated px-2 py-1 font-mono text-text-muted">{formatValue(change.from, change.key)}</span>
                      {/if}
                    </div>
                    <Icon icon={chevronRightIcon} class="mt-1.5 h-3 w-3 shrink-0 text-text-muted" />
                    <div class="space-y-1">
                      {#if isDeviceList(change.to)}
                        {#each change.to as device}
                          <div class="rounded bg-accent-muted px-2 py-1 font-mono text-accent">
                            <span class="block truncate">{device.name || device.address}</span>
                            {#if device.name}<span class="block truncate text-[0.625rem] text-accent/60">{device.address}</span>{/if}
                          </div>
                        {/each}
                      {:else}
                        <span class="block rounded bg-accent-muted px-2 py-1 font-mono text-accent">{formatValue(change.to, change.key)}</span>
                      {/if}
                    </div>
                  </div>
                {:else}
                  <div class="mt-1.5 flex items-center gap-2 text-[0.6875rem]">
                    <span class="min-w-0 flex-1 truncate rounded bg-surface-elevated px-2 py-1 font-mono text-text-muted" title={formatValue(change.from, change.key)}>
                      {formatValue(change.from, change.key)}
                    </span>
                    <Icon icon={chevronRightIcon} class="h-3 w-3 shrink-0 text-text-muted" />
                    <span class="min-w-0 flex-1 truncate rounded bg-accent-muted px-2 py-1 font-mono text-accent" title={formatValue(change.to, change.key)}>
                      {formatValue(change.to, change.key)}
                    </span>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}

        <!-- Actions -->
        <div class="mt-5 flex justify-end gap-2.5">
          <button
            onclick={dismissPreview}
            disabled={importing}
            class="btn-press rounded-lg px-4 py-2.5 text-[0.8125rem] font-medium text-text-secondary transition-colors hover:bg-surface-overlay hover:text-text-primary disabled:opacity-40"
          >
            {t("btn.cancel")}
          </button>
          {#if importPreview.changes.length > 0}
            <button
              onclick={confirmImport}
              disabled={importing}
              class="btn-press rounded-lg bg-accent/10 px-4 py-2.5 text-[0.8125rem] font-semibold text-accent transition-colors hover:bg-accent/18 disabled:opacity-40"
            >
              {importing ? t("btn.importing") : t("btn.confirmImport")}
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/if}
{/if}
