import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
export default function ProgressChart({ data }) {
  return (
    <div className="h-52" role="img" aria-label="Mastery over time">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ left: 0, right: 12, top: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#DDE2EA" />
          <XAxis dataKey="name" fontSize={12} /><YAxis domain={[0, 100]} fontSize={12} width={36} tickFormatter={(v) => `${v}%`} />
          <Tooltip formatter={(v) => [`${v}%`, 'Mastery']} />
          <Line type="monotone" dataKey="mastery" stroke="#2F4B8F" strokeWidth={2.5} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
