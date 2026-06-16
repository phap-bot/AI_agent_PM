import { useState, useRef, useEffect } from 'react';
import StoryDraftEditor from './StoryDraftEditor';
import { generateStoriesAsync, getGenerateStatus, previewJiraAction, executeJiraAction } from '../lib/api';
import { normalizeStoryDraft } from '../lib/normalizers';

export default function StorySplitManagerModal({ 
  splits, 
  onClose, 
  projectId, 
  forcedContextDocs = [] 
}) {
  const [activeSplitId, setActiveSplitId] = useState(null); // Which split is currently being generated or viewed
  
  // States for the generated split draft
  const [isLoading, setIsLoading] = useState(false);
  const [generateJobId, setGenerateJobId] = useState(null);
  const [generationMessage, setGenerationMessage] = useState('');
  const [error, setError] = useState(null);
  
  const [storyDraft, setStoryDraft] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [actions, setActions] = useState(null);
  const [actionExecution, setActionExecution] = useState(null);
  const [isPushingJira, setIsPushingJira] = useState(false);

  const generatePollingRef = useRef(null);

  // Poll for generate status
  useEffect(() => {
    if (!generateJobId || !isLoading) return;
    
    generatePollingRef.current = setInterval(async () => {
      try {
        const status = await getGenerateStatus(generateJobId);
        
        if (status.message) {
          setGenerationMessage(status.message);
        }
        
        if (status.partial_result?.story) {
          setStoryDraft(normalizeStoryDraft(status.partial_result.story, ""));
        }
        
        if (status.status === 'completed') {
          clearInterval(generatePollingRef.current);
          setGenerateJobId(null);
          setIsLoading(false);
          setGenerationMessage('');
          const finalResult = status.result;
          if (finalResult) {
             setStoryDraft(normalizeStoryDraft(finalResult.story, finalResult.story?.requirement || ""));
             setEvaluation(finalResult.evaluation);
             setActions(finalResult.actions);
          }
        } else if (status.status === 'failed') {
          clearInterval(generatePollingRef.current);
          setGenerateJobId(null);
          setIsLoading(false);
          setGenerationMessage('');
          setError(status.message);
        }
      } catch (err) {
         console.error("Polling error:", err);
      }
    }, 2000);

    return () => {
      if (generatePollingRef.current) clearInterval(generatePollingRef.current);
    }
  }, [generateJobId, isLoading]);

  const handleGenerateSplit = async (split) => {
    const splitTitle = typeof split === 'string' ? split : (split.title || split.name || 'Sub-ticket');
    const splitDesc = typeof split === 'string' ? '' : (split.description || split.reason || '');
    const splitText = splitTitle + (splitDesc ? `: ${splitDesc}` : '');
    
    setActiveSplitId(splitTitle);
    setIsLoading(true);
    setGenerationMessage('Đang khởi tạo Agent phân tích Split...');
    setError(null);
    setStoryDraft(null);
    setEvaluation(null);
    setActions(null);
    setActionExecution(null);

    try {
      const response = await generateStoriesAsync({
        requirement: `Tập trung phân tích và viết Story cho tính năng này: ${splitText}`,
        n_results: 5,
        allow_fallback_without_context: true,
        forced_context_docs: forcedContextDocs,
        project_id: projectId || undefined,
      });
      setGenerateJobId(response.job_id);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
      setGenerationMessage('');
    }
  };

  const handlePreviewJira = async () => {
    if (!storyDraft || !evaluation) return;
    try {
      const newActions = await previewJiraAction({
        story: storyDraft,
        evaluation: evaluation,
        project_id: projectId || undefined,
      });
      setActions(prev => ({ ...prev, jira: newActions.jira }));
    } catch (err) {
      alert(`Jira Preview Error: ${err.message}`);
    }
  };

  const handlePushToJira = async () => {
    if (!storyDraft || !evaluation) return;
    setIsPushingJira(true);
    setActionExecution(null);
    try {
      const result = await executeJiraAction({
        story: storyDraft,
        evaluation: evaluation,
        project_id: projectId || undefined,
      });
      setActionExecution(result);
    } catch (err) {
      alert(`Jira Execute Error: ${err.message}`);
    } finally {
      setIsPushingJira(false);
    }
  };

  // Simplistic quick push fallback if needed in future, but for now we focus on AI Generate (Option 2)
  const handleQuickPushSplit = async (split) => {
    // This is optional if user requested Option 1 features mixed in, 
    // but standard Option 2 is just AI generate. Let's stick to AI generate as primary action.
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-surface w-full max-w-6xl max-h-[95vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-outline-variant">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-outline-variant bg-surface-container-low">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary text-[28px]" style={{fontVariationSettings: "'FILL' 1"}}>splitscreen</span>
            <div>
              <h2 className="text-xl font-bold text-primary">Story Split Manager</h2>
              <p className="text-sm text-on-surface-variant">Quản lý và tạo chi tiết cho các ticket con</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-outline-variant/30 text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left Panel: List of splits */}
          <div className="w-1/3 border-r border-outline-variant bg-surface-container-lowest flex flex-col h-full">
            <div className="p-4 border-b border-outline-variant/50">
              <h3 className="font-bold text-label-md uppercase tracking-wider text-outline mb-1">Danh sách Split Đề Xuất</h3>
              <p className="text-xs text-on-surface-variant">Chọn một split để bắt đầu AI Generate</p>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3 sidebar-scroll">
              {splits?.map((split, idx) => {
                const splitTitle = typeof split === 'string' ? split : (split.title || split.name || `Sub-ticket ${idx+1}`);
                const splitDesc = typeof split === 'string' ? '' : (split.description || split.reason || '');
                const isActive = activeSplitId === splitTitle;
                const isCompleted = actionExecution?.jira?.executed && isActive;

                return (
                  <div 
                    key={idx}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isActive 
                        ? 'border-primary bg-primary/5 shadow-md scale-[1.02]' 
                        : 'border-outline-variant/50 bg-white hover:border-primary/50 hover:shadow-sm'
                    }`}
                    onClick={() => {
                      if (!isLoading && !isPushingJira) handleGenerateSplit(split);
                    }}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h4 className={`font-bold text-sm ${isActive ? 'text-primary' : 'text-on-surface'}`}>{splitTitle}</h4>
                      {isCompleted && <span className="material-symbols-outlined text-green-500 text-[18px]">check_circle</span>}
                    </div>
                    {splitDesc && <p className="text-xs text-on-surface-variant line-clamp-3">{splitDesc}</p>}
                    
                    <div className="mt-3 flex gap-2">
                      <button 
                        disabled={isLoading || isPushingJira}
                        className={`text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1 w-full justify-center transition-colors ${
                          isActive && isLoading ? 'bg-primary/20 text-primary animate-pulse' : 
                          'bg-primary text-on-primary hover:opacity-90'
                        }`}
                      >
                        <span className="material-symbols-outlined text-[14px]">
                          {isActive && isLoading ? 'sync' : 'auto_awesome'}
                        </span>
                        {isActive && isLoading ? 'Đang phân tích...' : 'AI Generate'}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Right Panel: Generate Status / Draft Editor */}
          <div className="w-2/3 bg-surface flex flex-col h-full overflow-hidden relative">
            {!activeSplitId ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                <span className="material-symbols-outlined text-[64px] text-outline-variant mb-4" style={{fontVariationSettings: "'wght' 200"}}>touch_app</span>
                <h3 className="text-title-lg font-bold text-on-surface mb-2">Chưa chọn Split nào</h3>
                <p className="text-body-md text-on-surface-variant max-w-sm">
                  Hãy chọn một Split từ danh sách bên trái để AI bắt đầu phân tích và viết Draft chi tiết cho bạn.
                </p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto p-6 sidebar-scroll">
                {/* Loading State */}
                {isLoading && (
                  <div className="bg-primary-container text-on-primary-container p-6 rounded-2xl flex flex-col items-center justify-center min-h-[300px] border border-primary/20">
                    <span className="material-symbols-outlined text-[48px] animate-spin mb-4">progress_activity</span>
                    <h3 className="text-xl font-bold mb-2">AI Đang Phân Tích Split</h3>
                    <p className="text-sm font-medium opacity-80">{generationMessage}</p>
                  </div>
                )}
                
                {/* Error State */}
                {error && (
                  <div className="bg-error-container text-on-error-container p-6 rounded-2xl flex gap-3 items-start border border-error/20">
                    <span className="material-symbols-outlined text-[24px]">error</span>
                    <div>
                      <h3 className="font-bold text-lg mb-1">Lỗi sinh luồng</h3>
                      <p className="text-sm">{error}</p>
                      <button 
                        className="mt-4 px-4 py-2 bg-error text-on-error rounded-lg text-sm font-medium"
                        onClick={() => handleGenerateSplit(activeSplitId)}
                      >
                        Thử lại
                      </button>
                    </div>
                  </div>
                )}

                {/* Draft Editor View */}
                {storyDraft && evaluation && !isLoading && (
                  <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-bold text-primary">Bản Nháp Cho: {activeSplitId}</h3>
                      <span className="bg-green-100 text-green-700 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">check_circle</span>
                        Tạo thành công
                      </span>
                    </div>
                    
                    {/* We reuse the StoryDraftEditor, but turn off split suggestions to avoid infinite loops */}
                    <div className="pointer-events-auto">
                      <StoryDraftEditor
                        draft={storyDraft}
                        evaluation={evaluation}
                        actions={actions}
                        actionExecution={actionExecution}
                        isPushingJira={isPushingJira}
                        isRegenerating={isLoading}
                        onChange={setStoryDraft}
                        onPreviewJira={handlePreviewJira}
                        onPushToJira={handlePushToJira}
                        projectId={projectId}
                        onSelectSplit={() => {}} // Disable inner splitting
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
