import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
export default function Overview() { const [s, setS] = useState([]), [h, setH] = useState({}), [e, setE] = useState(''); useEffect(() => { api.services().then(async (x) => { setS(x); setH(Object.fromEntries(await Promise.all(x.map(async (s) => [s.id, (await api.health(s.id)).state])))); }).catch(x => setE(x.message)); }, []); if (e)
    return _jsx("p", { role: "alert", children: e }); if (!s.length)
    return _jsx("p", { children: "Loading services\u2026" }); return _jsxs(_Fragment, { children: [_jsx("h1", { children: "Operations overview" }), _jsx("section", { className: "grid", children: s.sort((a, b) => ['DOWN', 'RECOVERING', 'DEGRADED', 'UNKNOWN', 'HEALTHY'].indexOf(h[a.id]) - ['DOWN', 'RECOVERING', 'DEGRADED', 'UNKNOWN', 'HEALTHY'].indexOf(h[b.id])).map(s => _jsxs(Link, { className: `card ${h[s.id]}`, to: `/services/${s.id}`, children: [_jsx("b", { children: s.name }), _jsx("span", { children: h[s.id] })] }, s.id)) })] }); }
