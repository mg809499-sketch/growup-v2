"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import {
  completeUploadAction,
  getMediaAssetStatusAction,
  requestUploadUrlAction,
} from "@/app/(dashboard)/media/actions";

const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const ALLOWED_MIMES = new Set(["image/jpeg", "image/png", "image/webp"]);
const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 90_000;

type Flow =
  | { phase: "idle" }
  | { phase: "signing" }
  | { phase: "uploading"; progress: number }
  | { phase: "completing" }
  | { phase: "processing"; assetId: string }
  | { phase: "ready"; assetId: string }
  | { phase: "failed"; error: string };

/**
 * Carga directa a R2 con URL prefirmada: el navegador nunca toca las
 * credenciales. Requiere CORS en el bucket/MinIO (ver docs/media-upload-cors.md).
 */
export function MediaUploader() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [alt, setAlt] = useState("");
  const [flow, setFlow] = useState<Flow>({ phase: "idle" });
  const [dragOver, setDragOver] = useState(false);
  const pollDeadlineRef = useRef(0);

  const reset = useCallback(() => {
    setFile(null);
    setAlt("");
    setFlow({ phase: "idle" });
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }, []);

  const acceptFile = useCallback((candidate: File | undefined | null) => {
    if (!candidate) return;
    if (!ALLOWED_MIMES.has(candidate.type)) {
      setFlow({ phase: "failed", error: "Solo se aceptan JPEG, PNG o WebP" });
      return;
    }
    if (candidate.size <= 0 || candidate.size > MAX_IMAGE_BYTES) {
      setFlow({ phase: "failed", error: "La imagen supera el límite de 10 MB" });
      return;
    }
    setFile(candidate);
    setAlt((current) => current || candidate.name.replace(/\.[^.]+$/, ""));
    setFlow({ phase: "idle" });
  }, []);

  // Poll de procesamiento (el worker genera variantes + blurhash).
  useEffect(() => {
    if (flow.phase !== "processing" || !file) return;
    let cancelled = false;
    pollDeadlineRef.current = Date.now() + POLL_TIMEOUT_MS;

    async function tick(): Promise<void> {
      if (flow.phase !== "processing") return;
      const assetId = flow.assetId;
      const result = await getMediaAssetStatusAction(assetId);
      if (cancelled) return;
      if (result.ok && result.status === "ready") {
        setFlow({ phase: "ready", assetId });
        router.refresh();
        return;
      }
      if (result.ok && result.status === "failed") {
        setFlow({ phase: "failed", error: "El procesamiento falló; sube la imagen de nuevo" });
        return;
      }
      if (Date.now() >= pollDeadlineRef.current) {
        setFlow({
          phase: "failed",
          error: "El procesamiento tardó demasiado; revisa la biblioteca en unos minutos",
        });
        return;
      }
      window.setTimeout(() => void tick(), POLL_INTERVAL_MS);
    }

    void tick();
    return () => {
      cancelled = true;
    };
  }, [flow, file, router]);

  const upload = useCallback(async () => {
    if (!file) return;
    const cleanAlt = alt.trim();
    if (!cleanAlt) {
      setFlow({ phase: "failed", error: "El alt text es obligatorio" });
      return;
    }

    setFlow({ phase: "signing" });
    const ticket = await requestUploadUrlAction({
      filename: file.name,
      contentType: file.type,
      sizeBytes: file.size,
    });
    if (!ticket.ok) {
      setFlow({ phase: "failed", error: ticket.error });
      return;
    }

    setFlow({ phase: "uploading", progress: 0 });
    const uploadResult = await new Promise<{ ok: true } | { ok: false; error: string }>(
      (resolve) => {
        const xhr = new XMLHttpRequest();
        xhr.open("PUT", ticket.uploadUrl);
        xhr.setRequestHeader("Content-Type", file.type);
        // El bucket firmó Content-Length implícitamente con el cuerpo; no se envía cabecera manual.
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            setFlow({ phase: "uploading", progress: Math.round((event.loaded / event.total) * 100) });
          }
        };
        xhr.onload = () =>
          xhr.status >= 200 && xhr.status < 300
            ? resolve({ ok: true })
            : resolve({ ok: false, error: `R2 respondió ${xhr.status}` });
        xhr.onerror = () =>
          resolve({ ok: false, error: "Error de red al subir a R2 (¿CORS configurado?)" });
        xhr.send(file);
      },
    );
    if (!uploadResult.ok) {
      setFlow({ phase: "failed", error: uploadResult.error });
      return;
    }

    setFlow({ phase: "completing" });
    const completed = await completeUploadAction(ticket.assetId, cleanAlt);
    if (!completed.ok) {
      setFlow({ phase: "failed", error: completed.error });
      return;
    }

    setFlow({ phase: "processing", assetId: ticket.assetId });
  }, [file, alt]);

  return (
    <div className="border border-slate-200 bg-white p-4">
      <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
        Subir imagen
      </p>

      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragOver(false);
          acceptFile(event.dataTransfer.files?.[0]);
        }}
        className={`mt-3 flex h-28 cursor-pointer flex-col items-center justify-center border border-dashed px-4 text-center transition-colors ${
          dragOver ? "border-emerald-500 bg-emerald-50" : "border-slate-300 hover:border-slate-400"
        }`}
      >
        <p className="text-sm text-slate-600">
          {file ? file.name : "Arrastra una imagen aquí o haz clic para elegir"}
        </p>
        <p className="mt-1 text-[11px] text-slate-400">JPEG, PNG o WebP · máx. 10 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(event) => acceptFile(event.target.files?.[0])}
        />
      </div>

      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end">
        <label className="flex-1">
          <span className="mono mb-1 block text-[10px] uppercase tracking-[0.14em] text-slate-500">
            Alt text *
          </span>
          <input
            type="text"
            value={alt}
            maxLength={300}
            placeholder="Describe la imagen para accesibilidad"
            onChange={(event) => setAlt(event.target.value)}
            className="w-full border border-slate-200 px-3 py-2 text-sm outline-none focus-visible:border-slate-500"
          />
        </label>
        <button
          type="button"
          onClick={upload}
          disabled={!file || flow.phase === "signing" || flow.phase === "uploading" || flow.phase === "completing" || flow.phase === "processing"}
          className="border border-slate-900 bg-slate-900 px-5 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
        >
          Subir
        </button>
      </div>

      <div aria-live="polite" className="mt-3 text-sm">
        {flow.phase === "signing" ? (
          <p className="text-slate-500">Solicitando URL de subida…</p>
        ) : null}
        {flow.phase === "uploading" ? (
          <p className="text-slate-600">
            Subiendo a R2… {flow.progress}%
            <span className="mt-1 block h-1.5 w-full bg-slate-100">
              <span
                className="block h-1.5 bg-slate-900 transition-all"
                style={{ width: `${flow.progress}%` }}
              />
            </span>
          </p>
        ) : null}
        {flow.phase === "completing" ? (
          <p className="text-slate-500">Verificando tamaño y encolando procesamiento…</p>
        ) : null}
        {flow.phase === "processing" ? (
          <p className="text-slate-500">Procesando: quitando EXIF y generando variantes…</p>
        ) : null}
        {flow.phase === "ready" ? (
          <p className="text-emerald-700">
            Imagen lista en la biblioteca.{" "}
            <button
              type="button"
              onClick={reset}
              className="underline underline-offset-2 hover:text-emerald-900"
            >
              Subir otra
            </button>
          </p>
        ) : null}
        {flow.phase === "failed" ? (
          <p className="text-red-700" role="alert">
            {flow.error}{" "}
            <button
              type="button"
              onClick={reset}
              className="underline underline-offset-2 hover:text-red-900"
            >
              Reintentar
            </button>
          </p>
        ) : null}
      </div>
    </div>
  );
}
