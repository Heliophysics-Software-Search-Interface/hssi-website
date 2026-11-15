/**
 * Decodes the email links rendered by the `obfuscated_email` template tag
 * (`django/website/templatetags/obfuscated_email.py`), which keep the address
 * base64-encoded in `data-email` so it never appears as plain text in the
 * page source. On page load this sets each link's `mailto:` target, and shows
 * the address as the link text unless the link has `data-keep-text`.
 *
 * @module
 */

/** `"obfuscated-email"`: class of links holding an encoded address. */
export const classObfuscatedEmail = "obfuscated-email";

/** Decodes every obfuscated email link in the page. */
export function revealObfuscatedEmails(): void {
	const links = document.querySelectorAll<HTMLAnchorElement>(
		`a.${classObfuscatedEmail}[data-email]`
	);
	for (const link of links) {
		const email = atob(link.dataset.email);
		link.href = `mailto:${email}`;
		if (link.dataset.keepText === undefined) link.textContent = email;
	}
}

if (document.readyState === "loading") {
	document.addEventListener("DOMContentLoaded", revealObfuscatedEmails);
} else {
	revealObfuscatedEmails();
}
