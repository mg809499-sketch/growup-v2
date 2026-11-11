import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "growup",
    short_name: "growup",
    description:
      "La tiendita completa para marcas de ropa y joyería: storefront, builder, catálogo, inventario, pagos Wompi y facturación DIAN.",
    start_url: "/",
    display: "standalone",
    background_color: "#f4f3ee",
    theme_color: "#f4f3ee",
    icons: [],
  };
}
