import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { TONE_HEX } from '../ui/tone';

// distribution: { high, medium, low }
export default function DebtChart({ distribution }) {
  const rows = [
    { name: 'High', value: Number(distribution.high) || 0, color: TONE_HEX.high },
    { name: 'Medium', value: Number(distribution.medium) || 0, color: TONE_HEX.mid },
    { name: 'Low', value: Number(distribution.low) || 0, color: TONE_HEX.low },
  ];
  return (
    <div className="flex items-center gap-4">
      <div className="h-40 w-40 shrink-0" role="img" aria-label="Learning debt distribution">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={rows} dataKey="value" innerRadius={44} outerRadius={70} paddingAngle={2} stroke="none">
              {rows.map((r) => <Cell key={r.name} fill={r.color} />)}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="space-y-2 text-sm">
        {rows.map((r) => (
          <li key={r.name} className="flex items-center gap-2"><span className="h-3 w-3 rounded-full" style={{ background: r.color }} aria-hidden />{r.name}: <b className="tabular-nums">{r.value}</b></li>
        ))}
      </ul>
    </div>
  );
}
