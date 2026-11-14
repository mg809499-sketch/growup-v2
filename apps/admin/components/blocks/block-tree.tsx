"use client";

import { useState } from "react";

import { BLOCK_DEFS, blockLabel, type Block } from "@/lib/builder-blocks";

export function BlockTree({
  blocks,
  selectedIndex,
  onSelect,
  onAdd,
  onDuplicate,
  onRemove,
  onReorder,
  onMove,
  canRemove,
}: {
  blocks: Block[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  onAdd: (type: string) => void;
  onDuplicate: (index: number) => void;
  onRemove: (index: number) => void;
  onReorder: (from: number, to: number) => void;
  onMove: (index: number, direction: -1 | 1) => void;
  canRemove: boolean;
}) {
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const [dragging, setDragging] = useState<number | null>(null);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 px-4 py-3">
        <p className="mono text-[10px] uppercase tracking-[0.18em] text-slate-500">
          Árbol de bloques
        </p>
      </div>
      <ul className="flex-1 divide-y divide-slate-100 overflow-y-auto">
        {blocks.map((block, index) => {
          const selected = index === selectedIndex;
          const isDropTarget = dropIndex === index && dragging !== null && dragging !== index;
          return (
            <li
              key={block.id}
              draggable
              onDragStart={(event) => {
                event.dataTransfer.setData("text/plain", String(index));
                event.dataTransfer.effectAllowed = "move";
                setDragging(index);
              }}
              onDragEnd={() => {
                setDragging(null);
                setDropIndex(null);
              }}
              onDragOver={(event) => {
                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
                setDropIndex(index);
              }}
              onDragLeave={() => setDropIndex((current) => (current === index ? null : current))}
              onDrop={(event) => {
                event.preventDefault();
                const from = Number(event.dataTransfer.getData("text/plain"));
                if (Number.isInteger(from) && from !== index) {
                  onReorder(from, index);
                }
                setDragging(null);
                setDropIndex(null);
              }}
              className={`group flex items-center gap-2 px-3 py-2 transition-colors ${
                selected ? "bg-slate-100" : "hover:bg-slate-50"
              } ${isDropTarget ? "bg-emerald-50 outline outline-1 -outline-offset-1 outline-emerald-400" : ""} ${
                dragging === index ? "opacity-50" : ""
              }`}
            >
              <span
                aria-hidden
                className="cursor-grab select-none text-slate-400 active:cursor-grabbing"
                title="Arrastrar para reordenar"
              >
                ⋮⋮
              </span>
              <button
                type="button"
                onClick={() => onSelect(index)}
                className="flex min-w-0 flex-1 items-center gap-2 text-left"
              >
                <span className="mono w-6 shrink-0 text-[10px] text-slate-400">{index + 1}</span>
                <span className="min-w-0">
                  <span className="block truncate text-xs font-medium text-slate-800">
                    {blockLabel(block.type)}
                  </span>
                  <span className="mono block truncate text-[9px] text-slate-400">
                    {block.id}
                  </span>
                </span>
              </button>
              <span className="flex shrink-0 items-center gap-1">
                <button
                  type="button"
                  onClick={() => onMove(index, -1)}
                  disabled={index === 0}
                  aria-label="Subir"
                  title="Subir"
                  className="border border-slate-200 px-1.5 py-0.5 text-[10px] text-slate-500 disabled:opacity-30"
                >
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => onMove(index, 1)}
                  disabled={index === blocks.length - 1}
                  aria-label="Bajar"
                  title="Bajar"
                  className="border border-slate-200 px-1.5 py-0.5 text-[10px] text-slate-500 disabled:opacity-30"
                >
                  ↓
                </button>
                <button
                  type="button"
                  onClick={() => onDuplicate(index)}
                  aria-label="Duplicar"
                  title="Duplicar"
                  className="border border-slate-200 px-1.5 py-0.5 text-[10px] text-slate-500 hover:border-slate-400"
                >
                  ⧉
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(index)}
                  disabled={!canRemove}
                  aria-label="Eliminar"
                  title="Eliminar"
                  className="border border-slate-200 px-1.5 py-0.5 text-[10px] text-slate-500 hover:border-red-300 hover:text-red-600 disabled:opacity-30"
                >
                  ✕
                </button>
              </span>
            </li>
          );
        })}
      </ul>
      <div className="border-t border-slate-200 p-3">
        <p className="mono mb-2 text-[10px] uppercase tracking-[0.18em] text-slate-500">
          Añadir bloque
        </p>
        <div className="grid max-h-44 grid-cols-2 gap-1 overflow-y-auto">
          {BLOCK_DEFS.map((def) => (
            <button
              key={def.type}
              type="button"
              onClick={() => onAdd(def.type)}
              title={`${def.hint} · ${def.type}`}
              className="border border-slate-200 px-2 py-1.5 text-left text-[11px] text-slate-700 hover:border-slate-400 hover:bg-slate-50"
            >
              {def.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
