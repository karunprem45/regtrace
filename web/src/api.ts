import type { Comparison, Device, PredicateLink } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const listDevices = (productCode: string) =>
  call<Device[]>(`/devices?product_code=${encodeURIComponent(productCode)}`);

export const listPredicates = (k: string) =>
  call<PredicateLink[]>(`/devices/${encodeURIComponent(k)}/predicates`);

export const compare = (subject_description: string, predicate_k: string) =>
  call<Comparison>("/compare", {
    method: "POST",
    body: JSON.stringify({ subject_description, predicate_k }),
  });
