// partner-admin: admin-only actions that need the Supabase secret key.
//   invite         { email, full_name, send_email? }  -> sends the invite email, or returns a one-time link
//   revoke_invite  { user_id }                         -> deletes an invited user who never signed in
//   suspend        { user_id, reason }                 -> marks the partner suspended and blocks sign-in
//   reactivate     { user_id, reason }                 -> reverses a suspension
//   remove         { user_id, reason }                 -> partner has left: closes the login, keeps money history
// The caller must be signed in as an active admin. Deploy with verify_jwt = false; auth is checked below.
import { createClient } from "npm:@supabase/supabase-js@2.49.4";

const URL = Deno.env.get("SUPABASE_URL")!;
const SECRET = JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}")["default"];
const PUBLISHABLE = JSON.parse(Deno.env.get("SUPABASE_PUBLISHABLE_KEYS") ?? "{}")["default"];
const PORTAL_URL = Deno.env.get("PORTAL_URL") ?? ""; // e.g. https://portal.twelfthspace.com
const ORIGIN = Deno.env.get("PORTAL_ORIGIN") ?? "*";

const cors = {
  "Access-Control-Allow-Origin": ORIGIN,
  "Access-Control-Allow-Headers": "authorization, content-type, apikey, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

const admin = createClient(URL, SECRET, { auth: { persistSession: false, autoRefreshToken: false } });
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const FOREVER = "876000h"; // about 100 years

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "Use POST." }, 405);

  // 1. who is calling?
  const token = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "");
  if (!token) return json({ error: "Sign in first." }, 401);
  const { data: who, error: whoErr } = await admin.auth.getUser(token);
  if (whoErr || !who?.user) return json({ error: "Your session has expired. Sign in again." }, 401);
  const { data: me } = await admin.from("profiles").select("role,status").eq("id", who.user.id).single();
  if (!me || me.role !== "admin" || me.status !== "active") return json({ error: "Only admins can do this." }, 403);

  // A client that acts as the admin, so database functions see auth.uid() and write the audit log.
  const asAdmin = createClient(URL, PUBLISHABLE, {
    auth: { persistSession: false, autoRefreshToken: false },
    global: { headers: { Authorization: `Bearer ${token}` } },
  });

  let body: Record<string, unknown>;
  try { body = await req.json(); } catch { return json({ error: "Send a JSON body." }, 400); }
  const action = String(body.action ?? "");

  try {
    if (action === "invite") {
      const email = String(body.email ?? "").trim().toLowerCase();
      const full_name = String(body.full_name ?? "").trim();
      if (!full_name) return json({ error: "Enter the partner's name." }, 400);
      if (!EMAIL.test(email)) return json({ error: "Enter a valid email address." }, 400);
      const { data: existing } = await admin.from("profiles").select("id").eq("email", email).maybeSingle();
      if (existing) return json({ error: "This email already has an account or a pending invitation." }, 409);

      // The page reads the invite tokens from the URL hash, so land on the bare site address.
      const redirectTo = PORTAL_URL ? PORTAL_URL.replace(/\/?$/, "/") : undefined;
      if (body.send_email === false) {
        const { data, error } = await admin.auth.admin.generateLink({
          type: "invite", email, options: { data: { full_name }, redirectTo },
        });
        if (error) throw error;
        return json({ user_id: data.user.id, link: data.properties.action_link });
      }
      const { data, error } = await admin.auth.admin.inviteUserByEmail(email, { data: { full_name }, redirectTo });
      if (error) throw error;
      return json({ user_id: data.user.id, sent: true });
    }

    if (action === "revoke_invite") {
      const id = String(body.user_id ?? "");
      const { data, error } = await admin.auth.admin.getUserById(id);
      if (error || !data?.user) return json({ error: "Invitation not found." }, 404);
      if (!data.user.invited_at || data.user.last_sign_in_at) {
        return json({ error: "This person has already accepted. Suspend them instead." }, 409);
      }
      const del = await admin.auth.admin.deleteUser(id);
      if (del.error) throw del.error;
      return json({ revoked: true });
    }

    if (action === "suspend" || action === "reactivate") {
      const id = String(body.user_id ?? "");
      const reason = String(body.reason ?? "");
      if (id === who.user.id) return json({ error: "You cannot suspend yourself." }, 400);
      const { error } = await asAdmin.rpc("set_partner_status", {
        p_partner: id, p_status: action === "suspend" ? "suspended" : "active", p_reason: reason,
      });
      if (error) return json({ error: error.message }, 400);
      const ban = await admin.auth.admin.updateUserById(id, { ban_duration: action === "suspend" ? FOREVER : "none" });
      if (ban.error) throw ban.error;
      return json({ ok: true });
    }

    if (action === "remove") {
      // For a partner who has left. Money history stays; the login and personal details go.
      const id = String(body.user_id ?? "");
      const reason = String(body.reason ?? "");
      if (id === who.user.id) return json({ error: "You cannot remove yourself." }, 400);
      const { data: oldPhoto, error } = await asAdmin.rpc("remove_partner", { p_partner: id, p_reason: reason });
      if (error) return json({ error: error.message }, 400);
      // Free the email so the person could be invited again one day, and block the login for good.
      const ban = await admin.auth.admin.updateUserById(id, { ban_duration: FOREVER, user_metadata: {} });
      if (ban.error) throw ban.error;
      const freed = await admin.auth.admin.updateUserById(id, {
        email: `removed-${id}@removed.twelfthspace.invalid`, email_confirm: true,
      });
      if (freed.error) console.error("could not free email", freed.error);
      if (oldPhoto) await admin.storage.from("avatars").remove([String(oldPhoto)]);
      return json({ removed: true, email_freed: !freed.error });
    }

    return json({ error: "Unknown action." }, 400);
  } catch (e) {
    console.error(action, e);
    return json({ error: e instanceof Error ? e.message : "Something went wrong." }, 500);
  }
});
