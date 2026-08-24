import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
export default function ServiceDetail() { const { id = '' } = useParams(); const [d, setD] = useState(); useEffect(() => { Promise.all([api.health(id), api.checks(id), api.history(id)]).then(x => setD(x)); }, [id]); if (!d)
    return _jsx("p", { children: "Loading service\u2026" }); return _jsxs(_Fragment, { children: [_jsx("h1", { children: "Service detail" }), _jsx("h2", { children: d[0].state }), _jsx("h3", { children: "Recent checks" }), d[1].map((x) => _jsxs("p", { children: [x.checked_at, " \u00B7 ", x.success ? 'success' : 'failure', " \u00B7 ", x.latency_ms ?? '—', "ms"] }, x.id)), _jsx("h3", { children: "Health history" }), d[2].map((x) => _jsxs("p", { children: [x.state, " \u00B7 ", x.started_at] }, x.id))] }); }
