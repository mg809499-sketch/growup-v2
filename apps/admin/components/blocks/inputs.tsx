"use client";

import { useEffect, useId, useRef, useState } from "react";

import {
  listMediaAction,
  type MediaItem,
} from "@/app/(dashboard)/builder/actions";

const inputClass =
  "w-full border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus-visible:border-slate-500";

export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mono mb-1 block text-[10px] uppercase tracking-[0.14em] text-slate-500">
        {label}
      </span>
      {children}
      {hint ? <span className="mt-1 block text-[11px] text-slate-500">{hint}</span> : null}
    </label>
  );
}

export function TextInput({
  value,
  onChange,
  maxLength,
  placeholder,
  mono,
}: {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
  placeholder?: string;
  mono?: boolean;
}) {
  return (
    <input
      type="text"
      value={value}
      maxLength={maxLength}
      placeholder={placeholder}
      onChange={(event) => onChange(event.target.value)}
      className={`${inputClass} ${mono ? "font-mono text-xs" : ""}`}
    />
  );
}

export function TextArea({
  value,
  onChange,
  maxLength,
  rows = 4,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <>
      <textarea
        value={value}
        rows={rows}
        maxLength={maxLength}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
        className={`${inputClass} resize-y leading-relaxed`}
      />
      {maxLength ? (
        <span className="mt-1 block text-right text-[11px] text-slate-500">
          {value.length} / {maxLength}
        </span>
      ) : null}
    </>
  );
}

export function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  return (
    <select value={value} onChange={(event) => onChange(event.target.value)} className={inputClass}>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

export function NumberInput({
  value,
  onChange,
  min,
  max,
}: {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <input
      type="number"
      value={Number.isFinite(value) ? value : 0}
      min={min}
      max={max}
      onChange={(event) => onChange(Number(event.target.value))}
      className={inputClass}
    />
  );
}

export function Checkbox({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 accent-slate-900"
      />
      {label}
    </label>
  );
}

export function LinkInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: { label: string; href: string } | null;
  onChange: (value: { label: string; href: string } | null) => void;
}) {
  const enabled = value !== null;
  return (
    <div>
      <Checkbox
        label={label}
        checked={enabled}
        onChange={(checked) => onChange(checked ? { label: "", href: "" } : null)}
      />
      {enabled && value ? (
        <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_1.4fr]">
          <input
            type="text"
            value={value.label}
            placeholder="Texto"
            maxLength={60}
            onChange={(event) => onChange({ ...value, label: event.target.value })}
            className={inputClass}
          />
          <input
            type="text"
            value={value.href}
            placeholder="/ruta o https://…"
            maxLength={2048}
            onChange={(event) => onChange({ ...value, href: event.target.value })}
            className={`${inputClass} font-mono text-xs`}
          />
        </div>
      ) : null}
    </div>
  );
}

export function RemoveRowButton({ onClick, label }: { onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:border-red-300 hover:text-red-600"
    >
      ✕
    </button>
  );
}

export function ImageInput({
  value,
  onChange,
  required,
}: {
  value: { url: string; alt: string } | null;
  onChange: (value: { url: string; alt: string } | null) => void;
  required?: boolean;
}) {
  const current = value ?? { url: "", alt: "" };
  const [pickerOpen, setPickerOpen] = useState(false);

  return (
    <div className="space-y-2 border border-slate-200 bg-slate-50 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
          Imagen{required ? " *" : ""}
        </span>
        <button
          type="button"
          onClick={() => setPickerOpen(true)}
          className="text-xs font-medium text-slate-700 underline underline-offset-2 hover:text-slate-900"
        >
          Elegir de biblioteca
        </button>
      </div>
      {current.url && /^https?:\/\//.test(current.url) ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={current.url}
          alt={current.alt || "Vista previa"}
          className="h-24 w-full border border-slate-200 object-cover"
        />
      ) : (
        <div className="flex h-24 w-full items-center justify-center border border-dashed border-slate-300 text-[11px] text-slate-400">
          sin imagen
        </div>
      )}
      <input
        type="url"
        value={current.url}
        placeholder="https://… (URL pública de la imagen)"
        maxLength={2048}
        onChange={(event) => onChange({ ...current, url: event.target.value })}
        className={`${inputClass} font-mono text-xs`}
      />
      <input
        type="text"
        value={current.alt}
        placeholder="Texto alternativo (obligatorio)"
        maxLength={200}
        onChange={(event) => onChange({ ...current, alt: event.target.value })}
        className={inputClass}
      />
      {value && !required ? (
        <button
          type="button"
          onClick={() => onChange(null)}
          className="text-[11px] text-slate-500 underline underline-offset-2 hover:text-red-600"
        >
          Quitar imagen
        </button>
      ) : null}
      {pickerOpen ? (
        <MediaPicker
          onClose={() => setPickerOpen(false)}
          onPick={(item) => {
            onChange({ url: item.url, alt: item.alt || item.filename });
            setPickerOpen(false);
          }}
        />
      ) : null}
    </div>
  );
}

function MediaPicker({
  onClose,
  onPick,
}: {
  onClose: () => void;
  onPick: (item: MediaItem) => void;
}) {
  const titleId = useId();
  const [offset, setOffset] = useState(0);
  const [items, setItems] = useState<MediaItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    listMediaAction(offset).then((result) => {
      if (cancelled) return;
      if (result.ok) {
        setItems(result.items);
        setError(null);
      } else {
        setError(result.error);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [offset]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        className="w-full max-w-2xl border border-slate-200 bg-white p-5 shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 id={titleId} className="text-base font-semibold text-slate-900">
            Biblioteca del tenant
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="border border-slate-200 px-2 py-1 text-sm text-slate-600 hover:border-slate-400"
          >
            Cerrar
          </button>
        </div>
        {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
        {!items && !error ? <p className="mt-4 text-sm text-slate-500">Cargando media…</p> : null}
        {items && items.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">
            No hay imágenes listas. Sube assets desde Media; los URLs públicos usan
            NEXT_PUBLIC_MEDIA_BASE_URL.
          </p>
        ) : null}
        <ul className="mt-4 grid max-h-96 grid-cols-2 gap-3 overflow-y-auto sm:grid-cols-3">
          {items?.map((item) =>
            item.url ? (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => onPick(item)}
                  className="w-full border border-slate-200 text-left hover:border-slate-500"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={item.url}
                    alt={item.alt || item.filename}
                    loading="lazy"
                    className="h-24 w-full object-cover"
                  />
                  <span className="block truncate px-2 py-1 text-[11px] text-slate-600">
                    {item.filename}
                  </span>
                </button>
              </li>
            ) : (
              <li
                key={item.id}
                className="border border-dashed border-slate-300 p-2 text-[11px] text-slate-500"
              >
                {item.filename} — configura NEXT_PUBLIC_MEDIA_BASE_URL para habilitar
              </li>
            ),
          )}
        </ul>
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - 24))}
            className="border border-slate-200 px-3 py-1.5 text-xs disabled:opacity-40"
          >
            ← Anterior
          </button>
          <button
            type="button"
            onClick={() => setOffset(offset + 24)}
            className="border border-slate-200 px-3 py-1.5 text-xs"
          >
            Siguiente →
          </button>
        </div>
      </div>
    </div>
  );
}
