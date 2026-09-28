import { Bar, BarChart, Cell, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { TONE_HEX, masteryTone } from '../ui/tone';

// data: [{ name, mastery }]. layout "vertical" = horizontal bars (best for long names).
export default function MasteryChart({ data, layout = 'vertical', height }) {
  const vertical = layout === 'vertical';
  const h = height || (vertical ? Math.max(180, data.length * 38) : 260);
  return (
    <div style={{ height: h }} role="img" aria-label="Mastery by concept bar chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout={layout} margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#DDE2EA" horizontal={!vertical} vertical={vertical} />
          {vertical ? (
            <>
              <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} fontSize={12} />
              <YAxis type="category" dataKey="name" width={110} fontSize={12} />
            </>
          ) : (
            <>
              <XAxis dataKey="name" fontSize={12} interval={0} tickFormatter={(v) => (v?.length > 10 ? `${v.slice(0, 9)}…` : v)} />
              <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} fontSize={12} width={40} />
            </>
          )}
          <Tooltip formatter={(v) => [`${v}%`, 'Mastery']} cursor={{ fill: 'rgba(21,34,56,0.04)' }} />
          <Bar dataKey="mastery" radius={4} barSize={vertical ? 16 : 28}>
            {data.map((d, i) => <Cell key={i} fill={TONE_HEX[masteryTone(d.mastery)]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
