import React, { useEffect, useState } from "react";
import api, { mensajeError } from "./api";

const fmt = (v, d = 4) => (v == null || v === "" ? "—" : Number(v).toLocaleString("es-GT", { maximumFractionDigits: d }));

// ---------- Consumos (matriz producto x recurso) ----------
export function Consumos() {
  const [prods, setProds] = useState([]), [recs, setRecs] = useState([]), [m, setM] = useState({});
  const [error, setError] = useState(""), [ok, setOk] = useState(""), [busy, setBusy] = useState(false);
  const key = (p, r) => `${p}-${r}`;
  async function load() {
    try {
      const [p, r, c] = await Promise.all([api.get("/productos"), api.get("/recursos"), api.get("/consumos")]);
      setProds(p.data.productos || []); setRecs(r.data.recursos || []);
      setM(Object.fromEntries((c.data.consumos || []).map(x => [key(x.producto_id, x.recurso_id), String(Number(x.cantidad))])));
      setError("");
    } catch (e) { setError(mensajeError(e)); }
  }
  useEffect(() => { load(); }, []);
  async function save(e) {
    e.preventDefault(); setBusy(true); setOk(""); setError("");
    try {
      const consumos = prods.flatMap(p => recs.map(r => ({ producto_id: p.id, recurso_id: r.id, cantidad: Number(m[key(p.id, r.id)] || 0) })));
      await api.put("/consumos", { consumos });
      setOk("Consumos guardados."); load();
    } catch (err) { setError(mensajeError(err)); } finally { setBusy(false); }
  }
  return <section className="panel">
    <div className="panel-head"><div><h3>Consumos</h3><p>Cuánto de cada recurso consume una unidad de cada producto.</p></div></div>
    {error && <div className="alert error">{error}</div>}{ok && <div className="alert success-alert">{ok}</div>}
    {prods.length && recs.length ? <form onSubmit={save}>
      <div className="table-wrap"><table><thead><tr><th>Producto \ Recurso</th>{recs.map(r => <th key={r.id}>{r.nombre} ({r.unidad})</th>)}</tr></thead>
        <tbody>{prods.map(p => <tr key={p.id}><td><b>{p.nombre}</b><small>{p.codigo}</small></td>
          {recs.map(r => <td key={r.id}><input className="table-input" type="number" min="0" step="any" value={m[key(p.id, r.id)] ?? ""} placeholder="0"
            onChange={e => setM({ ...m, [key(p.id, r.id)]: e.target.value })} /></td>)}</tr>)}</tbody></table></div>
      <div className="form-actions"><button className="btn primary" disabled={busy}>{busy ? "Guardando…" : "Guardar consumos"}</button></div>
    </form> : <p className="muted">Primero registra al menos un producto y un recurso.</p>}
  </section>;
}

// ---------- Resultado con pestaña de comprobación ----------
async function descargarPdf(id, tipo) {
  const r = await api.get(`/resultados/${id}/pdf`, { params: { tipo }, responseType: "blob" });
  const url = URL.createObjectURL(r.data);
  const a = document.createElement("a"); a.href = url; a.download = `${tipo}-${id}.pdf`; a.click();
  URL.revokeObjectURL(url);
}

const ESTADOS = {
  optimo: "Solución óptima encontrada.",
  multiple: "Soluciones múltiples: hay otras combinaciones con el mismo valor de Z.",
  degenerado: "Solución degenerada: es válida, pero hubo empate en la razón mínima.",
  infactible: "Sin solución factible: las restricciones se contradicen.",
  no_acotado: "Solución no acotada: Z puede crecer sin límite (revisa que los consumos estén configurados).",
};

function Comprobacion({ id }) {
  const [d, setD] = useState(null), [err, setErr] = useState("");
  useEffect(() => { api.get(`/resultados/${id}/procedimiento`).then(r => setD(r.data)).catch(e => setErr(mensajeError(e))); }, [id]);
  if (err) return <div className="alert error">{err}</div>;
  if (!d) return <div className="loading">Cargando procedimiento…</div>;
  const f = d.forma_estandar;
  return <div>
    <h4>Modelo</h4>
    <p>{f.objetivo === "max" ? "Maximizar" : "Minimizar"} Z = {f.c.map((c, i) => `${fmt(c)}${f.variables[i]}`).join(" + ")}</p>
    <ul>{f.A.map((fila, i) => <li key={i}>{f.restricciones[i]}: {fila.map((a, j) => `${fmt(a)}${f.variables[j]}`).join(" + ")} {f.tipos[i]} {fmt(f.b[i])}</li>)}</ul>
    {d.iteraciones.map(it => <div key={it.numero}>
      <h4>Tabla {it.numero}{it.fase ? ` (${it.fase})` : ""}</h4>
      <p className="muted">{it.explicacion}{it.entra ? ` Entra: ${it.entra}. Sale: ${it.sale}.` : ""}</p>
      <div className="table-wrap"><table><thead><tr><th>Base</th>{it.columnas.map(c => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>{it.filas.map((fila, i) => <tr key={i}><td><b>{it.base[i]}</b></td>
          {fila.map((v, j) => <td key={j} style={it.pivote && it.pivote.fila === i && it.pivote.columna === j ? { background: "#fde68a", fontWeight: 700 } : null}>{v}</td>)}</tr>)}
          {it.costos_reducidos && <tr><td><b>Z (c-z)</b></td>{it.columnas.map(c => <td key={c}>{it.costos_reducidos[c] ?? ""}</td>)}</tr>}
        </tbody></table></div>
      {it.valor_objetivo != null && <small>Z = {it.valor_objetivo}</small>}
    </div>)}
  </div>;
}

export function ResultadoDetalle({ result, onClose }) {
  const [tab, setTab] = useState("resultado"), [err, setErr] = useState("");
  useEffect(() => { setTab("resultado"); setErr(""); }, [result?.id]);
  if (!result) return null;
  const pdf = tipo => descargarPdf(result.id, tipo).catch(e => setErr(mensajeError(e)));
  return <section className="panel result-panel">
    <div className="panel-head"><div><div className="eyebrow">RESULTADO DEL MÉTODO SIMPLEX</div><h3>{result.escenario?.nombre}</h3>
      <p>Estado: {result.estado} · Iteraciones: {result.iteraciones_n ?? "—"}</p></div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button className="btn secondary small" onClick={() => pdf("reporte")}>PDF reporte</button>
        <button className="btn secondary small" onClick={() => pdf("comprobacion")}>PDF comprobación</button>
        <button className="btn secondary small" onClick={onClose}>Cerrar</button></div></div>
    {err && <div className="alert error">{err}</div>}
    <div className={`alert ${["optimo", "multiple", "degenerado"].includes(result.estado) ? "success-alert" : "warning"}`}>{ESTADOS[result.estado] || result.estado}</div>
    <div className="segmented" style={{ marginBottom: 12 }}>
      <button type="button" className={tab === "resultado" ? "selected" : ""} onClick={() => setTab("resultado")}>Resultado</button>
      <button type="button" className={tab === "comprobacion" ? "selected" : ""} onClick={() => setTab("comprobacion")}>Comprobación</button></div>
    {tab === "comprobacion" ? <Comprobacion id={result.id} /> : <>
      <div className="result-highlight"><span>Valor objetivo (Z)</span><b>{result.valor_z == null ? "No disponible" : fmt(result.valor_z)}</b></div>
      <h4>Plan por producto</h4>
      <div className="table-wrap"><table><thead><tr><th>Producto</th><th>Cantidad</th><th>Aporte</th></tr></thead>
        <tbody>{(result.variables || []).map(v => <tr key={v.producto_id}><td><b>{v.nombre}</b><small>{v.codigo}</small></td><td>{fmt(v.valor)}</td><td>{fmt(v.aporte)}</td></tr>)}</tbody></table></div>
      <h4>Uso de recursos</h4>
      <div className="table-wrap"><table><thead><tr><th>Recurso</th><th>Usado</th><th>Disponible</th><th>Holgura</th><th>Precio sombra</th></tr></thead>
        <tbody>{(result.recursos || []).map(r => <tr key={r.recurso_id}><td><b>{r.nombre}</b></td><td>{fmt(r.usado)}</td><td>{fmt(r.disponible)}</td><td>{fmt(r.holgura)}</td><td>{fmt(r.precio_sombra, 6)}</td></tr>)}</tbody></table></div>
      {result.posibilidades?.length > 1 && <>
        <h4>Otras combinaciones posibles</h4>
        <div className="table-wrap"><table><thead><tr><th>Opción</th><th>Cantidades</th><th>Z</th><th>% del óptimo</th></tr></thead>
          <tbody>{result.posibilidades.map((p, i) => <tr key={i} style={i === 0 ? { background: "#dcfce7", color: "#111" } : null}><td><b>{p.opcion}</b></td>
            <td>{(result.variables || []).map((v, j) => `${v.codigo}=${fmt(p.valores[j])}`).join(", ")}</td><td>{fmt(p.z)}</td><td>{fmt(p.pct, 1)}%</td></tr>)}</tbody></table></div></>}
      {result.recomendaciones?.length > 0 && <><h4>Recomendaciones</h4>
        <ul className="recommendations">{result.recomendaciones.map((r, i) => <li key={i}><b>{r.titulo}</b><p>{r.detalle}</p></li>)}</ul></>}
    </>}
  </section>;
}

// ---------- Ayuda (panel lateral) ----------
export function Ayuda() {
  const [open, setOpen] = useState(false);
  return <>
    <button aria-label="Ayuda" onClick={() => setOpen(true)} style={{ position: "fixed", right: 16, bottom: 16, width: 44, height: 44, borderRadius: "50%", border: 0, background: "#2563eb", color: "#fff", fontSize: 20, cursor: "pointer", zIndex: 50 }}>i</button>
    {open && <aside style={{ position: "fixed", top: 0, right: 0, bottom: 0, width: "min(380px,100%)", background: "#fff", color: "#111", boxShadow: "-4px 0 20px rgba(0,0,0,.2)", padding: 20, overflowY: "auto", zIndex: 60 }}>
      <button className="btn secondary small" onClick={() => setOpen(false)} style={{ float: "right" }}>Cerrar</button>
      <h3>Ayuda</h3>
      <h4>Guía de uso</h4>
      <ol><li>Registra productos (beneficio o costo) y recursos (disponibilidad).</li><li>En <b>Consumos</b>, indica cuánto recurso usa cada producto.</li><li>En <b>Escenarios</b>, elige objetivo, productos y ajusta recursos; crea el escenario y pulsa «Resolver con Simplex».</li><li>Revisa el resultado; en la pestaña «Comprobación» está el paso a paso.</li></ol>
      <h4>Avisos</h4>
      <ul>{Object.entries(ESTADOS).map(([k, v]) => <li key={k}><b>{k}</b>: {v}</li>)}</ul>
      <h4>Glosario</h4>
      <ul><li><b>Holgura</b>: recurso que sobra (0 = se agota).</li><li><b>Precio sombra</b>: lo que aportaría una unidad extra del recurso.</li><li><b>Cuello de botella</b>: recurso con mayor precio sombra.</li><li><b>Variable básica</b>: variable en la base de la tabla simplex.</li></ul>
    </aside>}
  </>;
}
