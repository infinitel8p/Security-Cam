export default {
  // Navigation
  nav: {
    dashboard: "Dashboard",
    archive: "Archive",
    settings: "Settings",
  },

  // Page titles
  page: {
    dashboard: "Dashboard",
    archive: "Archive",
    settings: "Settings",
  },

  // Section headings
  section: {
    liveFeed: "Live Feed",
    systemHealth: "System Health",
    accessLog: "Access Log",
    activityTimeline: "Activity Timeline",
    devices: "Devices",
    camera: "Camera",
    appearance: "Appearance",
    feed: "Feed",
    storage: "Storage",
    triggerSensors: "Trigger Sensors",
    cameraRotation: "Camera Rotation",
    streamQuality: "Stream Quality",
  },

  // Status labels
  status: {
    online: "Online",
    offline: "Offline",
    armed: "Armed",
    starting: "Starting...",
    disabled: "Disabled",
    triggered: "Triggered",
    suppressed: "Suppressed",
    idle: "Idle",
    off: "Off",
    active: "Active",
    past: "Past",
    ok: "OK",
    noData: "No data",
    saving: "Saving...",
    saved: "Saved",
    applied: "Applied",
    scanning: "Scanning...",
    added: "Added",
    connectingToCamera: "Connecting to camera...",
    reconnecting: "Reconnecting...",
    loading: "Loading...",
  },

  // Buttons
  btn: {
    retry: "Retry",
    retryNow: "Retry now",
    record: "Record",
    stop: "Stop",
    fullscreen: "Fullscreen",
    exitFullscreen: "Exit fullscreen",
    cancel: "Cancel",
    delete: "Delete",
    deleting: "Deleting...",
    download: "Download",
    save: "Save Configuration",
    saving: "Saving...",
    apply: "Apply",
    applying: "Applying...",
    add: "Add",
    adding: "Adding...",
    close: "Close",
    dismiss: "Dismiss",
    browse: "Browse",
    select: "Select",
    showMore: "Show more",
    showLess: "Show less",
    newer: "Newer",
    older: "Older",
    clearFilters: "Clear filters",
    clearAllFilters: "Clear all filters",
    scanForDevices: "Scan for devices",
    addDevice: "Add device",
    removeDevice: "Remove device",
    enterManually: "Enter manually",
    rescan: "Rescan",
    displayOnly: "Display only",
    applyToStream: "Apply to stream",
    startTest: "Start Test",
    stopTest: "Stop Test",
    simulateTrigger: "Simulate Trigger",
    firing: "Firing...",
    simulateRelease: "Simulate Release",
    releasing: "Releasing...",
    showWiring: "Show wiring guide",
    hideWiring: "Hide wiring guide",
    downloadRecording: "Download recording",
    deleteRecording: "Delete recording",
  },

  // Labels
  label: {
    last72h: "Last 72h",
    last7days: "Last 7 days",
    liveFeed: "Live Feed",
    temperature: "Temp",
    cpu: "CPU",
    disk: "Disk",
    ram: "RAM",
    uptime: "Uptime",
    throttle: "Throttle",
    sensor: "Sensor",
    gpio: "GPIO",
    bluetooth: "BT",
    wifi: "WiFi",
    accessPoint: "AP",
    eventsLast7Days: "Events - Last 7 days",
    activityHeatmap: "Activity",
    healthLast72h: "Health - Last 72h",
    now: "Now",
    recordings: "recording | recordings",
    clips: "clip | clips",
    videoSaveLocation: "Video Save Location",
    sensorType: "Sensor Type",
    gpioPin: "GPIO Pin",
    holdTimeout: "Hold Timeout",
    seconds: "seconds",
    testWiring: "Test Wiring",
    invertTrigger: "Invert trigger",
    autoRecording: "Auto-recording",
    scanLines: "Scan lines",
    mockSensorControls: "Mock Sensor Controls",
    preset: "Preset",
    width: "Width",
    height: "Height",
    fps: "FPS",
    custom: "Custom",
    recommended: "Recommended",
    discoveredDevices: "Discovered devices",
    sensorPin: "Sensor Pin",
    raspberryPi: "Raspberry Pi",
    sinceBoot: "Since boot",
    high: "HIGH",
    low: "LOW",
    bluetoothDevices: "Bluetooth Devices",
    wifiDevices: "WiFi Devices",
    status: "Status",
    calibration: "Calibration",
  },

  // Input placeholders
  input: {
    searchRecordings: "Search recordings...",
    macAddress: "MAC address",
    nameOptional: "Name (optional)",
  },

  // Filter & sort
  filter: {
    allTime: "All time",
    today: "Today",
    thisWeek: "This week",
    thisMonth: "This month",
  },
  sort: {
    newestFirst: "Newest first",
    oldestFirst: "Oldest first",
    name: "Name",
  },

  // Empty states
  empty: {
    archive: "All quiet on the home front",
    archiveDesc: "Recordings will appear here once you start capturing",
    noMatches: "No recordings match your filters",
    accessLog: "No devices have come or gone - all quiet",
    activityTimeline: "System is running smoothly - no events to report",
    noDevicesTracked: "No devices tracked",
    noDevicesConfigured: "No devices configured",
    noSubdirectories: "No subdirectories",
    addDevicesHint: "Add a phone or laptop in {link} for presence detection",
  },

  // Errors
  error: {
    accessLog: "Unable to load access log",
    activityTimeline: "Unable to load activity timeline",
    archive: "Unable to load archive",
    checkBackend: "Check that the backend is running",
    connectionStatus: "Unable to reach connection status",
    eventData: "Unable to load event data",
    healthData: "Unable to load health data",
    sensorConfig: "Unable to load sensor configuration",
    sensorStatus: "Unable to load sensor status",
    systemMonitor: "Unable to reach system monitor",
    settings: "Unable to load settings",
    directories: "Failed to load directories",
    streamDisconnected: "Stream disconnected",
    connectFailed: "Failed to connect to stream",
  },

  // Toast messages
  toast: {
    recordingStarted: "Recording started",
    recordingStopped: "Recording stopped",
    toggleRecordingFailed: "Failed to toggle recording",
    recordingDeleted: "Recording deleted",
    deleteRecordingFailed: "Failed to delete recording",
    deviceAdded: "Added {name}",
    deviceRemoved: "Device removed",
    addDeviceFailed: "Failed to add device",
    removeDeviceFailed: "Failed to remove device",
    sensorConfigured: "Sensor configured",
    sensorEnabled: "Sensor enabled",
    sensorDisabled: "Sensor disabled",
    saveLocationUpdated: "Save location updated",
    saveLocationFailed: "Failed to save location",
    saveFailed: "Failed to save setting",
    streamSettingsApplied: "Stream settings applied",
    streamSettingsFailed: "Failed to save stream settings",
    rotationFailed: "Failed to save rotation settings",
  },

  // Dialogs
  dialog: {
    deleteTitle: "Delete recording?",
    deleteMessage: "{filename} will be permanently removed.",
    selectDirectory: "Select Directory",
  },

  // Events
  event: {
    recordingStarted: "Recording started",
    recordingStopped: "Recording stopped",
    motionDetected: "Motion detected",
    streamDisconnected: "Stream disconnected",
    streamReconnected: "Stream reconnected",
    unauthorizedAccess: "Unauthorized access",
    systemBoot: "System boot",
    deviceArrived: "Device arrived",
    deviceLeft: "Device left",
    sensorTriggered: "Sensor triggered",
    sensorReleased: "Sensor released",
    sensorArmed: "Sensor armed",
    sensorDisarmed: "Sensor disarmed",
  },

  // Relative time
  time: {
    justNow: "Just now",
    minutesAgo: "{n}m ago",
    hoursAgo: "{n}h ago",
    daysAgo: "{n}d ago",
  },

  // Help text
  help: {
    autoRecording: "Trigger recording when sensor fires and no tracked device is present",
    gpioPin: "BCM pin number (0-27). Default for this sensor: GPIO {n}",
    testWiring: "Read the live GPIO pin state to verify your sensor is connected correctly",
    testInstructions: "Activate the sensor now - you should see the value change. Polling every 500ms.",
    holdTimeout: "Keep recording for this long after sensor releases (prevents gaps from brief interruptions)",
    invertActive: "Currently: GPIO LOW (0) triggers recording - e.g. reed switch magnet removed, door opened",
    invertInactive: "Currently: GPIO HIGH (1) triggers recording - e.g. PIR detects motion, button pressed",
    displayRotation: "Rotates the video on the dashboard only. Recordings are not affected. No performance cost.",
    hardwareRotation: "Applies rotation at the hardware level via MediaMTX. No performance cost for 0°/180°. Recordings will also be rotated.",
    hardwareRotationLimited: "Hardware rotation only supports 0° and 180°. The {angle}° rotation will be applied as display-only instead.",
    streamInterrupt: "Changing stream settings will briefly interrupt the live feed while MediaMTX restarts.",
    scanLines: "Subtle CRT-style overlay on the live camera feed",
    presenceGating: "Sensor-triggered recording is gated by presence detection. If any tracked Bluetooth or WiFi device is connected, the sensor trigger is ignored. Manual recording from the dashboard is always allowed regardless of sensor or presence state.",
    searchingBluetooth: "Searching for nearby Bluetooth devices...",
    checkingWiFi: "Checking connected WiFi clients...",
    addDevicesForPresence: "Add a phone or laptop in Settings for presence detection",
  },

  // Rotation options
  rotation: {
    default: "0° - Default",
    clockwise: "90° - Clockwise",
    flipped: "180° - Flipped",
    counterClockwise: "270° - Counter-clockwise",
  },

  // Throttle status
  throttle: {
    lowVoltage: "Low voltage",
    throttled: "Throttled",
    freqCapped: "Freq cap",
    tempLimit: "Temp limit",
  },

  // Theme labels
  theme: {
    system: "System",
    light: "Light",
    dark: "Dark",
  },

  // Badge
  badge: {
    rec: "REC",
    live: "LIVE",
  },

  // Setup checklist
  setup: {
    title: "Get your camera ready",
    stepProgress: "{n} of {total} steps done",
    addDevices: "Add your phone or laptop",
    addDevicesDesc: "Bluetooth or WiFi device for presence detection",
    addDevicesDone: "Devices configured",
    enableSensor: "Enable a trigger sensor",
    enableSensorDesc: "Auto-record when motion or door activity is detected",
    enableSensorDone: "Sensor armed",
  },

  // Arrived/Left
  device: {
    arrived: "Arrived",
    left: "Left",
  },

  // Language
  language: {
    label: "Language",
    en: "English",
    de: "Deutsch",
    fr: "Français",
    es: "Español",
    it: "Italiano",
  },

  // Calibration
  calibration: {
    sensitivity: "Sensitivity",
    sensitivity_min: "Low",
    sensitivity_max: "High",
    sensitivity_help: "How easily motion triggers the sensor. Lower values require more sustained movement.",
    pulse_count: "Pulse threshold",
    pulse_count_min: "Sensitive",
    pulse_count_max: "Firm",
    pulse_count_help: "Number of impacts required to trigger. Higher values filter out accidental bumps.",
    pulse_window: "Counting window",
    pulse_window_min: "1s",
    pulse_window_max: "30s",
    pulse_window_help: "Time window to count pulses in. Only used when pulse threshold is greater than 1.",
    settle_time: "Settle time",
    settle_time_min: "Instant",
    settle_time_max: "5s",
    settle_time_help: "How long the sensor must stay tilted before triggering. Filters out brief bumps and vibrations.",
    touch_duration: "Touch duration",
    touch_duration_min: "Instant",
    touch_duration_max: "3s",
    touch_duration_help: "How long the touch must be held before triggering. Filters out accidental brushes.",
  },

  // Wiring
  wiring: {
    power3v3: "3.3V Power",
    power5v: "5V Power",
    ground: "Ground",
    signal: "Signal",
  },
} as const;
