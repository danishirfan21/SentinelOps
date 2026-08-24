import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { api } from '../api/client';
export default function Alerts() {
    const [alerts, setAlerts] = useState(null);
    const [error, setError] = useState('');
    useEffect(() => {
        api.alerts().then(items => setAlerts(items.sort((a, b) => {
            if (a.state !== b.state)
                return a.state === 'OPEN' ? -1 : 1;
            if (a.severity !== b.severity)
                return a.severity === 'CRITICAL' ? -1 : 1;
            return b.opened_at.localeCompare(a.opened_at);
        }))).catch(value => setError(value.message));
    }, []);
    if (error)
        return _jsx("p", { role: "alert", children: error });
    if (!alerts)
        return _jsx("p", { children: "Loading alerts\u2026" });
    return _jsxs(_Fragment, { children: [_jsx("h1", { children: "Alerts" }), alerts.length === 0 ? _jsx("p", { children: "No alerts." }) : alerts.map(alert => _jsxs("p", { className: alert.state, children: [alert.severity, " \u00B7 ", alert.state, " \u00B7 ", alert.opened_at] }, alert.id))] });
}
