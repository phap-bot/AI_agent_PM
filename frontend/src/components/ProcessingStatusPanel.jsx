import { useTranslation } from 'react-i18next';

export default function ProcessingStatusPanel({ isLoading, context, storyDraft, evaluation }) {
  const { t } = useTranslation();
  // Determine state of Researcher
  const isResearcherDone = !!context;
  const isResearcherEmpty = context && (context.retrieval_status === 'empty' || context.retrieval_status === 'failed');
  
  // Determine state of Planner
  const isPlannerDone = !!storyDraft;
  const isPlannerWorking = isLoading && isResearcherDone && !isPlannerDone; // roughly 
  
  // Determine state of Evaluator
  const isEvaluatorDone = !!evaluation;
  const evaluatorStatus = evaluation?.status; // APPROVED or REVISION

  return (
    <section className="grid grid-cols-1 gap-gutter lg:grid-cols-3">
      {/* Researcher Card */}
      <div className={`bg-white/80 backdrop-blur-sm rounded-xl border border-outline-variant p-stack-md border-l-4 shadow-sm transition-all hover:shadow-md ${isResearcherDone ? 'border-l-blue-500' : 'border-l-gray-300'}`}>
        <div className="flex items-center justify-between mb-unit">
          <span className="text-label-md font-label-md text-outline uppercase tracking-wider">{t('processing_status.researcher')}</span>
          {isResearcherDone && !isResearcherEmpty && (
             <span className="material-symbols-outlined text-blue-500 text-[20px]" style={{fontVariationSettings: "'FILL' 1"}}>verified</span>
          )}
          {isLoading && !isResearcherDone && (
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>
        {isResearcherDone ? (
          isResearcherEmpty ? (
            <p className="font-body-md text-on-surface font-semibold">{t('processing_status.researcher_empty')}</p>
          ) : (
            <div className="font-body-sm text-on-surface">
              <div className="font-semibold mb-1">{t('processing_status.retrieved_context')}</div>
              <ul className="list-decimal pl-4 mb-2 space-y-1">
                {context?.retrieved_sources?.map((src, idx) => (
                  <li key={idx} className="text-xs text-gray-700">
                    <span className="font-medium">{src.source} <span className="text-gray-400 font-normal">({t('processing_status.chunk_label')} {src.chunk_index !== undefined ? src.chunk_index : '?'})</span></span>
                    <span className="text-gray-500">
                      {' '} - {t('processing_status.score_label')}: {src.score != null ? Number(src.score).toFixed(2) : t('common.not_available')}
                      {' '} - {src.score < 0.5 ? t('processing_status.low_relevance') : t('processing_status.high_relevance')}
                    </span>
                  </li>
                ))}
              </ul>
              {context?.warnings?.length > 0 && (
                <div className="text-orange-600 text-xs mt-2 bg-orange-50 p-2 rounded border border-orange-100">
                  <span className="font-bold">{t('processing_status.warning')}</span> {context.warnings.join(' ')}
                </div>
              )}
            </div>
          )
        ) : (
          <p className="font-body-md text-on-surface font-semibold">
            {isLoading ? t('processing_status.researching') : t('processing_status.waiting')}
          </p>
        )}
        <div className={`mt-2 text-[10px] font-bold ${isResearcherDone ? 'text-blue-400' : 'text-gray-400'}`}>
          {isResearcherDone ? t('processing_status.completed') : t('processing_status.pending')}
        </div>
      </div>

      {/* Planner Card */}
      <div className={`bg-white/80 backdrop-blur-sm rounded-xl border border-outline-variant p-stack-md border-l-4 relative overflow-hidden shadow-sm transition-all hover:shadow-md ${isPlannerDone ? 'border-l-primary' : (isPlannerWorking ? 'border-l-primary' : 'border-l-gray-300')}`}>
        {isPlannerWorking && <div className="absolute top-0 left-0 w-full h-1 shimmer-bg"></div>}
        <div className="flex items-center justify-between mb-unit">
          <span className="text-label-md font-label-md text-outline uppercase tracking-wider">{t('processing_status.planner')}</span>
          {isPlannerWorking && (
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
          )}
          {isPlannerDone && (
             <span className="material-symbols-outlined text-primary text-[20px]" style={{fontVariationSettings: "'FILL' 1"}}>check_circle</span>
          )}
        </div>
        <p className="font-body-md text-on-surface font-semibold">
          {isPlannerDone 
            ? t('processing_status.planner_done')
            : (isPlannerWorking ? t('processing_status.planner_working') : t('processing_status.waiting'))}
        </p>
        <div className="mt-2 flex gap-1">
          {isPlannerWorking ? (
            <>
              <div className="h-1 bg-primary rounded-full flex-1"></div>
              <div className="h-1 bg-primary/20 rounded-full flex-1"></div>
              <div className="h-1 bg-primary/20 rounded-full flex-1"></div>
            </>
          ) : isPlannerDone ? (
            <div className="mt-2 text-[10px] text-primary font-bold">{t('processing_status.completed')}</div>
          ) : (
            <div className="mt-2 text-[10px] text-gray-400 font-bold">{t('processing_status.pending')}</div>
          )}
        </div>
      </div>

      {/* Evaluator Card */}
      <div className={`bg-white/80 backdrop-blur-sm rounded-xl border border-outline-variant p-stack-md border-l-4 shadow-sm transition-all hover:shadow-md ${isEvaluatorDone ? (evaluatorStatus === 'APPROVED' ? 'border-l-green-500' : 'border-l-orange-500') : 'border-l-gray-300'}`}>
        <div className="flex items-center justify-between mb-unit">
          <span className="text-label-md font-label-md text-outline uppercase tracking-wider">{t('processing_status.evaluator')}</span>
          {isEvaluatorDone && (
            <span className={`material-symbols-outlined text-[20px] ${evaluatorStatus === 'APPROVED' ? 'text-green-500' : 'text-orange-500'}`} style={{fontVariationSettings: "'FILL' 1"}}>
              {evaluatorStatus === 'APPROVED' ? 'task_alt' : 'warning'}
            </span>
          )}
          {isLoading && isPlannerDone && !isEvaluatorDone && (
            <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>
        <p className="font-body-md text-on-surface font-semibold">
          {isEvaluatorDone 
            ? (evaluatorStatus === 'APPROVED' ? t('processing_status.evaluator_pass') : t('processing_status.evaluator_fail'))
            : (isLoading && isPlannerDone && !isEvaluatorDone ? t('processing_status.evaluator_working') : t('processing_status.waiting'))}
        </p>
        <div className={`mt-2 text-[10px] font-bold ${isEvaluatorDone ? (evaluatorStatus === 'APPROVED' ? 'text-green-500' : 'text-orange-500') : 'text-gray-400'}`}>
          {isEvaluatorDone ? (evaluatorStatus === 'APPROVED' ? t('processing_status.success') : t('processing_status.revision_required')) : t('processing_status.pending')}
        </div>
      </div>
    </section>
  );
}
