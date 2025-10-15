
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8050";
export async function api(path:string, opts: RequestInit = {}){
  const isFD = typeof FormData !== 'undefined' && opts.body instanceof FormData;
  const headers:any = { ...(opts.headers||{}) };
  if(!isFD) headers["Content-Type"]="application/json";
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}
