export const masteryTone = (v) => (v < 40 ? 'high' : v < 60 ? 'mid' : 'low');
export const TONE_HEX = { high: '#C43D2F', mid: '#B9740F', low: '#2E7D6B', brand: '#2F4B8F' };
export const severityTone = (s) => ({ HIGH: 'high', MEDIUM: 'mid', LOW: 'low' }[s] || 'mid');
export const difficultyTone = (d) => (/(begin|easy|basic)/.test(d) ? 'low' : /(inter|medium)/.test(d) ? 'mid' : /(adv|hard)/.test(d) ? 'high' : 'neutral');
export const formatDate = (d) => { if (!d) return ''; const t = new Date(d); return Number.isNaN(t.getTime()) ? String(d) : t.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }); };
