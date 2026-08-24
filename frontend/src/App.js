import { Fragment as _Fragment, jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link, Route, Routes } from 'react-router-dom';
import Overview from './pages/OverviewPage';
import ServiceDetail from './pages/ServiceDetailPage';
import Alerts from './pages/AlertsPage';
import Incidents from './pages/IncidentsPage';
import IncidentDetail from './pages/IncidentDetailPage';
export default function App() { return _jsxs(_Fragment, { children: [_jsxs("header", { children: [_jsx(Link, { to: "/", children: "SentinelOps" }), _jsxs("nav", { children: [_jsx(Link, { to: "/alerts", children: "Alerts" }), _jsx(Link, { to: "/incidents", children: "Incidents" })] })] }), _jsx("main", { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Overview, {}) }), _jsx(Route, { path: "/services/:id", element: _jsx(ServiceDetail, {}) }), _jsx(Route, { path: "/alerts", element: _jsx(Alerts, {}) }), _jsx(Route, { path: "/incidents", element: _jsx(Incidents, {}) }), _jsx(Route, { path: "/incidents/:id", element: _jsx(IncidentDetail, {}) })] }) })] }); }
