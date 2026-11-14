"use client";

import { useEffect, useState } from "react";

import { BlockRenderer } from "@/components/blocks";
import { parseLayoutBlocks, type Block } from "@/lib/blocks";

/**
 * Renderiza los bloques iniciales del borrador y acepta updates vía postMessage
 * desde el Host del builder admin (origen verificado).
 */
export function PreviewBlocks({
  initialBlocks,
  adminOrigin,
}: {
  initialBlocks: Block[];
  adminOrigin: string | null;
}) {
  const [blocks, setBlocks] = useState<Block[]>(initialBlocks);

  useEffect(() => {
    function onMessage(event: MessageEvent) {
      const expectedOrigin = adminOrigin
        ? new URL(adminOrigin).origin
        : window.location.origin;
      if (event.origin !== expectedOrigin) return;

      const data = event.data as { type?: string; blocks?: unknown } | null;
      if (!data || data.type !== "GROWUP_UPDATE_BLOCKS" || !Array.isArray(data.blocks)) {
        return;
      }
      setBlocks(parseLayoutBlocks({ blocks: data.blocks }));
    }

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [adminOrigin]);

  return (
    <>
      {blocks.map((block) => (
        <BlockRenderer key={block.id} block={block} />
      ))}
    </>
  );
}
