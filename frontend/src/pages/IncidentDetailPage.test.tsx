import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { vi, describe, expect, it } from 'vitest';
import IncidentDetail from './IncidentDetailPage';

vi.mock('../api/client', () => ({ api: {
  incident: vi.fn().mockResolvedValue({ id: 'incident-1', title: 'Payments outage', severity: 'CRITICAL', status: 'RESOLVED', opened_at: '2026-08-24T10:00:00Z', resolved_at: '2026-08-24T10:30:00Z' }),
  events: vi.fn().mockResolvedValue([
    { id: '1', event_type: 'OPENED', occurred_at: '2026-08-24T10:00:00Z', message: 'Opened by critical alert' },
    { id: '2', event_type: 'RECOVERY_STARTED', occurred_at: '2026-08-24T10:10:00Z', message: 'Recovery started' },
    { id: '3', event_type: 'STATE_CHANGED', occurred_at: '2026-08-24T10:15:00Z', message: 'Recovery failed' },
    { id: '4', event_type: 'RECOVERY_STARTED', occurred_at: '2026-08-24T10:20:00Z', message: 'Recovery started again' },
    { id: '5', event_type: 'RESOLVED', occurred_at: '2026-08-24T10:30:00Z', message: 'Resolved after healthy recovery' },
  ])
} }));

describe('incident timeline', () => {
  it('renders a failed recovery as events within one incident', async () => {
    render(<MemoryRouter initialEntries={['/incidents/incident-1']}><Routes><Route path="/incidents/:id" element={<IncidentDetail />} /></Routes></MemoryRouter>);
    expect(await screen.findByText('Payments outage')).toBeInTheDocument();
    expect(screen.getAllByText('RECOVERY STARTED')).toHaveLength(2);
    expect(screen.getByText('STATE CHANGED')).toBeInTheDocument();
    expect(screen.getAllByText('Payments outage')).toHaveLength(1);
  });
});
