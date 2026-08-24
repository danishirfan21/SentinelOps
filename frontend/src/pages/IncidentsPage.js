import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
const order = (x) => [x.status === 'OPEN' ? 0 : 1, x.severity === 'CRITICAL' ? 0 : 1, -Date.parse(x.opened_at)];
export default function Incidents() { const [d, setD] = useState(null), [e, setE] = useState(''); useEffect(() => { api.incidents().then(x => setD(x.sort((a, b) => { const A = order(a), B = order(b); return A[0] - B[0] || A[1] - B[1] || A[2] - B[2]; }))).catch(x => setE(x.message)); }, []); if (e)
    return _jsx("p", { role: "alert", children: e }); if (!d)
    return _jsx("p", { children: "Loading incidents\u2026" }); return _jsxs(_Fragment, { children: [_jsx("h1", { children: "Incidents" }), !d.length ? _jsx("p", { children: "No incidents." }) : d.map(x => _jsxs(Link, { className: `incident ${x.status}`, to: `/incidents/${x.id}`, children: [_jsx("b", { children: x.title }), _jsxs("span", { children: [x.severity, " \u00B7 ", x.status] }), _jsxs("small", { children: ["Opened ", new Date(x.opened_at).toLocaleString()] })] }, x.id))] }); }
