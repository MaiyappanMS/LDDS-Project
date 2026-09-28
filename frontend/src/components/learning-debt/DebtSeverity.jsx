import Badge from '../ui/Badge';
import { severityTone } from '../ui/tone';
const LABEL = { HIGH: 'High debt', MEDIUM: 'Medium debt', LOW: 'Low debt' };
export default function DebtSeverity({ severity }) {
  return <Badge tone={severityTone(severity)}>{LABEL[severity] || severity}</Badge>;
}
