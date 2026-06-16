export default function ProcessingStatusPanel({ isLoading, context, storyDraft, evaluation }) {
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
    <section className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
      {/* Researcher Card */}
      <div className={`bg-white/80 backdrop-blur-sm rounded-xl border border-outline-variant p-stack-md border-l-4 shadow-sm transition-all hover:shadow-md ${isResearcherDone ? 'border-l-blue-500' : 'border-l-gray-300'}`}>
        <div className="flex items-center justify-between mb-unit">
          <span className="text-label-md font-label-md text-outline uppercase tracking-wider">Researcher</span>
          {isResearcherDone && !isResearcherEmpty && (
             <span className="material-symbols-outlined text-blue-500 text-[20px]" style={{fontVariationSettings: "'FILL' 1"}}>verified</span>
          )}
          {isLoading && !isResearcherDone && (
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>
        {isResearcherDone ? (
          isResearcherEmpty ? (
            <p className="font-body-md text-on-surface font-semibold">Không tìm thấy context</p>
          ) : (
            <div className="font-body-sm text-on-surface">
              <div className="font-semibold mb-1">Retrieved Context:</div>
              <ul className="list-decimal pl-4 mb-2 space-y-1">
                {context?.retrieved_sources?.map((src, idx) => (
                  <li key={idx} className="text-xs text-gray-700">
                    <span className="font-medium">{src.source} <span className="text-gray-400 font-normal">(Chunk {src.chunk_index !== undefined ? src.chunk_index : '?'})</span></span>
                    <span className="text-gray-500">
                      {' '}– score: {src.score != null ? Number(src.score).toFixed(2) : 'N/A'} 
                      {' '}– {src.score < 0.5 ? 'low relevance' : 'high relevance'}
                    </span>
                  </li>
                ))}
              </ul>
              {context?.warnings?.length > 0 && (
                <div className="text-orange-600 text-xs mt-2 bg-orange-50 p-2 rounded border border-orange-100">
                  <span className="font-bold">Warning:</span> {context.warnings.join(' ')}
                </div>
              )}
            </div>
          )
        ) : (
          <p className="font-body-md text-on-surface font-semibold">
            {isLoading ? 'Đang tìm kiếm context...' : 'Chờ bắt đầu...'}
          </p>
        )}
        <div className={`mt-2 text-[10px] font-bold ${isResearcherDone ? 'text-blue-400' : 'text-gray-400'}`}>
          {isResearcherDone ? 'COMPLETED' : 'PENDING'}
        </div>
      </div>

      {/* Planner Card */}
      <div className={`bg-white/80 backdrop-blur-sm rounded-xl border border-outline-variant p-stack-md border-l-4 relative overflow-hidden shadow-sm transition-all hover:shadow-md ${isPlannerDone ? 'border-l-primary' : (isPlannerWorking ? 'border-l-primary' : 'border-l-gray-300')}`}>
        {isPlannerWorking && <div className="absolute top-0 left-0 w-full h-1 shimmer-bg"></div>}
        <div className="flex items-center justify-between mb-unit">
          <span className="text-label-md font-label-md text-outline uppercase tracking-wider">Planner</span>
          {isPlannerWorking && (
            <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
          )}
          {isPlannerDone && (
             <span className="material-symbols-outlined text-primary text-[20px]" style={{fontVariationSettings: "'FILL' 1"}}>check_circle</span>
          )}
        </div>
        <p className="font-body-md text-on-surface font-semibold">
          {isPlannerDone 
            ? 'Đã viết User Story'
            : (isPlannerWorking ? 'Đang viết User Story...' : 'Chờ bắt đầu...')}
        </p>
        <div className="mt-2 flex gap-1">
          {isPlannerWorking ? (
            <>
              <div className="h-1 bg-primary rounded-full flex-1"></div>
              <div className="h-1 bg-primary/20 rounded-full flex-1"></div>
              <div className="h-1 bg-primary/20 rounded-full flex-1"></div>
            </>
          ) : isPlannerDone ? (
            <div className="mt-2 text-[10px] text-primary font-bold">COMPLETED</div>
          ) : (
            <div className="mt-2 text-[10px] text-gray-400 font-bold">PENDING</div>
          )}
        </div>
      </div>

      {/* Evaluator Card */}
      <div className={`bg-white/80 backdrop-blur-sm rounded-xl border border-outline-variant p-stack-md border-l-4 shadow-sm transition-all hover:shadow-md ${isEvaluatorDone ? (evaluatorStatus === 'APPROVED' ? 'border-l-green-500' : 'border-l-orange-500') : 'border-l-gray-300'}`}>
        <div className="flex items-center justify-between mb-unit">
          <span className="text-label-md font-label-md text-outline uppercase tracking-wider">Evaluator</span>
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
            ? `Đánh giá ${evaluatorStatus === 'APPROVED' ? 'Pass (Score: 5/5)' : 'Cần sửa (Score: thấp)'}`
            : (isLoading && isPlannerDone && !isEvaluatorDone ? 'Đang đánh giá...' : 'Chờ bắt đầu...')}
        </p>
        <div className={`mt-2 text-[10px] font-bold ${isEvaluatorDone ? (evaluatorStatus === 'APPROVED' ? 'text-green-500' : 'text-orange-500') : 'text-gray-400'}`}>
          {isEvaluatorDone ? (evaluatorStatus === 'APPROVED' ? 'SUCCESS' : 'REVISION REQUIRED') : 'PENDING'}
        </div>
      </div>
    </section>
  );
}
