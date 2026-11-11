import { useState } from "react";
import { compare, listDevices, listPredicates } from "./api";
import type { Cell, Comparison, Device, PredicateLink } from "./types";

export default function App() {
  const [code, setCode] = useState("DQA");
  const [devices, setDevices] = useState<Device[]>([]);
  const [selected, setSelected] = useState<Device | null>(null);
  const [links, setLinks] = useState<PredicateLink[]>([]);
  const [subject, setSubject] = useState("");
  const [result, setResult] = useState<Comparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function search() {
    const d = await run(() => listDevices(code.trim()));
    if (d) { setDevices(d); setSelected(null); setLinks([]); setResult(null); }
  }

  async function pick(d: Device) {
    setSelected(d);
    setResult(null);
    const l = await run(() => listPredicates(d.k_number));
    if (l) setLinks(l);
  }

  async function draft(predicateK: string) {
    const r = await run(() => compare(subject, predicateK));
    if (r) setResult(r);
  }

  const supported = result?.cells.filter((c) => c.supported) ?? [];

  return (
    <main>
      <header>
        <p className="eyebrow">510(k) evidence workbench</p>
        <h1>RegTrace</h1>
        <p className="lede">
          Find cleared devices, follow their predicates, and draft a comparison
          where every line points to a page in the FDA summary.
        </p>
      </header>

      <section className="step">
        <h2><span>01</span> Product code</h2>
        <div className="row">
          <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())}
                 aria-label="FDA product code" maxLength={3} className="mono" />
          <button onClick={search} disabled={busy || code.length !== 3}>Find devices</button>
        </div>
        {devices.length > 0 && (
          <ul className="devices">
            {devices.map((d) => (
              <li key={d.k_number}>
                <button className={selected?.k_number === d.k_number ? "device on" : "device"}
                        onClick={() => pick(d)}>
                  <span className="mono">{d.k_number}</span>
                  <span>{d.device_name ?? "Unnamed device"}</span>
                  <span className="muted">{d.applicant} · {d.decision_date ?? "no date"}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {selected && (
        <section className="step">
          <h2><span>02</span> Predicates cited by <span className="mono">{selected.k_number}</span></h2>
          <label className="field">
            Describe your device
            <textarea rows={3} value={subject} onChange={(e) => setSubject(e.target.value)}
                      placeholder="e.g. fingertip pulse oximeter for spot checks in adults" />
          </label>
          {links.length === 0 ? <p className="muted">No predicates stored for this device yet.</p> : (
            <table>
              <thead><tr><th>Predicate</th><th>Found on page</th><th>Method</th><th /></tr></thead>
              <tbody>
                {links.map((l) => (
                  <tr key={`${l.predicate_k}-${l.method}`}>
                    <td className="mono">{l.predicate_k}</td>
                    <td>{l.page ?? "?"}</td>
                    <td>{l.method}</td>
                    <td><button onClick={() => draft(l.predicate_k)} disabled={busy || !subject.trim()}>
                      Draft comparison</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {result && (
        <section className="step">
          <h2><span>03</span> Comparison against <span className="mono">{result.predicate_k}</span></h2>
          <p className="muted">{supported.length} of {result.cells.length} rows supported by the source.
            Unsupported rows are left blank on purpose.</p>
          <ol className="cells">
            {result.cells.map((c: Cell, i) => (
              <li key={c.row} className={c.supported ? "cell" : "cell gap"}>
                <h3>{c.row}</h3>
                <p>{c.value}{c.supported && <sup>{i + 1}</sup>}</p>
                {c.supported && (
                  <blockquote>
                    <span className="mono">[{i + 1}] {c.k_number}, page {c.page}</span>
                    “{c.evidence}”
                  </blockquote>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}

      {error && <p role="alert" className="error">{error}</p>}
      <footer className="muted">Drafts only. Every claim must be checked against the cited page before use.</footer>
    </main>
  );
}
