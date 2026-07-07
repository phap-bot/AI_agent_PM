import React, { useState, useEffect, useRef } from 'react';
import { uploadDocumentsAsync, getIngestStatus } from '../lib/api';
import { useTranslation } from 'react-i18next';

export default function RequirementInputPanel({ onSubmit, isLoading, projectId }) {
  const { t } = useTranslation();
  const storageKey = `draftRequirement_${projectId || 'default'}`;
  const [requirement, setRequirement] = useState('');

  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    setRequirement(saved || '');
  }, [storageKey]);

  const handleRequirementChange = (e) => {
    const val = e.target.value;
    setRequirement(val);
    localStorage.setItem(storageKey, val);
  };

  const [nResults, setNResults] = useState(5);
  const [allowFallback, setAllowFallback] = useState(false);

  // Ingest states
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestData, setIngestData] = useState(null);  // IngestStatusResponse
  const [ingestError, setIngestError] = useState(null);
  const [jobId, setJobId] = useState(null);

  // Accumulated imported files across multiple uploads
  const [importedFiles, setImportedFiles] = useState([]);

  const fileInputRef = useRef(null);
  const pollingRef = useRef(null);

  // --- Polling logic ---
  useEffect(() => {
    if (!jobId || !isIngesting) return;

    console.log(`[POLL] Starting polling for job ${jobId}`);
    pollingRef.current = setInterval(async () => {
      try {
        console.log(`[POLL] Checking status for job ${jobId}...`);
        const status = await getIngestStatus(jobId);
        console.log(`[POLL] Status: ${status.status} - ${status.message}`);

        if (status.status === 'completed') {
          clearInterval(pollingRef.current);
          setIsIngesting(false);
          setIngestData(status);
          setJobId(null);

          // Accumulate newly imported files into the master list
          const newFiles = [
            ...(status.result?.indexed_files || []),
            ...(status.result?.skipped_files || []),
          ];
          setImportedFiles(prev => {
            const existing = new Set(prev.map(f => f.name));
            const additions = newFiles
              .filter(name => !existing.has(name))
              .map(name => ({ name, status: status.result?.indexed_files?.includes(name) ? 'new' : 'existing' }));
            return [...prev, ...additions];
          });

          console.log('[POLL] Ingestion completed', status.result);
        } else if (status.status === 'failed') {
          clearInterval(pollingRef.current);
          setIsIngesting(false);
          setIngestError(status.message);
          setJobId(null);
          console.error('[POLL] Ingestion failed:', status.message);
        }
        // else: still "processing", keep polling
      } catch (err) {
        console.error('[POLL] Error polling status:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [jobId, isIngesting]);

  const handleRemoveFile = (fileName) => {
    setImportedFiles(prev => prev.filter(f => f.name !== fileName));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (requirement.trim().length < 3) return;
    
    // Use accumulated imported files list
    const forcedDocs = importedFiles.map(f => f.name);

    onSubmit({
      requirement,
      n_results: parseInt(nResults, 10),
      allow_fallback_without_context: allowFallback,
      forced_context_docs: forcedDocs,
    });
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsIngesting(true);
    setIngestData(null);
    setIngestError(null);

    try {
      console.log(`[UPLOAD] Uploading ${files.length} file(s)...`);
      const jobResponse = await uploadDocumentsAsync(files, projectId);
      console.log(`[UPLOAD] Job created: ${jobResponse.job_id} - ${jobResponse.message}`);
      setJobId(jobResponse.job_id); // This triggers the polling useEffect
    } catch (err) {
      console.error('[UPLOAD] Upload failed:', err);
      setIsIngesting(false);
      setIngestError(err.message);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_14px_36px_rgba(15,23,42,0.05)]">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-4 sm:px-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex items-start gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-slate-800 text-white shadow-sm">
              <span className="material-symbols-outlined">edit_note</span>
            </div>
            <div>
              <h2 className="text-lg font-black tracking-[-0.03em] text-slate-950 sm:text-xl">
                {t('requirement_input.title')}
              </h2>
              <p className="mt-1 max-w-2xl text-sm leading-5 text-slate-500">
                Paste a stakeholder request, attach context docs, then let the agent research, plan, and evaluate before Jira.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] font-bold">
            <span className="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-slate-700">Local AI ready</span>
            <span className="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-slate-700">BE / FE / QA split</span>
            <span className="rounded-full border border-slate-300 bg-white px-2.5 py-1 text-slate-700">Eval gated</span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 p-4 sm:p-5 xl:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-4">
          <label className="block">
            <span className="mb-2 flex items-center justify-between text-sm font-extrabold text-slate-800">
              Customer request
              <span className="text-xs font-bold text-slate-400">{requirement.trim().length} chars</span>
            </span>
            <textarea
              className="min-h-[160px] w-full resize-none rounded-2xl border border-slate-200 bg-slate-50/80 p-4 text-sm leading-6 text-slate-950 outline-none transition-all placeholder:text-slate-400 focus:border-slate-400 focus:bg-white focus:ring-4 focus:ring-slate-200 disabled:cursor-not-allowed disabled:opacity-60 lg:min-h-[180px]"
              placeholder={t('requirement_input.placeholder')}
              value={requirement}
              onChange={handleRequirementChange}
              disabled={isLoading}
            />
          </label>

          <div className="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/60 p-3 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <input
                type="file"
                multiple
                ref={fileInputRef}
                onChange={handleFileUpload}
                className="hidden"
                id="doc-upload"
                accept=".pdf,.docx,.txt,.md"
              />
              <label
                htmlFor="doc-upload"
                onClick={(e) => {
                  if (!projectId) {
                    e.preventDefault();
                    setIngestError(t('requirement_input.select_project_first'));
                  }
                }}
                className={`inline-flex min-h-10 cursor-pointer items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-bold text-slate-700 shadow-sm transition-all ${isIngesting || isLoading ? 'pointer-events-none opacity-50' : 'hover:-translate-y-0.5 hover:border-slate-400 hover:bg-slate-100'}`}
              >
                <span className="material-symbols-outlined text-[20px]">upload_file</span>
                {isIngesting ? t('requirement_input.processing') : t('requirement_input.import_docs')}
              </label>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">{t('requirement_input.support_formats')}</p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <label className="flex items-center gap-2 text-sm font-bold text-slate-600">
                {t('requirement_input.search_results')}
                <input
                  type="number"
                  min="1"
                  max="10"
                  className="h-10 w-14 rounded-xl border border-slate-200 bg-white px-2 text-center font-bold text-slate-900 outline-none transition focus:border-slate-400 focus:ring-4 focus:ring-slate-200"
                  value={nResults}
                  onChange={e => setNResults(e.target.value)}
                  disabled={isLoading}
                />
              </label>
              <label className="flex min-h-10 cursor-pointer items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-600 transition hover:border-slate-300 hover:bg-slate-100">
                <input
                  type="checkbox"
                  className="rounded border-slate-300 text-slate-700 focus:ring-slate-500"
                  checked={allowFallback}
                  onChange={e => setAllowFallback(e.target.checked)}
                  disabled={isLoading}
                />
                {t('requirement_input.allow_fallback')}
              </label>
            </div>
          </div>

          {ingestError && (
            <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-bold text-red-700">
              <span className="material-symbols-outlined text-red-500">error</span>
              <span>{ingestError}</span>
              <button className="ml-auto rounded-lg p-1 text-red-400 transition hover:bg-red-100 hover:text-red-700" onClick={() => setIngestError(null)} aria-label="Dismiss upload error">
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
          )}

          {isIngesting && (
            <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-100 p-3">
              <span className="h-4 w-4 rounded-full border-2 border-slate-700 border-t-transparent animate-spin"></span>
              <p className="text-sm font-extrabold text-slate-700">{t('requirement_input.backend_embedding')}</p>
            </div>
          )}

          {importedFiles.length > 0 && (
            <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-3">
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-slate-400">{t('requirement_input.imported_docs')} ({importedFiles.length})</p>
              <div className="flex flex-wrap gap-2">
                {importedFiles.map((file, idx) => (
                  <div
                    key={`file-${idx}`}
                    className="group flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-bold transition hover:border-slate-300 hover:bg-slate-100"
                    title={file.name}
                  >
                    <span className={`h-2 w-2 rounded-full ${file.status === 'new' ? 'bg-slate-700' : 'bg-slate-500'}`}></span>
                    <span className="max-w-[220px] truncate text-slate-600">{file.name}</span>
                    <button
                      className="ml-1 rounded-full text-slate-400 opacity-70 transition hover:text-red-600 group-hover:opacity-100"
                      onClick={() => handleRemoveFile(file.name)}
                      title={t('requirement_input.remove_file')}
                    >
                      <span className="material-symbols-outlined text-[14px]">close</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <aside className="flex flex-col gap-3">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Agent path</p>
            <div className="mt-4 space-y-3">
              {['Researcher', 'Planner', 'Evaluator', 'Human approval'].map((step, index) => (
                <div key={step} className="flex items-center gap-2.5">
                  <span className="grid h-6 w-6 place-items-center rounded-full bg-white text-xs font-black text-slate-700 shadow-sm">{index + 1}</span>
                  <span className="text-sm font-extrabold text-slate-700">{step}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 text-white">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-300">Output contract</p>
            <ul className="mt-4 space-y-2.5 text-sm font-semibold text-slate-300">
              <li className="flex gap-2"><span className="text-slate-300">✓</span> As a / I want / So that</li>
              <li className="flex gap-2"><span className="text-slate-300">✓</span> Given / When / Then AC</li>
              <li className="flex gap-2"><span className="text-slate-300">✓</span> Fibonacci story points</li>
              <li className="flex gap-2"><span className="text-slate-300">✓</span> BE / FE / QA tasks</li>
            </ul>
          </div>

          <button
            onClick={handleSubmit}
            disabled={isLoading || requirement.trim().length < 3 || isIngesting}
            className="mt-auto inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-slate-800 px-5 py-3 text-xs font-black uppercase tracking-[0.04em] text-white shadow-sm transition-all hover:-translate-y-0.5 hover:bg-slate-900 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
          >
            {isLoading ? (
              <><span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span> {t('requirement_input.analyzing')}</>
            ) : (
              <>{t('requirement_input.analyze_create_task')}</>
            )}
          </button>
        </aside>
      </div>
    </section>
  );
}
