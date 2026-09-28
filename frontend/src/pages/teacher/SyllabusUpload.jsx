import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle2, Loader2, Circle } from 'lucide-react';
import SubjectHeader from '../../components/layout/SubjectHeader';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import ProgressBar from '../../components/ui/ProgressBar';
import FileDropzone from '../../components/ui/FileDropzone';
import SyllabusAnalysis from '../../components/concepts/SyllabusAnalysis';
import Async from '../../components/ui/Async';
import { syllabusApi, STAGES, normStage } from '../../api/syllabusApi';
import { conceptApi } from '../../api/conceptApi';
import { apiError } from '../../api/client';
import { useApi, invalidate } from '../../hooks/useApi';
import { useToast } from '../../context/ToastContext';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export default function SyllabusUpload() {
  const { id } = useParams();
  const toast = useToast();
  const [file, setFile] = useState(null);
  const [phase, setPhase] = useState('idle'); // idle | uploading | processing | done | error
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('processing');
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const cancelled = useRef(false);
  useEffect(() => () => { cancelled.current = true; }, []);

  const concepts = useApi(`concepts:${id}`, () => conceptApi.bySubject(id), { ttl: 0 });

  const start = async () => {
    setError(''); setPhase('uploading'); setProgress(0);
    try {
      let rec = await syllabusApi.upload(id, file, (p) => { setProgress(p); if (p >= 100) setPhase('processing'); });
      setPhase('processing');
      // If the backend reports a processing status, follow it until it finishes (no faked stages).
      const statusOf = (r) => r?.status ?? r?.processing_status;
      const recId = rec?.id ?? rec?.syllabus_id;
      let s = normStage(statusOf(rec));
      for (let i = 0; statusOf(rec) && s !== 'completed' && s !== 'failed' && recId != null && i < 90 && !cancelled.current; i++) {
        setStage(s);
        await sleep(2000);
        rec = await syllabusApi.get(recId);
        s = normStage(statusOf(rec));
      }
      if (s === 'failed') throw new Error(rec?.error ?? 'The syllabus could not be processed.');
      setResult(rec); setPhase('done');
      invalidate(`concepts:${id}`); invalidate('subject');
      concepts.reload();
      toast.success('Syllabus analyzed.');
    } catch (e) { setError(e.response ? apiError(e) : e.message); setPhase('error'); }
  };

  const busy = phase === 'uploading' || phase === 'processing';
  const stageIdx = STAGES.findIndex((s) => s.key === stage);

  return (
    <>
      <SubjectHeader subjectId={id} section="Syllabus" />
      <div className="grid gap-6 lg:grid-cols-5">
        <div className="space-y-4 lg:col-span-2">
          <FileDropzone file={file} onFile={(f) => { setFile(f); setPhase('idle'); setError(''); }} onReject={setError} disabled={busy} />
          <Button className="w-full" disabled={!file || busy} loading={busy} onClick={start}>{phase === 'error' ? 'Try again' : 'Upload and analyze'}</Button>
          {error && <div role="alert" className="rounded-lg bg-sev-high-tint p-3 text-sm text-sev-high">{error}</div>}
        </div>
        <div className="lg:col-span-3">
          {phase === 'uploading' && <Card><p className="mb-2 text-sm font-medium">Uploading syllabus…</p><ProgressBar tone="brand" value={progress} showValue /></Card>}
          {phase === 'processing' && (
            <Card aria-live="polite">
              <p className="mb-3 flex items-center gap-2 text-sm font-medium"><Loader2 className="h-4 w-4 animate-spin" aria-hidden />{stageIdx >= 0 ? STAGES[stageIdx].label : 'The server is processing your syllabus. This can take up to a minute.'}</p>
              {stageIdx >= 0 && (
                <ol className="space-y-2 text-sm">
                  {STAGES.map((s, i) => (
                    <li key={s.key} className="flex items-center gap-2 text-muted">
                      {i < stageIdx ? <CheckCircle2 className="h-4 w-4 text-sev-low" aria-hidden /> : i === stageIdx ? <Loader2 className="h-4 w-4 animate-spin text-brand" aria-hidden /> : <Circle className="h-4 w-4" aria-hidden />}{s.label}
                    </li>
                  ))}
                </ol>
              )}
            </Card>
          )}
          {!busy && (
            <Async state={concepts} skeleton={<div className="h-32" />} isEmpty={(d) => d.length === 0}
              empty={<Card className="text-center text-sm text-muted">No syllabus has been uploaded yet.</Card>}>
              {(list) => <SyllabusAnalysis result={result} concepts={list} />}
            </Async>
          )}
        </div>
      </div>
    </>
  );
}
