import type { MetadataRoute } from "next";

import { services } from "@/content/services";
import { site } from "@/content/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const staticRoutes: MetadataRoute.Sitemap = [
    "",
    "/planes",
    "/servicios",
    "/consola",
    "/solicitar-acceso",
  ].map((path) => ({
    url: `${site.url}${path}`,
    lastModified: now,
  }));

  const serviceRoutes: MetadataRoute.Sitemap = services.map((service) => ({
    url: `${site.url}/servicios/${service.slug}`,
    lastModified: now,
  }));

  return [...staticRoutes, ...serviceRoutes];
}
