import Image from "next/image";
import Link from "next/link";

import { listProducts } from "@/lib/api";
import { getStorefrontHost } from "@/lib/api";
import { asImage, asLink, str } from "@/lib/blocks";
import type { Block } from "@/lib/blocks";
import { ProductCard } from "@/components/product-card";
import { EmptyState } from "@/components/empty-state";

type BlockProps = { block: Block };

function Section({ children }: { children: React.ReactNode }) {
  return <section className="mx-auto w-full max-w-6xl px-6 py-16 md:px-10">{children}</section>;
}

function BlockHeader({ kicker, title }: { kicker?: string; title?: string }) {
  if (!title && !kicker) return null;
  return (
    <div className="mb-8">
      {kicker ? <p className="label text-[var(--muted)]">{kicker}</p> : null}
      {title ? <h2 className="display mt-2 text-3xl md:text-4xl">{title}</h2> : null}
    </div>
  );
}

function CtaLink({ href, label }: { href: string; label: string }) {
  const external = href.startsWith("http");
  const className =
    "inline-flex items-center gap-2 border border-[var(--ink)] px-6 py-3 label transition-colors hover:bg-[var(--ink)] hover:text-[var(--surface)]";
  return external ? (
    <a className={className} href={href} rel="noopener noreferrer">
      {label}
    </a>
  ) : (
    <Link className={className} href={href}>
      {label}
    </Link>
  );
}

export function HeaderBlockView({ block }: BlockProps) {
  const nav = Array.isArray(block.nav) ? block.nav : [];
  const cta = asLink(block.cta);
  return (
    <header className="sticky top-0 z-40 border-b border-[var(--hairline)] bg-[var(--surface)]/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4 md:px-10">
        <Link href="/" className="display text-lg">
          {str(block.brand, "growup")}
        </Link>
        <nav className="hidden items-center gap-6 md:flex">
          {nav.map((item, index) =>
            item && typeof item === "object" && "href" in item ? (
              <Link
                key={`${index}-${String((item as { href: unknown }).href)}`}
                href={String((item as { href: unknown }).href)}
                className="label text-[var(--muted)] hover:text-[var(--ink)]"
              >
                {String((item as { label?: unknown }).label ?? "")}
              </Link>
            ) : null,
          )}
        </nav>
        {cta ? <CtaLink href={cta.href} label={cta.label} /> : null}
      </div>
    </header>
  );
}

export function FooterBlockView({ block }: BlockProps) {
  const columns = Array.isArray(block.columns) ? block.columns : [];
  return (
    <footer className="border-t border-[var(--hairline)]">
      <div className="mx-auto max-w-6xl px-6 py-12 md:px-10">
        <div className="grid gap-8 md:grid-cols-4">
          {columns.map((column, index) =>
            column && typeof column === "object" ? (
              <div key={index}>
                <p className="label text-[var(--muted)]">{str((column as Record<string, unknown>).title)}</p>
                <ul className="mt-3 space-y-2">
                  {(Array.isArray((column as Record<string, unknown>).links)
                    ? ((column as Record<string, unknown>).links as unknown[])
                    : []
                  ).map((link, linkIndex) =>
                    link && typeof link === "object" && "href" in link ? (
                      <li key={linkIndex}>
                        <Link
                          href={String((link as { href: unknown }).href)}
                          className="text-sm text-[var(--muted)] hover:text-[var(--ink)]"
                        >
                          {String((link as { label?: unknown }).label ?? "")}
                        </Link>
                      </li>
                    ) : null,
                  )}
                </ul>
              </div>
            ) : null,
          )}
        </div>
        {typeof block.legal_line === "string" && block.legal_line ? (
          <p className="label mt-10 text-[var(--muted)]">{block.legal_line}</p>
        ) : null}
      </div>
    </footer>
  );
}

export function HeroBlockView({ block }: BlockProps) {
  const image = asImage(block.image);
  const eyebrow = str(block.eyebrow);
  const subtitle = str(block.subtitle);
  const cta = asLink(block.cta);
  const centered = block.align === "center";

  return (
    <section className="relative overflow-hidden border-b border-[var(--hairline)]">
      {image ? (
        <Image
          src={image.url}
          alt={image.alt}
          fill
          priority
          sizes="100vw"
          className="object-cover"
        />
      ) : null}
      <div
        className={`relative mx-auto flex min-h-[70vh] max-w-6xl flex-col justify-end gap-6 px-6 pb-20 pt-40 md:px-10 ${
          image ? "text-[#faf9f4]" : ""
        } ${centered ? "items-center text-center" : "items-start"}`}
      >
        {eyebrow ? <p className="label opacity-80">{eyebrow}</p> : null}
        <h1 className="display max-w-4xl text-6xl leading-[0.95] md:text-8xl">{str(block.title)}</h1>
        {subtitle ? <p className="max-w-xl text-lg opacity-90">{subtitle}</p> : null}
        {cta ? <CtaLink href={cta.href} label={cta.label} /> : null}
      </div>
    </section>
  );
}

export function EditorialSplitBlockView({ block }: BlockProps) {
  const image = asImage(block.image);
  const kicker = str(block.kicker);
  const cta = asLink(block.cta);
  const imageLeft = block.image_side !== "right";

  return (
    <Section>
      <div className="grid items-center gap-10 md:grid-cols-2">
        <div className={imageLeft ? "" : "md:order-2"}>
          {image ? (
            <div className="relative aspect-[4/5] w-full overflow-hidden bg-[var(--surface-2)]">
              <Image src={image.url} alt={image.alt} fill sizes="(min-width: 768px) 50vw, 100vw" className="object-cover" />
            </div>
          ) : null}
        </div>
        <div>
          {kicker ? <BlockHeader kicker={kicker} /> : null}
          <h2 className="display text-4xl leading-[1.02] md:text-5xl">{str(block.title)}</h2>
          <p className="mt-6 whitespace-pre-line text-lg leading-relaxed text-[var(--muted)]">{str(block.body)}</p>
          {cta ? <div className="mt-8"><CtaLink href={cta.href} label={cta.label} /></div> : null}
        </div>
      </div>
    </Section>
  );
}

async function ProductGrid({ block, carousel }: { block: Block; carousel: boolean }) {
  const host = await getStorefrontHost();
  const source = block.source === "category" ? String(block.category_slug ?? "") : undefined;
  const limitRaw = typeof block.limit === "number" ? block.limit : 8;
  const limit = Math.min(Math.max(1, limitRaw), carousel ? 12 : 24);
  const products = await listProducts(host, limit, source || undefined);

  const showPrice = block.show_price !== false;
  const title = str(block.title);

  return (
    <Section>
      {title ? <BlockHeader title={title} /> : null}
      {products.items.length === 0 ? (
        <EmptyState title="Sin productos" description="Esta tienda aún no tiene productos publicados." />
      ) : (
        <div
          className={
            carousel
              ? "flex snap-x snap-mandatory gap-6 overflow-x-auto pb-4 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
              : "grid grid-cols-2 gap-6 md:grid-cols-4"
          }
        >
          {products.items.map((product, index) => (
            <div key={product.id} className={carousel ? "w-[240px] shrink-0 snap-start" : undefined}>
              {showPrice ? (
                <ProductCard product={product} index={index} />
              ) : (
                <ProductCard product={product} index={index} />
              )}
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

export function ProductGridBlockView({ block }: BlockProps) {
  return <ProductGrid block={block} carousel={false} />;
}

export function ProductCarouselBlockView({ block }: BlockProps) {
  return <ProductGrid block={block} carousel />;
}

export function CollectionGridBlockView({ block }: BlockProps) {
  const title = str(block.title);
  const items = Array.isArray(block.items) ? block.items : [];
  return (
    <Section>
      {title ? <BlockHeader title={title} /> : null}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {items.map((item, index) => {
          if (!item || typeof item !== "object") return null;
          const record = item as Record<string, unknown>;
          const image = asImage(record.image);
          return (
            <Link
              key={index}
              href={str(record.href, "/collection")}
              className="group relative aspect-[3/4] overflow-hidden bg-[var(--surface-2)]"
            >
              {image ? (
                <Image
                  src={image.url}
                  alt={image.alt}
                  fill
                  sizes="(min-width: 768px) 25vw, 50vw"
                  className="object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                />
              ) : null}
              <span className="label absolute bottom-3 left-3 bg-[var(--surface)]/80 px-3 py-1 backdrop-blur">
                {str(record.title)}
              </span>
            </Link>
          );
        })}
      </div>
    </Section>
  );
}

export function ImageBannerBlockView({ block }: BlockProps) {
  const image = asImage(block.image);
  if (!image) return null;
  const href = str(block.href);
  const title = str(block.title);
  const button = str(block.button_label);
  const ratio =
    block.ratio === "16:9" ? "aspect-[16/9]" : block.ratio === "4:3" ? "aspect-[4/3]" : "aspect-[21/9]";

  const inner = (
    <div className={`relative w-full overflow-hidden bg-[var(--surface-2)] ${ratio}`}>
      <Image src={image.url} alt={image.alt} fill sizes="100vw" className="object-cover" />
      {title || button ? (
        <div className="absolute inset-0 flex flex-col items-start justify-end gap-3 bg-gradient-to-t from-black/55 to-transparent p-6 text-[#faf9f4] md:p-10">
          {title ? <h2 className="display text-3xl md:text-5xl">{title}</h2> : null}
          {button ? <span className="label border border-white/60 px-4 py-2">{button}</span> : null}
        </div>
      ) : null}
    </div>
  );

  if (href) {
    const external = href.startsWith("http");
    return external ? (
      <a href={href} rel="noopener noreferrer">{inner}</a>
    ) : (
      <Link href={href}>{inner}</Link>
    );
  }
  return inner;
}

export function RichTextBlockView({ block }: BlockProps) {
  const width = block.width === "wide" ? "max-w-4xl" : "max-w-2xl";
  return (
    <Section>
      <div
        className={`mx-auto ${width} whitespace-pre-line text-lg leading-relaxed`}
      >
        {str(block.markdown)}
      </div>
    </Section>
  );
}

export function QuoteBlockView({ block }: BlockProps) {
  const author = str(block.author);
  return (
    <Section>
      <figure className="mx-auto max-w-3xl text-center">
        <blockquote className="display text-3xl leading-tight md:text-4xl">
          “{str(block.text)}”
        </blockquote>
        {author ? <figcaption className="label mt-6 text-[var(--muted)]">{author}</figcaption> : null}
      </figure>
    </Section>
  );
}

export function GalleryBlockView({ block }: BlockProps) {
  const images = Array.isArray(block.images) ? block.images : [];
  const columns = block.columns === 2 ? 2 : block.columns === 4 ? 4 : 3;
  const grid =
    columns === 2 ? "grid-cols-2" : columns === 4 ? "grid-cols-2 md:grid-cols-4" : "grid-cols-2 md:grid-cols-3";
  return (
    <Section>
      <div className={`grid gap-4 ${grid}`}>
        {images.map((item, index) => {
          const image = asImage(item);
          if (!image) return null;
          return (
            <div key={index} className="relative aspect-square overflow-hidden bg-[var(--surface-2)]">
              <Image src={image.url} alt={image.alt} fill sizes="(min-width: 768px) 33vw, 50vw" className="object-cover" />
            </div>
          );
        })}
      </div>
    </Section>
  );
}

export function VideoEmbedBlockView({ block }: BlockProps) {
  const url = str(block.url);
  if (!url) return null;
  const embed = toEmbedUrl(url);
  if (!embed) return null;
  return (
    <Section>
      <div className="relative aspect-video w-full overflow-hidden border border-[var(--hairline)] bg-black">
        <iframe
          src={embed}
          title={str(block.title, "Video")}
          loading="lazy"
          sandbox="allow-scripts allow-same-origin allow-presentation"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="absolute inset-0 h-full w-full"
        />
      </div>
    </Section>
  );
}

function toEmbedUrl(url: string): string | null {
  const youtube = url.match(/^https:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{6,})/);
  if (youtube) return `https://www.youtube.com/embed/${youtube[1]}`;
  const vimeo = url.match(/^https:\/\/(?:www\.)?player\.vimeo\.com\/video\/(\d+)/);
  if (vimeo) return `https://player.vimeo.com/video/${vimeo[1]}`;
  const vimeoPlain = url.match(/^https:\/\/(?:www\.)?vimeo\.com\/(\d+)/);
  if (vimeoPlain) return `https://player.vimeo.com/video/${vimeoPlain[1]}`;
  return null;
}

export function FaqBlockView({ block }: BlockProps) {
  const title = str(block.title);
  const items = Array.isArray(block.items) ? block.items : [];
  return (
    <Section>
      {title ? <BlockHeader title={title} /> : null}
      <div className="mx-auto max-w-3xl divide-y divide-[var(--hairline)] border border-[var(--hairline)]">
        {items.map((item, index) =>
          item && typeof item === "object" ? (
            <details key={index} className="group p-5">
              <summary className="flex cursor-pointer items-center justify-between gap-4 font-medium">
                {str((item as Record<string, unknown>).question)}
                <span aria-hidden className="text-[var(--muted)] transition-transform group-open:rotate-45">+</span>
              </summary>
              <div className="mt-3 whitespace-pre-line text-[var(--muted)]">
                {str((item as Record<string, unknown>).answer)}
              </div>
            </details>
          ) : null,
        )}
      </div>
    </Section>
  );
}

export function NewsletterBlockView({ block }: BlockProps) {
  const title = str(block.title, "Boletín");
  const subtitle = str(block.subtitle);
  const cta = str(block.cta_label, "Suscribirme");
  return (
    <Section>
      <div className="mx-auto max-w-xl border border-[var(--hairline)] p-8 text-center">
        <p className="label text-[var(--muted)]">boletín</p>
        <h2 className="display mt-2 text-3xl">{title}</h2>
        {subtitle ? <p className="mt-3 text-[var(--muted)]">{subtitle}</p> : null}
        <form className="mt-6 flex flex-col gap-3 sm:flex-row">
          <label htmlFor="newsletter-email" className="sr-only">Correo</label>
          <input
            id="newsletter-email"
            type="email"
            required
            placeholder="tu@email.com"
            className="w-full border border-[var(--hairline)] bg-[var(--surface-2)] px-4 py-3 outline-none focus-visible:border-[var(--ink)]"
          />
          <button type="submit" disabled className="label cursor-not-allowed border border-[var(--hairline)] px-6 py-3 text-[var(--muted)]">
            {cta}
          </button>
        </form>
        <p className="label mt-4 text-[var(--muted)]">disponible pronto</p>
      </div>
    </Section>
  );
}

export function SpacerBlockView({ block }: BlockProps) {
  const height = block.height === "sm" ? "h-6" : block.height === "lg" ? "h-24" : "h-12";
  return <div aria-hidden className={height} />;
}

export function ColumnsBlockView({ block }: BlockProps) {
  const columns = Array.isArray(block.columns) ? block.columns : [];
  const total = columns.reduce((acc, col) => {
    const width = col && typeof col === "object" ? Number((col as Record<string, unknown>).width) || 0 : 0;
    return acc + width;
  }, 0);
  return (
    <Section>
      <div className="grid gap-8 md:grid-cols-12">
        {columns.map((column, index) => {
          const record = (column ?? {}) as Record<string, unknown>;
          const width = Number(record.width) || 12;
          const span = Math.max(1, Math.min(12, Math.round((width / Math.max(total, 12)) * 12) || width));
          const children = Array.isArray(record.blocks) ? (record.blocks as Block[]) : [];
          return (
            <div key={index} className="" style={{ gridColumn: `span ${span} / span ${span}` }}>
              {children.map((child) => (
                <BlockRenderer key={child.id} block={child} />
              ))}
            </div>
          );
        })}
      </div>
    </Section>
  );
}

export function BlockRenderer({ block }: BlockProps) {
  switch (block.type) {
    case "header":
      return <HeaderBlockView block={block} />;
    case "footer":
      return <FooterBlockView block={block} />;
    case "hero":
      return <HeroBlockView block={block} />;
    case "editorial_split":
      return <EditorialSplitBlockView block={block} />;
    case "product_grid":
      return <ProductGridBlockView block={block} />;
    case "product_carousel":
      return <ProductCarouselBlockView block={block} />;
    case "collection_grid":
      return <CollectionGridBlockView block={block} />;
    case "image_banner":
      return <ImageBannerBlockView block={block} />;
    case "rich_text":
      return <RichTextBlockView block={block} />;
    case "quote":
      return <QuoteBlockView block={block} />;
    case "gallery":
      return <GalleryBlockView block={block} />;
    case "video_embed":
      return <VideoEmbedBlockView block={block} />;
    case "faq":
      return <FaqBlockView block={block} />;
    case "newsletter":
      return <NewsletterBlockView block={block} />;
    case "spacer":
      return <SpacerBlockView block={block} />;
    case "columns":
      return <ColumnsBlockView block={block} />;
    default:
      return null;
  }
}
