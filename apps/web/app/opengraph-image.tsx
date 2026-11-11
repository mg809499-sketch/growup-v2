import { ImageResponse } from "next/og";

export const alt = "growup — la tiendita completa para ropa y joyería";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          background: "#0d0d0d",
          color: "#f4f3ee",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ fontSize: 20, letterSpacing: 4, textTransform: "uppercase", color: "#8c887b" }}>
          [ growup · ropa &amp; joyería ]
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ fontSize: 96, lineHeight: 0.95, fontWeight: 900, textTransform: "uppercase" }}>
            La tiendita completa
          </div>
          <div style={{ fontSize: 28, color: "#8c887b" }}>
            Storefront · Builder · Wompi · DIAN — Colombia
          </div>
        </div>
        <div style={{ fontSize: 18, color: "#8c887b" }}>growup.com · Q1 2027</div>
      </div>
    ),
    size,
  );
}
