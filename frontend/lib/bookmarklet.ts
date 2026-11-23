import type { BookmarkletPayload } from "@/lib/api";

export function encodeBookmarkletPayload(payload: BookmarkletPayload): string {
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).split("+").join("-").split("/").join("_").replace(/=+$/, "");
}

export function decodeBookmarkletPayload(value: string): BookmarkletPayload | null {
  try {
    const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
    const binary = atob(padded);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    const parsed = JSON.parse(new TextDecoder().decode(bytes)) as Partial<BookmarkletPayload>;
    if (!parsed || typeof parsed.url !== "string") {
      return null;
    }
    return {
      url: parsed.url,
      title: parsed.title,
      company: parsed.company,
      location: parsed.location,
      salary_text: parsed.salary_text,
      og_site_name: parsed.og_site_name,
      jsonld: Array.isArray(parsed.jsonld) ? parsed.jsonld : [],
      text: typeof parsed.text === "string" ? parsed.text : "",
    };
  } catch {
    return null;
  }
}

export function buildBookmarklet(origin: string): string {
  const target = JSON.stringify(`${origin}/captura`);
  return `javascript:(()=>{try{
const scripts=[...document.querySelectorAll('script[type="application/ld+json"]')].map((node)=>node.textContent||'').filter(Boolean);
const meta=document.querySelector('meta[property="og:site_name"]');
const data={url:location.href,title:document.title||'',og_site_name:meta?meta.content:'',jsonld:scripts,text:(document.body?document.body.innerText:'').slice(0,20000)};
const bytes=new TextEncoder().encode(JSON.stringify(data));
let binary='';for(const byte of bytes)binary+=String.fromCharCode(byte);
const encoded=btoa(binary).split('+').join('-').split('/').join('_').replace(/=+$/,'');
window.open(${target}+'#'+encoded,'_blank','noopener');
}catch(error){alert('PractiCV: '+error);}})();`;
}
