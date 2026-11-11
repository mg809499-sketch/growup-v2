"use client";

import { useCallback, useEffect, useRef } from "react";

export function Modal({
  title,
  onClose,
  children,
  describedBy,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  describedBy?: string;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  const close = useCallback(() => {
    onClose();
    triggerRef.current?.focus();
  }, [onClose]);

  useEffect(() => {
    triggerRef.current = document.activeElement as HTMLElement | null;
    const previouslyFocused = triggerRef.current;

    const focusables = () =>
      Array.from(
        panelRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );

    focusables()[0]?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close();
        return;
      }
      if (event.key !== "Tab") return;
      const nodes = focusables();
      if (nodes.length === 0) {
        event.preventDefault();
        return;
      }
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
      previouslyFocused?.focus();
    };
  }, [close]);

  return (
    <div
      role="presentation"
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 backdrop-blur-[2px] sm:items-center sm:p-6"
      onClick={close}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        aria-describedby={describedBy}
        className="max-h-[92dvh] w-full overflow-y-auto border border-[var(--hairline)] bg-[var(--surface-2)] p-6 shadow-2xl sm:max-w-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <h2 className="display text-2xl leading-none">{title}</h2>
          <button
            type="button"
            onClick={close}
            aria-label="Cerrar"
            className="label border border-[var(--hairline)] px-3 py-2 text-[var(--muted)] transition-colors hover:text-[var(--ink)]"
          >
            Esc
          </button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}
