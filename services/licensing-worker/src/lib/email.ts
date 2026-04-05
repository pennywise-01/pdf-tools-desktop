import { Env } from "../types";

interface EmailSendPayload {
  to: string;
  licenseToken: string;
  orderId: string;
}

export async function sendLicenseEmailIfConfigured(
  env: Env,
  payload: EmailSendPayload,
): Promise<{ sent: boolean; reason?: string }> {
  if (!env.RESEND_API_KEY || !env.RESEND_FROM_EMAIL) {
    return { sent: false, reason: "resend_not_configured" };
  }

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
    },
    body: JSON.stringify({
      from: env.RESEND_FROM_EMAIL,
      to: [payload.to],
      subject: "Your PDF Tools Pro license key",
      text: [
        "Thanks for your purchase.",
        "",
        `Order ID: ${payload.orderId}`,
        "",
        "Paste this key into PDF Tools Desktop > Activate License:",
        payload.licenseToken,
        "",
        "Keep this key private.",
      ].join("\n"),
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    return { sent: false, reason: `resend_error:${response.status}:${errorText}` };
  }

  return { sent: true };
}
