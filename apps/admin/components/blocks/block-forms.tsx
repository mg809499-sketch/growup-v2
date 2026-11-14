"use client";

import {
  BLOCK_DEF_MAP,
  isValidVideoUrl,
  list,
  num,
  obj,
  readImage,
  readLink,
  str,
  type Block,
} from "@/lib/builder-blocks";
import {
  Checkbox,
  Field,
  ImageInput,
  LinkInput,
  NumberInput,
  RemoveRowButton,
  Select,
  TextArea,
  TextInput,
} from "./inputs";

export type BlockFormProps = {
  value: Block;
  onChange: (patch: Record<string, unknown>) => void;
};

// ---------- header ----------
function HeaderForm({ value, onChange }: BlockFormProps) {
  const nav = list(value.nav).map(obj);
  const links = nav.map((item) => ({
    label: str(item.label),
    href: str(item.href),
  }));
  const updateLinks = (next: Array<{ label: string; href: string }>) =>
    onChange({ nav: next });
  return (
    <div className="space-y-4">
      <Field label="Marca">
        <TextInput value={str(value.brand)} maxLength={60} onChange={(brand) => onChange({ brand })} />
      </Field>
      <Field label={`Navegación (${links.length} / 6)`}>
        <div className="space-y-2">
          {links.map((item, index) => (
            <div key={index} className="flex items-center gap-2">
              <input
                type="text"
                value={item.label}
                placeholder="Texto"
                maxLength={60}
                aria-label={`Texto del enlace ${index + 1}`}
                onChange={(event) =>
                  updateLinks(links.map((l, i) => (i === index ? { ...l, label: event.target.value } : l)))
                }
                className="w-1/3 border border-slate-200 px-2 py-1.5 text-xs"
              />
              <input
                type="text"
                value={item.href}
                placeholder="/ruta"
                maxLength={2048}
                aria-label={`Destino del enlace ${index + 1}`}
                onChange={(event) =>
                  updateLinks(links.map((l, i) => (i === index ? { ...l, href: event.target.value } : l)))
                }
                className="flex-1 border border-slate-200 px-2 py-1.5 font-mono text-[11px]"
              />
              <RemoveRowButton
                label="Quitar enlace"
                onClick={() => updateLinks(links.filter((_, i) => i !== index))}
              />
            </div>
          ))}
          {links.length < 6 ? (
            <button
              type="button"
              onClick={() => updateLinks([...links, { label: "", href: "/" }])}
              className="text-xs font-medium text-slate-700 underline underline-offset-2"
            >
              + Añadir enlace
            </button>
          ) : null}
        </div>
      </Field>
      <LinkInput
        label="Mostrar botón (CTA)"
        value={readLink(value.cta)}
        onChange={(cta) => onChange({ cta })}
      />
    </div>
  );
}

// ---------- footer ----------
function FooterForm({ value, onChange }: BlockFormProps) {
  const columns = list(value.columns).map(obj);
  const updateColumns = (next: Array<{ title: string; links: Array<{ label: string; href: string }> }>) =>
    onChange({ columns: next });
  const cols = columns.map((col) => ({
    title: str(col.title),
    links: list(col.links).map(obj).map((link) => ({ label: str(link.label), href: str(link.href) })),
  }));
  return (
    <div className="space-y-4">
      <Field label={`Columnas (${cols.length} / 4)`}>
        <div className="space-y-3">
          {cols.map((col, index) => (
            <div key={index} className="space-y-2 border border-slate-200 p-3">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={col.title}
                  placeholder="Título de columna"
                  maxLength={60}
                  aria-label={`Título de columna ${index + 1}`}
                  onChange={(event) =>
                    updateColumns(cols.map((c, i) => (i === index ? { ...c, title: event.target.value } : c)))
                  }
                  className="flex-1 border border-slate-200 px-2 py-1.5 text-xs"
                />
                <RemoveRowButton
                  label="Quitar columna"
                  onClick={() => updateColumns(cols.filter((_, i) => i !== index))}
                />
              </div>
              {col.links.map((link, linkIndex) => (
                <div key={linkIndex} className="flex items-center gap-2 pl-3">
                  <input
                    type="text"
                    value={link.label}
                    placeholder="Texto"
                    maxLength={60}
                    aria-label={`Texto del enlace ${linkIndex + 1}`}
                    onChange={(event) =>
                      updateColumns(
                        cols.map((c, i) =>
                          i === index
                            ? {
                                ...c,
                                links: c.links.map((l, j) =>
                                  j === linkIndex ? { ...l, label: event.target.value } : l,
                                ),
                              }
                            : c,
                        ),
                      )
                    }
                    className="w-1/3 border border-slate-200 px-2 py-1 text-[11px]"
                  />
                  <input
                    type="text"
                    value={link.href}
                    placeholder="/ruta"
                    maxLength={2048}
                    aria-label={`Destino del enlace ${linkIndex + 1}`}
                    onChange={(event) =>
                      updateColumns(
                        cols.map((c, i) =>
                          i === index
                            ? {
                                ...c,
                                links: c.links.map((l, j) =>
                                  j === linkIndex ? { ...l, href: event.target.value } : l,
                                ),
                              }
                            : c,
                        ),
                      )
                    }
                    className="flex-1 border border-slate-200 px-2 py-1 font-mono text-[10px]"
                  />
                  <RemoveRowButton
                    label="Quitar enlace"
                    onClick={() =>
                      updateColumns(
                        cols.map((c, i) =>
                          i === index
                            ? { ...c, links: c.links.filter((_, j) => j !== linkIndex) }
                            : c,
                        ),
                      )
                    }
                  />
                </div>
              ))}
              {col.links.length < 8 ? (
                <button
                  type="button"
                  onClick={() =>
                    updateColumns(
                      cols.map((c, i) =>
                        i === index ? { ...c, links: [...c.links, { label: "", href: "/" }] } : c,
                      ),
                    )
                  }
                  className="pl-3 text-[11px] font-medium text-slate-600 underline underline-offset-2"
                >
                  + Añadir enlace
                </button>
              ) : null}
            </div>
          ))}
          {cols.length < 4 ? (
            <button
              type="button"
              onClick={() =>
                updateColumns([...cols, { title: "Nueva columna", links: [{ label: "", href: "/" }] }])
              }
              className="text-xs font-medium text-slate-700 underline underline-offset-2"
            >
              + Añadir columna
            </button>
          ) : null}
        </div>
      </Field>
      <Field label="Línea legal">
        <TextInput value={str(value.legal_line)} maxLength={300} onChange={(legal_line) => onChange({ legal_line })} />
      </Field>
    </div>
  );
}

// ---------- hero ----------
function HeroForm({ value, onChange }: BlockFormProps) {
  return (
    <div className="space-y-4">
      <Field label="Eyebrow">
        <TextInput value={str(value.eyebrow)} maxLength={60} onChange={(eyebrow) => onChange({ eyebrow })} />
      </Field>
      <Field label="Título *">
        <TextInput value={str(value.title)} maxLength={120} onChange={(title) => onChange({ title })} />
      </Field>
      <Field label="Subtítulo">
        <TextInput value={str(value.subtitle)} maxLength={300} onChange={(subtitle) => onChange({ subtitle })} />
      </Field>
      <ImageInput
        value={readImage(value.image)}
        onChange={(image) => onChange({ image })}
      />
      <LinkInput
        label="Mostrar botón (CTA)"
        value={readLink(value.cta)}
        onChange={(cta) => onChange({ cta })}
      />
      <Field label="Alineación">
        <Select
          value={str(value.align, "left")}
          onChange={(align) => onChange({ align })}
          options={[
            { value: "left", label: "Izquierda" },
            { value: "center", label: "Centrada" },
          ]}
        />
      </Field>
    </div>
  );
}

// ---------- editorial_split ----------
function EditorialSplitForm({ value, onChange }: BlockFormProps) {
  return (
    <div className="space-y-4">
      <Field label="Kicker">
        <TextInput value={str(value.kicker)} maxLength={60} onChange={(kicker) => onChange({ kicker })} />
      </Field>
      <Field label="Título *">
        <TextInput value={str(value.title)} maxLength={120} onChange={(title) => onChange({ title })} />
      </Field>
      <Field label="Cuerpo * (sin HTML)">
        <TextArea
          value={str(value.body)}
          maxLength={2000}
          rows={6}
          onChange={(body) => onChange({ body })}
        />
      </Field>
      <ImageInput
        value={readImage(value.image)}
        required
        onChange={(image) => onChange({ image })}
      />
      <Field label="Lado de la imagen">
        <Select
          value={str(value.image_side, "left")}
          onChange={(image_side) => onChange({ image_side })}
          options={[
            { value: "left", label: "Izquierda" },
            { value: "right", label: "Derecha" },
          ]}
        />
      </Field>
      <LinkInput
        label="Mostrar botón (CTA)"
        value={readLink(value.cta)}
        onChange={(cta) => onChange({ cta })}
      />
    </div>
  );
}

// ---------- product_grid / product_carousel ----------
function ProductGridForm({ value, onChange }: BlockFormProps) {
  const isCarousel = value.type === "product_carousel";
  const maxLimit = isCarousel ? 12 : 24;
  const source = str(value.source, "latest");
  return (
    <div className="space-y-4">
      <Field label="Título">
        <TextInput value={str(value.title)} maxLength={80} onChange={(title) => onChange({ title })} />
      </Field>
      <Field label="Origen">
        <Select
          value={["latest", "category"].includes(source) ? source : "latest"}
          onChange={(s) => onChange({ source: s })}
          options={[
            { value: "latest", label: "Más recientes" },
            { value: "category", label: "Categoría específica" },
          ]}
        />
      </Field>
      {source === "category" ? (
        <Field label="Slug de categoría" hint="ej.: abrigos-invierno">
          <TextInput
            value={str(value.category_slug)}
            maxLength={63}
            mono
            onChange={(category_slug) => onChange({ category_slug })}
          />
        </Field>
      ) : null}
      <Field label={`Límite (1–${maxLimit})`}>
        <NumberInput
          value={num(value.limit, 8)}
          min={1}
          max={maxLimit}
          onChange={(limit) => onChange({ limit: Math.max(1, Math.min(maxLimit, Math.round(limit) || 1)) })}
        />
      </Field>
      {!isCarousel ? (
        <Checkbox
          label="Mostrar precio"
          checked={value.show_price !== false}
          onChange={(show_price) => onChange({ show_price })}
        />
      ) : null}
    </div>
  );
}

// ---------- collection_grid ----------
function CollectionGridForm({ value, onChange }: BlockFormProps) {
  const items = list(value.items).map(obj).map((item) => ({
    title: str(item.title),
    href: str(item.href),
    image: readImage(item.image),
  }));
  const updateItems = (next: typeof items) => onChange({ items: next });
  return (
    <div className="space-y-4">
      <Field label="Título">
        <TextInput value={str(value.title)} maxLength={80} onChange={(title) => onChange({ title })} />
      </Field>
      <Field label={`Colecciones (${items.length} / 12)`}>
        <div className="space-y-3">
          {items.map((item, index) => (
            <div key={index} className="space-y-2 border border-slate-200 p-3">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={item.title}
                  placeholder="Nombre"
                  maxLength={80}
                  aria-label={`Título de la colección ${index + 1}`}
                  onChange={(event) =>
                    updateItems(items.map((t, i) => (i === index ? { ...t, title: event.target.value } : t)))
                  }
                  className="flex-1 border border-slate-200 px-2 py-1.5 text-xs"
                />
                <RemoveRowButton
                  label="Quitar colección"
                  onClick={() => updateItems(items.filter((_, i) => i !== index))}
                />
              </div>
              <input
                type="text"
                value={item.href}
                placeholder="/collection/slug"
                maxLength={2048}
                aria-label={`Destino de la colección ${index + 1}`}
                onChange={(event) =>
                  updateItems(items.map((t, i) => (i === index ? { ...t, href: event.target.value } : t)))
                }
                className="w-full border border-slate-200 px-2 py-1.5 font-mono text-[11px]"
              />
              <ImageInput
                value={item.image}
                onChange={(image) =>
                  updateItems(items.map((t, i) => (i === index ? { ...t, image } : t)))
                }
              />
            </div>
          ))}
          {items.length < 12 ? (
            <button
              type="button"
              onClick={() => updateItems([...items, { title: "", href: "/collection", image: null }])}
              className="text-xs font-medium text-slate-700 underline underline-offset-2"
            >
              + Añadir colección
            </button>
          ) : null}
        </div>
      </Field>
    </div>
  );
}

// ---------- image_banner ----------
function ImageBannerForm({ value, onChange }: BlockFormProps) {
  return (
    <div className="space-y-4">
      <ImageInput
        value={readImage(value.image)}
        required
        onChange={(image) => onChange({ image })}
      />
      <Field label="Título">
        <TextInput value={str(value.title)} maxLength={80} onChange={(title) => onChange({ title })} />
      </Field>
      <Field label="Etiqueta del botón">
        <TextInput value={str(value.button_label)} maxLength={40} onChange={(button_label) => onChange({ button_label })} />
      </Field>
      <Field label="Enlace (vacío = sin botón)">
        <TextInput value={str(value.href)} maxLength={2048} mono onChange={(href) => onChange({ href })} />
      </Field>
      <Field label="Proporción">
        <Select
          value={str(value.ratio, "21:9")}
          onChange={(ratio) => onChange({ ratio })}
          options={[
            { value: "21:9", label: "21:9 (ancho)" },
            { value: "16:9", label: "16:9" },
            { value: "4:3", label: "4:3" },
          ]}
        />
      </Field>
    </div>
  );
}

// ---------- rich_text ----------
function RichTextForm({ value, onChange }: BlockFormProps) {
  return (
    <div className="space-y-4">
      <Field label="Markdown (sin HTML)" hint="**negrita**, *cursiva*, listas con -, enlaces [texto](url)">
        <TextArea
          value={str(value.markdown)}
          maxLength={10000}
          rows={12}
          onChange={(markdown) => onChange({ markdown })}
        />
      </Field>
      <Field label="Ancho">
        <Select
          value={str(value.width, "narrow")}
          onChange={(width) => onChange({ width })}
          options={[
            { value: "narrow", label: "Estrecho (artículo)" },
            { value: "wide", label: "Ancho" },
          ]}
        />
      </Field>
    </div>
  );
}

// ---------- quote ----------
function QuoteForm({ value, onChange }: BlockFormProps) {
  return (
    <div className="space-y-4">
      <Field label="Cita *">
        <TextArea value={str(value.text)} maxLength={500} rows={4} onChange={(text) => onChange({ text })} />
      </Field>
      <Field label="Autor">
        <TextInput value={str(value.author)} maxLength={120} onChange={(author) => onChange({ author })} />
      </Field>
    </div>
  );
}

// ---------- gallery ----------
function GalleryForm({ value, onChange }: BlockFormProps) {
  const images = list(value.images).map((item) => readImage(item) ?? { url: "", alt: "" });
  const updateImages = (next: Array<{ url: string; alt: string }>) => onChange({ images: next });
  return (
    <div className="space-y-4">
      <Field label="Columnas">
        <Select
          value={String(num(value.columns, 3))}
          onChange={(columns) => onChange({ columns: Number(columns) })}
          options={[
            { value: "2", label: "2 columnas" },
            { value: "3", label: "3 columnas" },
            { value: "4", label: "4 columnas" },
          ]}
        />
      </Field>
      <Field label={`Imágenes (${images.length} / 12)`}>
        <div className="space-y-3">
          {images.map((image, index) => (
            <div key={index} className="relative">
              <ImageInput
                value={image}
                required
                onChange={(next) =>
                  updateImages(images.map((img, i) => (i === index ? (next ?? img) : img)))
                }
              />
              <button
                type="button"
                onClick={() => updateImages(images.filter((_, i) => i !== index))}
                className="absolute right-2 top-2 border border-slate-200 bg-white px-2 py-0.5 text-xs text-slate-500 hover:text-red-600"
              >
                Quitar
              </button>
            </div>
          ))}
          {images.length < 12 ? (
            <button
              type="button"
              onClick={() => updateImages([...images, { url: "", alt: "" }])}
              className="text-xs font-medium text-slate-700 underline underline-offset-2"
            >
              + Añadir imagen
            </button>
          ) : null}
        </div>
      </Field>
    </div>
  );
}

// ---------- video_embed ----------
function VideoEmbedForm({ value, onChange }: BlockFormProps) {
  const url = str(value.url);
  const invalid = url !== "" && !isValidVideoUrl(url);
  return (
    <div className="space-y-4">
      <Field label="URL (YouTube o Vimeo)" hint="https://www.youtube.com/watch?v=… o https://player.vimeo.com/video/…">
        <TextInput value={url} maxLength={600} mono onChange={(next) => onChange({ url: next })} />
        {invalid ? (
          <span className="mt-1 block text-[11px] text-red-600">
            URL no reconocida: solo YouTube y Vimeo (allowlist del servidor).
          </span>
        ) : null}
      </Field>
      <Field label="Título accesible">
        <TextInput value={str(value.title)} maxLength={120} onChange={(title) => onChange({ title })} />
      </Field>
    </div>
  );
}

// ---------- faq ----------
function FaqForm({ value, onChange }: BlockFormProps) {
  const items = list(value.items).map(obj).map((item) => ({
    question: str(item.question),
    answer: str(item.answer),
  }));
  const updateItems = (next: typeof items) => onChange({ items: next });
  return (
    <div className="space-y-4">
      <Field label="Título">
        <TextInput value={str(value.title)} maxLength={120} onChange={(title) => onChange({ title })} />
      </Field>
      <Field label={`Preguntas (${items.length} / 12)`}>
        <div className="space-y-2">
          {items.map((item, index) => (
            <div key={index} className="space-y-2 border border-slate-200 p-3">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={item.question}
                  placeholder="Pregunta"
                  maxLength={200}
                  aria-label={`Pregunta ${index + 1}`}
                  onChange={(event) =>
                    updateItems(items.map((t, i) => (i === index ? { ...t, question: event.target.value } : t)))
                  }
                  className="flex-1 border border-slate-200 px-2 py-1.5 text-xs"
                />
                <RemoveRowButton
                  label="Quitar pregunta"
                  onClick={() => updateItems(items.filter((_, i) => i !== index))}
                />
              </div>
              <TextArea
                value={item.answer}
                maxLength={2000}
                rows={3}
                placeholder="Respuesta"
                onChange={(answer) => updateItems(items.map((t, i) => (i === index ? { ...t, answer } : t)))}
              />
            </div>
          ))}
          {items.length < 12 ? (
            <button
              type="button"
              onClick={() => updateItems([...items, { question: "", answer: "" }])}
              className="text-xs font-medium text-slate-700 underline underline-offset-2"
            >
              + Añadir pregunta
            </button>
          ) : null}
        </div>
      </Field>
    </div>
  );
}

// ---------- newsletter ----------
function NewsletterForm({ value, onChange }: BlockFormProps) {
  return (
    <div className="space-y-4">
      <Field label="Título">
        <TextInput value={str(value.title, "Boletín")} maxLength={120} onChange={(title) => onChange({ title })} />
      </Field>
      <Field label="Subtítulo">
        <TextInput value={str(value.subtitle)} maxLength={300} onChange={(subtitle) => onChange({ subtitle })} />
      </Field>
      <Field label="Texto del botón">
        <TextInput value={str(value.cta_label, "Suscribirme")} maxLength={60} onChange={(cta_label) => onChange({ cta_label })} />
      </Field>
    </div>
  );
}

// ---------- spacer ----------
function SpacerForm({ value, onChange }: BlockFormProps) {
  return (
    <Field label="Altura">
      <Select
        value={str(value.height, "md")}
        onChange={(height) => onChange({ height })}
        options={[
          { value: "sm", label: "Pequeño" },
          { value: "md", label: "Mediano" },
          { value: "lg", label: "Grande" },
        ]}
      />
    </Field>
  );
}

// ---------- columns ----------
function ColumnsForm({
  value,
  onChange,
  nested = false,
}: BlockFormProps & { nested?: boolean }) {
  const slots = list(value.columns).map(obj).map((slot) => ({
    width: Math.max(1, Math.min(12, num(slot.width, 6))),
    blocks: list(slot.blocks) as Block[],
  }));
  const updateSlots = (next: Array<{ width: number; blocks: Block[] }>) =>
    onChange({ columns: next });
  const childTypes = Object.keys(BLOCK_DEF_MAP).filter((type) => type !== "columns");

  return (
    <div className="space-y-4">
      <Field label={`Columnas (${slots.length} / 4) · ancho total 12`}>
        <div className="space-y-3">
          {slots.map((slot, index) => (
            <div key={index} className="space-y-2 border border-slate-200 p-3">
              <div className="flex items-center justify-between gap-2">
                <label className="flex items-center gap-2 text-xs text-slate-600">
                  Ancho
                  <input
                    type="number"
                    min={1}
                    max={12}
                    value={slot.width}
                    onChange={(event) =>
                      updateSlots(
                        slots.map((s, i) =>
                          i === index
                            ? { ...s, width: Math.max(1, Math.min(12, Number(event.target.value) || 1)) }
                            : s,
                        ),
                      )
                    }
                    className="w-16 border border-slate-200 px-2 py-1 text-xs"
                  />
                </label>
                <RemoveRowButton
                  label="Quitar columna"
                  onClick={() => updateSlots(slots.filter((_, i) => i !== index))}
                />
              </div>
              {slot.blocks.map((child, childIndex) => (
                <div key={childIndex} className="border border-slate-100 bg-slate-50 p-2">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="mono text-[10px] uppercase tracking-[0.14em] text-slate-500">
                      {BLOCK_DEF_MAP[child.type]?.label ?? child.type}
                    </span>
                    <RemoveRowButton
                      label="Quitar bloque"
                      onClick={() =>
                        updateSlots(
                          slots.map((s, i) =>
                            i === index
                              ? { ...s, blocks: s.blocks.filter((_, j) => j !== childIndex) }
                              : s,
                          ),
                        )
                      }
                    />
                  </div>
                  <BlockForm
                    value={child}
                    nested
                    onChange={(patch) =>
                      updateSlots(
                        slots.map((s, i) =>
                          i === index
                            ? {
                                ...s,
                                blocks: s.blocks.map((b, j) =>
                                  j === childIndex ? { ...b, ...patch } : b,
                                ),
                              }
                            : s,
                        ),
                      )
                    }
                  />
                </div>
              ))}
              {slot.blocks.length < 12 && !nested ? (
                <select
                  value=""
                  aria-label="Añadir sub-bloque"
                  onChange={(event) => {
                    const type = event.target.value;
                    if (!type) return;
                    updateSlots(
                      slots.map((s, i) =>
                        i === index
                          ? {
                              ...s,
                              blocks: [
                                ...s.blocks,
                                { id: `${type}-${Math.random().toString(36).slice(2, 8)}`, type, ...(BLOCK_DEF_MAP[type]?.defaults() ?? {}) },
                              ],
                            }
                          : s,
                      ),
                    );
                  }}
                  className="border border-slate-200 bg-white px-2 py-1 text-[11px] text-slate-600"
                >
                  <option value="">+ sub-bloque…</option>
                  {childTypes.map((type) => (
                    <option key={type} value={type}>
                      {BLOCK_DEF_MAP[type]?.label ?? type}
                    </option>
                  ))}
                </select>
              ) : null}
            </div>
          ))}
          {slots.length < 4 ? (
            <button
              type="button"
              onClick={() => updateSlots([...slots, { width: 6, blocks: [] }])}
              className="text-xs font-medium text-slate-700 underline underline-offset-2"
            >
              + Añadir columna
            </button>
          ) : null}
        </div>
      </Field>
      <p className="text-[11px] text-slate-500">
        Los anchos se normalizan sobre 12 columnas; el servidor valida el layout al publicar.
      </p>
    </div>
  );
}

// ---------- registry ----------
export function BlockForm(props: BlockFormProps & { nested?: boolean }) {
  switch (props.value.type) {
    case "header":
      return <HeaderForm {...props} />;
    case "footer":
      return <FooterForm {...props} />;
    case "hero":
      return <HeroForm {...props} />;
    case "editorial_split":
      return <EditorialSplitForm {...props} />;
    case "product_grid":
    case "product_carousel":
      return <ProductGridForm {...props} />;
    case "collection_grid":
      return <CollectionGridForm {...props} />;
    case "image_banner":
      return <ImageBannerForm {...props} />;
    case "rich_text":
      return <RichTextForm {...props} />;
    case "quote":
      return <QuoteForm {...props} />;
    case "gallery":
      return <GalleryForm {...props} />;
    case "video_embed":
      return <VideoEmbedForm {...props} />;
    case "faq":
      return <FaqForm {...props} />;
    case "newsletter":
      return <NewsletterForm {...props} />;
    case "spacer":
      return <SpacerForm {...props} />;
    case "columns":
      return <ColumnsForm {...props} />;
    default:
      return (
        <p className="border border-dashed border-slate-300 p-3 text-xs text-slate-500">
          Bloque desconocido “{String(props.value.type)}”. El editor no puede editarlo; elimínalo o recarga.
        </p>
      );
  }
}
