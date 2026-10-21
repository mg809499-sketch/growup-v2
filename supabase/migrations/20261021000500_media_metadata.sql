-- Metadatos de media: nombre original como metadata, nunca en la clave de R2.

alter table app.media_assets
    add column original_filename text;

alter table app.media_assets
    add constraint media_assets_original_filename_len
    check (original_filename is null or char_length(original_filename) <= 255);
