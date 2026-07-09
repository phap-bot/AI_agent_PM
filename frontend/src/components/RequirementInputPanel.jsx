import React, { useState, useEffect, useRef } from 'react';
import { uploadDocumentsAsync, getIngestStatus } from '../lib/api';
import { useTranslation } from 'react-i18next';

export default function RequirementInputPanel({
  onSubmit,
  isLoading,
  projectId,
  context,
  storyDraft,
  evaluation,
  generationMessage,
}) {
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

  const evaluationStatus = evaluation?.status || '';
  const hasContext = Boolean(context);
  const hasStoryDraft = Boolean(storyDraft);
  const hasEvaluation = Boolean(evaluation);
  const contextHasWarning = hasContext && ['empty', 'failed'].includes(context?.retrieval_status);
  const currentAgentStep = !isLoading && !hasEvaluation
    ? 0
    : !hasContext
      ? 0
      : !hasStoryDraft
        ? 1
        : !hasEvaluation
          ? 2
          : 3;
  const completedAgentSteps = [
    hasContext,
    hasStoryDraft,
    hasEvaluation,
    hasEvaluation && evaluationStatus === 'APPROVED',
  ].filter(Boolean).length;
  const agentProgress = Math.min(100, Math.max(12, (completedAgentSteps / 4) * 100));
  const agentSteps = [
    {
      title: 'Researcher',
      icon: 'manage_search',
      description: contextHasWarning
        ? 'No strong context found; assumptions will be explicit.'
        : 'Retrieves project context and prepares evidence.',
      done: hasContext,
      active: isLoading && !hasContext,
      tone: contextHasWarning ? 'warning' : 'blue',
      meta: hasContext ? `${context?.raw_match_count || 0} matches` : 'Scanning docs',
    },
    {
      title: 'Planner',
      icon: 'account_tree',
      description: 'Drafts story, AC, story points, DoD and BE / FE / QA tasks.',
      done: hasStoryDraft,
      active: isLoading && hasContext && !hasStoryDraft,
      tone: 'violet',
      meta: hasStoryDraft ? (storyDraft?.planning_status || 'Draft ready') : 'Waiting for context',
    },
    {
      title: 'Evaluator',
      icon: 'fact_check',
      description: 'Checks readiness, scope, traceability and Jira safety.',
      done: hasEvaluation,
      active: isLoading && hasStoryDraft && !hasEvaluation,
      tone: evaluationStatus === 'REVISION' ? 'warning' : 'green',
      meta: hasEvaluation ? evaluationStatus : 'Waiting for draft',
    },
    {
      title: 'Human approval',
      icon: 'verified_user',
      description: evaluationStatus === 'APPROVED'
        ? 'Ready for PM review before Jira / Slack execution.'
        : 'Blocked until the evaluator approves the story.',
      done: hasEvaluation && evaluationStatus === 'APPROVED',
      active: hasEvaluation && evaluationStatus === 'APPROVED',
      tone: evaluationStatus === 'APPROVED' ? 'green' : 'slate',
      meta: evaluationStatus === 'APPROVED' ? 'Approval gate open' : 'Final gate',
    },
  ];

  const agentToneClass = {
    blue: {
      dot: 'bg-blue-600 text-white shadow-blue-500/25',
      ring: 'ring-blue-100',
      badge: 'bg-blue-50 text-blue-700 border-blue-200',
      text: 'text-blue-700',
    },
    violet: {
      dot: 'bg-violet-600 text-white shadow-violet-500/25',
      ring: 'ring-violet-100',
      badge: 'bg-violet-50 text-violet-700 border-violet-200',
      text: 'text-violet-700',
    },
    green: {
      dot: 'bg-emerald-600 text-white shadow-emerald-500/25',
      ring: 'ring-emerald-100',
      badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      text: 'text-emerald-700',
    },
    warning: {
      dot: 'bg-amber-500 text-white shadow-amber-500/25',
      ring: 'ring-amber-100',
      badge: 'bg-amber-50 text-amber-700 border-amber-200',
      text: 'text-amber-700',
    },
    slate: {
      dot: 'bg-white text-slate-500 shadow-slate-900/5',
      ring: 'ring-slate-100',
      badge: 'bg-slate-100 text-slate-500 border-slate-200',
      text: 'text-slate-500',
    },
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

      <div className="grid gap-4 p-3 sm:p-4 lg:p-5">
        <div className="space-y-4">
          <label className="block">
            <span className="mb-2 flex items-center justify-between text-sm font-extrabold text-slate-800">
              Customer request
              <span className="text-xs font-bold text-slate-400">{requirement.trim().length} chars</span>
            </span>
            <textarea
              className="min-h-[clamp(150px,22vh,240px)] w-full resize-none rounded-2xl border border-slate-200 bg-slate-50/80 p-3.5 text-sm leading-6 text-slate-950 outline-none transition-all placeholder:text-slate-400 focus:border-slate-400 focus:bg-white focus:ring-4 focus:ring-slate-200 disabled:cursor-not-allowed disabled:opacity-60 sm:p-4"
              placeholder={t('requirement_input.placeholder')}
              value={requirement}
              onChange={handleRequirementChange}
              disabled={isLoading}
            />
          </label>

          <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white via-slate-50/80 to-blue-50/40 p-3 shadow-sm">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <input
                type="file"
                multiple
                ref={fileInputRef}
                onChange={handleFileUpload}
                className="hidden"
                id="doc-upload"
                accept=".pdf,.docx,.txt,.md"
              />
              <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center">
                <label
                  htmlFor="doc-upload"
                  onClick={(e) => {
                    if (!projectId) {
                      e.preventDefault();
                      setIngestError(t('requirement_input.select_project_first'));
                    }
                  }}
                  className={`group inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-2xl border border-blue-100 bg-white px-4 py-2 text-sm font-black text-slate-800 shadow-sm shadow-blue-950/5 transition-all ${isIngesting || isLoading ? 'pointer-events-none opacity-50' : 'hover:-translate-y-0.5 hover:border-blue-200 hover:bg-blue-50 hover:shadow-md'}`}
                >
                  <span className="grid h-7 w-7 place-items-center rounded-xl bg-blue-50 text-blue-700 transition group-hover:bg-blue-100">
                    <span className="material-symbols-outlined text-[18px]">upload_file</span>
                  </span>
                  {isIngesting ? t('requirement_input.processing') : t('requirement_input.import_docs')}
                </label>
                <div className="min-w-0">
                  <p className="text-[11px] font-black uppercase tracking-[0.14em] text-slate-400">Context files</p>
                  <p className="mt-0.5 text-xs font-semibold text-slate-500">{t('requirement_input.support_formats')}</p>
                </div>
              </div>

              <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center xl:justify-end">
                <label className="flex min-h-11 items-center gap-3 rounded-2xl border border-slate-200 bg-white/90 px-3.5 py-2 shadow-sm shadow-slate-950/5">
                  <span className="material-symbols-outlined text-[18px] text-slate-400">travel_explore</span>
                  <span className="text-xs font-bold text-slate-500">{t('requirement_input.search_results')}</span>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    className="h-8 w-12 rounded-xl border border-slate-100 bg-slate-50 px-2 text-center text-sm font-black text-slate-900 outline-none transition focus:border-blue-200 focus:bg-white focus:ring-4 focus:ring-blue-100"
                    value={nResults}
                    onChange={e => setNResults(e.target.value)}
                    disabled={isLoading}
                  />
                </label>
                <label className={`flex min-h-11 min-w-0 cursor-pointer items-center gap-3 rounded-2xl border px-3.5 py-2 text-sm font-bold shadow-sm shadow-slate-950/5 transition ${
                  allowFallback
                    ? 'border-blue-200 bg-blue-50 text-blue-800'
                    : 'border-slate-200 bg-white/90 text-slate-600 hover:border-slate-300 hover:bg-white'
                }`}>
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    checked={allowFallback}
                    onChange={e => setAllowFallback(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span className="min-w-0">{t('requirement_input.allow_fallback')}</span>
                </label>
              </div>
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
            <div className="flex items-start gap-3 rounded-xl border border-blue-200 bg-blue-50 p-3 text-blue-950">
              <span className="mt-0.5 h-4 w-4 rounded-full border-2 border-blue-700 border-t-transparent animate-spin"></span>
              <div>
                <p className="text-sm font-extrabold">{t('requirement_input.backend_embedding')}</p>
                <p className="mt-1 text-xs font-semibold leading-5 text-blue-700">{t('requirement_input.backend_embedding_hint')}</p>
              </div>
            </div>
          )}

          {!isIngesting && ingestData?.result && (
            <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-emerald-950">
              <span className="material-symbols-outlined mt-0.5 text-[18px] text-emerald-600">check_circle</span>
              <div>
                <p className="text-sm font-extrabold">{t('requirement_input.import_complete')}</p>
                <p className="mt-1 text-xs font-semibold leading-5 text-emerald-700">
                  {ingestData.result.files_indexed} indexed · {ingestData.result.skipped_count} unchanged · {ingestData.result.chunks_indexed} search chunks
                </p>
              </div>
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

          <div className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-3 text-white shadow-sm lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
            <div className="min-w-0">
              <p className="text-[11px] font-black uppercase tracking-[0.18em] text-slate-300">Output contract</p>
              <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-xs font-semibold text-slate-200">
                <li className="flex items-center gap-1.5 whitespace-nowrap"><span className="material-symbols-outlined text-[15px] text-emerald-300">check</span> As a / I want / So that</li>
                <li className="flex items-center gap-1.5 whitespace-nowrap"><span className="material-symbols-outlined text-[15px] text-emerald-300">check</span> Given / When / Then AC</li>
                <li className="flex items-center gap-1.5 whitespace-nowrap"><span className="material-symbols-outlined text-[15px] text-emerald-300">check</span> Fibonacci story points</li>
                <li className="flex items-center gap-1.5 whitespace-nowrap"><span className="material-symbols-outlined text-[15px] text-emerald-300">check</span> BE / FE / QA tasks</li>
              </ul>
            </div>

            <button
              onClick={handleSubmit}
              disabled={isLoading || requirement.trim().length < 3 || isIngesting}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-xs font-black uppercase tracking-[0.04em] text-slate-900 shadow-sm transition-all hover:-translate-y-0.5 hover:bg-slate-100 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 lg:w-auto"
            >
              {isLoading ? (
                <><span className="h-4 w-4 rounded-full border-2 border-slate-900 border-t-transparent animate-spin"></span> {t('requirement_input.analyzing')}</>
              ) : (
                <>{t('requirement_input.analyze_create_task')}</>
              )}
            </button>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-50">
            <div className="border-b border-slate-200 bg-white/80 px-4 py-3">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.18em] text-slate-500">Agent path</p>
                  <p className="mt-1 text-[11px] font-semibold text-slate-500">
                    {isLoading
                      ? (generationMessage || 'Agents are working in sequence...')
                      : hasEvaluation
                        ? 'Pipeline completed. Review the gate result.'
                        : 'Follow the work from context to approval.'}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-[10px] font-black ${
                    isLoading ? 'border-blue-200 bg-blue-50 text-blue-700' : hasEvaluation ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-500'
                  }`}>
                    {isLoading && <span className="absolute inset-0 rounded-full bg-blue-400/20 animate-ping" />}
                    {completedAgentSteps}/4
                  </span>
                  <div className="h-1.5 w-28 overflow-hidden rounded-full bg-slate-200 sm:w-36">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        evaluationStatus === 'APPROVED'
                          ? 'bg-emerald-500'
                          : evaluationStatus === 'REVISION'
                            ? 'bg-amber-500'
                            : 'bg-blue-600'
                      }`}
                      style={{ width: `${agentProgress}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="relative overflow-x-auto overscroll-x-contain p-4">
              <div className="absolute left-8 right-8 top-[38px] hidden h-px bg-slate-200 lg:block" />
              <div className="absolute left-8 right-8 top-[38px] hidden h-px overflow-hidden lg:block">
                <div
                  className={`h-full transition-all duration-700 ${
                    evaluationStatus === 'REVISION' ? 'bg-amber-400' : 'bg-blue-500'
                  }`}
                  style={{ width: `${agentProgress}%` }}
                />
              </div>

              <div className="grid min-w-[880px] grid-cols-4 gap-3">
                {agentSteps.map((step, index) => {
                  const tone = agentToneClass[step.tone] || agentToneClass.slate;
                  const isCurrent = step.active || (isLoading && currentAgentStep === index);
                  const stateLabel = step.done
                    ? 'Done'
                    : isCurrent
                      ? 'Running'
                      : 'Queued';

                  return (
                    <div
                      key={step.title}
                      className={`relative min-h-[178px] rounded-2xl border bg-white p-3 shadow-sm transition-all duration-300 ${
                        isCurrent
                          ? `border-slate-300 ring-4 ${tone.ring}`
                          : step.done
                            ? 'border-slate-200'
                            : 'border-slate-100 bg-white/70'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className={`relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white text-[18px] shadow-md ${step.done || isCurrent ? tone.dot : agentToneClass.slate.dot}`}>
                          {isCurrent && <span className="absolute inset-0 rounded-full bg-current opacity-20 animate-ping" />}
                          <span className="material-symbols-outlined text-[18px]">
                            {step.done ? 'check' : step.icon}
                          </span>
                        </span>
                        <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[9px] font-black uppercase tracking-[0.08em] ${step.done || isCurrent ? tone.badge : agentToneClass.slate.badge}`}>
                          {stateLabel}
                        </span>
                      </div>
                      <div className="mt-3 min-w-0">
                        <p className="text-sm font-black text-slate-800">{step.title}</p>
                        <p className="mt-1 text-[11px] leading-4 text-slate-500">{step.description}</p>
                        <div className="mt-3 flex items-center gap-2 rounded-xl bg-slate-50 px-2.5 py-2">
                          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${step.done || isCurrent ? tone.dot.split(' ')[0] : 'bg-slate-300'}`} />
                          <p className={`truncate text-[10px] font-bold ${step.done || isCurrent ? tone.text : 'text-slate-400'}`}>
                            {step.meta}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>


      </div>
    </section>
  );
}
