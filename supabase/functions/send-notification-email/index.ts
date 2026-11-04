// send-notification-email: emails one portal notification to its recipient through Resend.
// Called by the database (trigger on public.notifications) with { id, token }.
// Secrets: RESEND_API_KEY (required to send), EMAIL_FROM (e.g. "Twelfth Space <portal@twelfthspace.com>"),
// PORTAL_URL (already set). Deploy with verify_jwt = false: the id + token pair is the check.
import { createClient } from "npm:@supabase/supabase-js@2.49.4";

const URL = Deno.env.get("SUPABASE_URL")!;
const SECRET = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}")["default"];
const RESEND = Deno.env.get("RESEND_API_KEY") ?? "";
const FROM = Deno.env.get("EMAIL_FROM") ?? "Twelfth Space <onboarding@resend.dev>";
const PORTAL = (Deno.env.get("PORTAL_URL") ?? "https://twelfthspace.github.io/portal/").replace(/\/?$/, "/");
const UUID = /^[0-9a-f-]{36}$/i;

const db = createClient(URL, SECRET, { auth: { persistSession: false, autoRefreshToken: false } });
const json = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json" } });
const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));

function emailHtml(name: string, text: string, link: string) {
  return `<!doctype html><html><body style="margin:0;background:#F3F3E7;font-family:Inter,Segoe UI,Arial,sans-serif;color:#24282C">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F3E7;padding:28px 12px"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border-radius:20px;overflow:hidden;border:1px solid rgba(62,70,49,.13)">
<tr><td style="background:#24282C;padding:20px 28px;color:#FAFF7E;font-weight:700;font-size:16px;letter-spacing:.2px">Twelfth Space Portal</td></tr>
<tr><td style="padding:28px">
<p style="margin:0 0 6px;font-size:14px;color:#6a7360">Hi ${esc(name || "there")},</p>
<p style="margin:0 0 22px;font-size:18px;line-height:1.45;font-weight:600">${esc(text)}</p>
<a href="${esc(link)}" style="display:inline-block;background:#3E4631;color:#ffffff;text-decoration:none;padding:12px 20px;border-radius:999px;font-weight:600;font-size:14px">Open the portal</a>
<p style="margin:26px 0 0;font-size:12px;color:#6a7360;line-height:1.5">You get this email because notifications are on in your portal profile. You can turn them off under Profile, Notifications.</p>
</td></tr></table></td></tr></table></body></html>`;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "Use POST." }, 405);
  let body: { id?: string; token?: string };
  try { body = await req.json(); } catch { return json({ error: "Bad body." }, 400); }
  const id = String(body.id ?? ""), token = String(body.token ?? "");
  if (!UUID.test(id) || !UUID.test(token)) return json({ error: "Bad request." }, 400);
  if (!RESEND) return json({ skipped: "RESEND_API_KEY is not set yet" });

  // Claim the notification so it is emailed at most once.
  const { data: note } = await db.from("notifications")
    .update({ emailed_at: new Date().toISOString() })
    .eq("id", id).eq("email_token", token).is("emailed_at", null)
    .select("id,user_id,text,link").maybeSingle();
  if (!note) return json({ skipped: "not found or already emailed" });

  const { data: who } = await db.from("profiles")
    .select("email,full_name,status,notify_email").eq("id", note.user_id).maybeSingle();
  if (!who || who.status !== "active" || !who.notify_email || !who.email || who.email.endsWith(".invalid")) {
    return json({ skipped: "recipient not emailable" });
  }

  const link = PORTAL + (note.link ? "#" + note.link : "");
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${RESEND}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      from: FROM, to: [who.email], subject: note.text.length > 90 ? note.text.slice(0, 87) + "…" : note.text,
      html: emailHtml(who.full_name ?? "", note.text, link),
      text: `${note.text}\n\nOpen the portal: ${link}\n\nTurn these emails off under Profile, Notifications.`,
    }),
  });
  if (!res.ok) {
    const detail = await res.text();
    console.error("resend failed", res.status, detail);
    await db.from("notifications").update({ emailed_at: null }).eq("id", id); // allow a later retry
    return json({ error: "email provider refused", status: res.status }, 502);
  }
  return json({ sent: true });
});
