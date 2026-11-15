// @growup/config — utilidades, constantes y registro cerrado de temas/fuentes.
// Dinero SIEMPRE en centavos enteros COP.

export const COP_CURRENCY = "COP";
export const SUPPORT_EMAIL = "soporte@growup.com";
export const LEGAL_REVIEW_BANNER = "El texto legal está en revisión.";

export const DEFAULT_SHIPPING_ZONES = [
  { code: "bogota", name: "Bogotá D.C.", price_cents: 800_000 },
  { code: "resto", name: "Resto del país", price_cents: 1_500_000 },
] as const;

export const THEME_PRESETS = ["ropa", "joyeria", "nova"] as const;
export type ThemePreset = (typeof THEME_PRESETS)[number];

export const FONT_REGISTRY = [
  "Anton",
  "Space Grotesk",
  "Space Mono",
  "Playfair Display",
  "Plus Jakarta Sans",
  "Unbounded",
  "Geist",
  "Geist Mono",
  "Inter",
  "JetBrains Mono",
] as const;
export type RegisteredFont = (typeof FONT_REGISTRY)[number];

export const COLOR_SCHEMES = ["light", "dark", "system"] as const;
export type ThemeColorScheme = (typeof COLOR_SCHEMES)[number];

export const MOTION_LEVELS = ["none", "subtle", "technical"] as const;
export type ThemeMotionLevel = (typeof MOTION_LEVELS)[number];

export interface ThemeColorsV1 {
  surface: string;
  surface_2: string;
  ink: string;
  signal: string;
  muted: string;
  hairline: string;
}

export interface ThemeTokensV1 {
  schema_version: 1;
  preset: ThemePreset;
  color_scheme: ThemeColorScheme;
  font_display: RegisteredFont;
  font_body: RegisteredFont;
  font_mono: RegisteredFont;
  colors: ThemeColorsV1;
  radius_px: number;
  clip_angle_px: number;
  motion: ThemeMotionLevel;
}

export const PRESET_DEFAULT_TOKENS: Readonly<Record<ThemePreset, ThemeTokensV1>> = {
  nova: {
    schema_version: 1,
    preset: "nova",
    color_scheme: "light",
    font_display: "Unbounded",
    font_body: "Geist",
    font_mono: "Geist Mono",
    colors: {
      surface: "#ffffff",
      surface_2: "#f4f6fb",
      ink: "#0d0d0d",
      signal: "#111111",
      muted: "#525866",
      hairline: "#e2e8f0",
    },
    radius_px: 16,
    clip_angle_px: 0,
    motion: "technical",
  },
  ropa: {
    schema_version: 1,
    preset: "ropa",
    color_scheme: "light",
    font_display: "Anton",
    font_body: "Space Grotesk",
    font_mono: "Space Mono",
    colors: {
      surface: "#f4f3ee",
      surface_2: "#faf9f4",
      ink: "#0d0d0d",
      signal: "#ff3b1d",
      muted: "#8c887b",
      hairline: "#e5e3dc",
    },
    radius_px: 0,
    clip_angle_px: 0,
    motion: "subtle",
  },
  joyeria: {
    schema_version: 1,
    preset: "joyeria",
    color_scheme: "dark",
    font_display: "Playfair Display",
    font_body: "Plus Jakarta Sans",
    font_mono: "Plus Jakarta Sans",
    colors: {
      surface: "#0b0b0c",
      surface_2: "#141416",
      ink: "#f5f4f0",
      signal: "#d4af37",
      muted: "#9e9b93",
      hairline: "#26262b",
    },
    radius_px: 0,
    clip_angle_px: 0,
    motion: "subtle",
  },
};

export function isThemePreset(value: unknown): value is ThemePreset {
  return typeof value === "string" && (THEME_PRESETS as readonly string[]).includes(value);
}

export function isRegisteredFont(value: unknown): value is RegisteredFont {
  return typeof value === "string" && (FONT_REGISTRY as readonly string[]).includes(value);
}

export function resolveThemePreset(
  theme?: Record<string, unknown> | null,
  tenantSlug?: string | null,
): ThemePreset {
  if (theme && isThemePreset(theme.preset)) {
    return theme.preset;
  }
  const displayFont = theme?.font_display ?? theme?.display;
  if (displayFont === "Unbounded") {
    return "nova";
  }
  if (displayFont === "Playfair Display") {
    return "joyeria";
  }
  if (displayFont === "Anton") {
    return "ropa";
  }
  if (tenantSlug === "joyeria" && theme && Object.keys(theme).length > 0) {
    return "joyeria";
  }
  if (tenantSlug === "ropa" && theme && Object.keys(theme).length > 0) {
    return "ropa";
  }
  return "nova";
}

const SAFE_CSS_COLOR = /^(#[0-9a-fA-F]{3,8}|oklch\([0-9.% /deg+-]+\)|rgb\([0-9., %/]+\)|hsl\([0-9., %/deg]+\))$/;

function pickSafeColor(value: unknown, fallback: string): string {
  return typeof value === "string" && SAFE_CSS_COLOR.test(value.trim())
    ? value.trim()
    : fallback;
}

export function resolveThemeCssVars(
  theme?: Record<string, unknown> | null,
  tenantSlug?: string | null,
): Record<string, string> {
  const preset = resolveThemePreset(theme, tenantSlug);
  const defaults = PRESET_DEFAULT_TOKENS[preset].colors;
  const nestedColors =
    theme && typeof theme.colors === "object" && theme.colors !== null && !Array.isArray(theme.colors)
      ? (theme.colors as Record<string, unknown>)
      : {};

  return {
    "--surface": pickSafeColor(nestedColors.surface ?? theme?.surface, defaults.surface),
    "--surface-2": pickSafeColor(nestedColors.surface_2 ?? theme?.surface_2, defaults.surface_2),
    "--ink": pickSafeColor(nestedColors.ink ?? theme?.ink, defaults.ink),
    "--signal": pickSafeColor(nestedColors.signal ?? theme?.signal, defaults.signal),
    "--muted": pickSafeColor(nestedColors.muted ?? theme?.muted, defaults.muted),
    "--hairline": pickSafeColor(nestedColors.hairline ?? theme?.hairline, defaults.hairline),
  };
}

export function formatPrice(cents: number): string {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: COP_CURRENCY,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

export function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
