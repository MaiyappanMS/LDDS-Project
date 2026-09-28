import { useRef, useState } from 'react';
import { UploadCloud, FileText } from 'lucide-react';

const ACCEPT = '.pdf,.docx,.txt';
const OK = /\.(pdf|docx|txt)$/i;
export const formatSize = (b) => (b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / 1024 / 1024).toFixed(1)} MB`);

export default function FileDropzone({ file, onFile, onReject, disabled }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const pick = (f) => {
    if (!f) return;
    if (!OK.test(f.name)) return onReject?.('Only PDF, DOCX, and TXT files are supported.');
    onFile(f);
  };
  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); if (!disabled) pick(e.dataTransfer.files?.[0]); }}
        className={`flex flex-col items-center rounded-card border-2 border-dashed p-8 text-center ${over ? 'border-brand bg-brand-tint' : 'border-line bg-surface'}`}
      >
        <UploadCloud className="mb-2 h-8 w-8 text-muted" aria-hidden />
        <p className="font-medium">Drag and drop your syllabus here</p>
        <p className="text-sm text-muted">PDF, DOCX, or TXT</p>
        <input ref={input} type="file" accept={ACCEPT} className="sr-only" aria-label="Choose syllabus file" disabled={disabled} onChange={(e) => pick(e.target.files?.[0])} />
        <button type="button" disabled={disabled} onClick={() => input.current?.click()} className="mt-3 rounded-lg border border-line px-4 py-2 text-sm font-medium hover:bg-canvas disabled:opacity-60">Browse files</button>
      </div>
      {file && (
        <div className="mt-3 flex items-center gap-3 rounded-lg border border-line bg-surface p-3">
          <FileText className="h-5 w-5 text-brand" aria-hidden />
          <div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{file.name}</p><p className="text-xs text-muted">{(file.name.split('.').pop() || '').toUpperCase()} · {formatSize(file.size)}</p></div>
        </div>
      )}
    </div>
  );
}
