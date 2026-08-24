import { useEffect, useState } from 'react';
import { api } from '../api/client';

export default function Alerts() {
  const [alerts, setAlerts] = useState<any[] | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    api.alerts().then(items => setAlerts(items.sort((a, b) => {
      if (a.state !== b.state) return a.state === 'OPEN' ? -1 : 1;
      if (a.severity !== b.severity) return a.severity === 'CRITICAL' ? -1 : 1;
      return b.opened_at.localeCompare(a.opened_at);
    }))).catch(value => setError(value.message));
  }, []);
  if (error) return <p role="alert">{error}</p>;
  if (!alerts) return <p>Loading alerts…</p>;
  return <><h1>Alerts</h1>{alerts.length === 0 ? <p>No alerts.</p> : alerts.map(alert => <p className={alert.state} key={alert.id}>{alert.severity} · {alert.state} · {alert.opened_at}</p>)}</>;
}
