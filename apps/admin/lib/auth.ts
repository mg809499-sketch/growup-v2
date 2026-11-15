import { redirect } from "next/navigation";

import { createClient, isSupabaseConfigured } from "@/lib/supabase/server";
import {
  designPreviewToken,
  designPreviewUser,
  isDesignPreview,
} from "@/lib/design-preview";

export async function requireSession() {
  if (isDesignPreview()) {
    return {
      user: {
        ...designPreviewUser,
        authMode: "design-preview" as const,
      },
      token: designPreviewToken,
      supabase: null as never,
    };
  }

  if (!isSupabaseConfigured()) {
    redirect("/login?error=config");
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  return { user, token: session.access_token, supabase };
}
