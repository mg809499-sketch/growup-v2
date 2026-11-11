"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createClient, isSupabaseConfigured } from "@/lib/supabase/server";
import { ApiError, apiSend } from "@/lib/api";

async function getOrigin(): Promise<string> {
  const requestHeaders = await headers();
  const host =
    requestHeaders.get("x-forwarded-host") ??
    requestHeaders.get("host") ??
    "localhost:3001";
  const protocol = requestHeaders.get("x-forwarded-proto") ?? "http";
  return `${protocol}://${host}`;
}

export async function login(formData: FormData) {
  if (!isSupabaseConfigured()) {
    redirect("/login?error=config");
  }

  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    redirect("/login?error=missing&tab=iniciar");
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    redirect("/login?error=invalid&tab=iniciar");
  }

  redirect("/");
}

export async function loginWithGoogle() {
  if (!isSupabaseConfigured()) {
    redirect("/login?error=config");
  }

  const origin = await getOrigin();
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: `${origin}/auth/callback`,
    },
  });

  if (error || !data.url) {
    redirect("/login?error=oauth&tab=crear");
  }

  redirect(data.url);
}

export async function completeSignup(formData: FormData) {
  if (!isSupabaseConfigured()) {
    redirect("/login?error=config&tab=crear");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!user || !session) {
    redirect("/login?error=session&tab=crear");
  }

  const domainChoice = String(formData.get("domain_choice") ?? "subdomain");
  const wantsSubdomain =
    domainChoice === "subdomain" && formData.get("wants_subdomain") === "on";

  const payload = {
    full_name: String(formData.get("full_name") ?? "").trim(),
    phone: String(formData.get("phone") ?? "").trim(),
    doc_type: String(formData.get("doc_type") ?? ""),
    doc_number: String(formData.get("doc_number") ?? "").trim(),
    store_name: String(formData.get("store_name") ?? "").trim(),
    store_type: String(formData.get("store_type") ?? ""),
    plan_code: String(formData.get("plan_code") ?? "starter"),
    slug: String(formData.get("slug") ?? "").trim().toLowerCase(),
    domain_choice: domainChoice,
    custom_domain:
      domainChoice === "custom"
        ? String(formData.get("custom_domain") ?? "").trim().toLowerCase() || null
        : null,
    wants_subdomain: wantsSubdomain,
  };

  if (
    !payload.full_name ||
    !payload.phone ||
    !payload.doc_type ||
    !payload.doc_number ||
    !payload.store_name ||
    !payload.store_type ||
    !payload.slug
  ) {
    redirect("/login?error=missing&tab=crear");
  }

  try {
    await apiSend("POST", "/v1/onboarding/complete", session.access_token, payload);
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.code === "SIGNUP_ALREADY_COMPLETED") {
        // El alta ya existe: refrescar sesión y entrar directo.
        await supabase.auth.refreshSession();
        redirect("/");
      }
      if (error.code === "SLUG_TAKEN") {
        redirect("/login?error=slug&tab=crear");
      }
      if (error.code === "DOMAIN_TAKEN") {
        redirect("/login?error=domain&tab=crear");
      }
      if (error.code === "PLAN_NOT_FOUND") {
        redirect("/login?error=plan&tab=crear");
      }
    }
    redirect("/login?error=signup&tab=crear");
  }

  // El alta creó membership + app_metadata; el token actual aún no los tiene.
  await supabase.auth.refreshSession();
  redirect("/");
}

export async function logout() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect("/login");
}
