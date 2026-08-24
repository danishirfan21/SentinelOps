import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client';
export default function IncidentDetail() { const { id = '' } = useParams(), [d, setD] = useState(), [e, setE] = useState(''); useEffect(() => { Promise.all([api.incident(id), api.events(id)]).then(x => setD(x)).catch(x => setE(x.message)); }, [id]); if (e)
    return _jsx("p", { role: "alert", children: e }); if (!d)
    return _jsx("p", { children: "Loading incident\u2026" }); const [i, events] = d; return _jsxs(_Fragment, { children: [_jsx("h1", { children: i.title }), _jsxs("p", { children: [i.severity, " \u00B7 ", _jsx("b", { children: i.status })] }), _jsxs("p", { children: ["Opened ", new Date(i.opened_at).toLocaleString(), i.resolved_at && ` · Resolved ${new Date(i.resolved_at).toLocaleString()}`] }), _jsx("h2", { children: "Timeline" }), events.map((x) => _jsxs("article", { className: "event", children: [_jsx("b", { children: x.event_type.replaceAll('_', ' ') }), _jsx("time", { children: new Date(x.occurred_at).toLocaleString() }), _jsx("p", { children: x.message })] }, x.id))] }); }
