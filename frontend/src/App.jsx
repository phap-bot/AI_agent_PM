import { useState, useEffect, useRef } from 'react';
import RequirementInputPanel from './components/RequirementInputPanel';
import ProcessingStatusPanel from './components/ProcessingStatusPanel';
import StoryDraftEditor from './components/StoryDraftEditor';
import { executeJiraAction, generateStoriesAsync, getGenerateStatus, previewJiraAction } from './lib/api';
import { normalizeStoryDraft } from './lib/normalizers';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [context, setContext] = useState(null);
  const [storyDraft, setStoryDraft] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [actions, setActions] = useState(null);
  const [actionExecution, setActionExecution] = useState(null);
  const [isPushingJira, setIsPushingJira] = useState(false);

  const [generateJobId, setGenerateJobId] = useState(null);
  const [lastRequirement, setLastRequirement] = useState(null);
  const generatePollingRef = useRef(null);

  useEffect(() => {
    if (!generateJobId || !isLoading) return;
    
    generatePollingRef.current = setInterval(async () => {
      try {
        const status = await getGenerateStatus(generateJobId);
        
        if (status.partial_result?.context) setContext(status.partial_result.context);
        if (status.partial_result?.story) setStoryDraft(normalizeStoryDraft(status.partial_result.story, ""));
        
        if (status.status === 'completed') {
          clearInterval(generatePollingRef.current);
          setGenerateJobId(null);
          setIsLoading(false);
          const finalResult = status.result;
          if (finalResult) {
             setContext(finalResult.context);
             setStoryDraft(normalizeStoryDraft(finalResult.story, finalResult.story?.requirement || ""));
             setEvaluation(finalResult.evaluation);
             setActions(finalResult.actions);
          }
        } else if (status.status === 'failed') {
          clearInterval(generatePollingRef.current);
          setGenerateJobId(null);
          setIsLoading(false);
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

  const handleGenerate = async (requestPayload) => {
    if (lastRequirement === requestPayload.requirement) {
      alert("Yêu cầu này đã được phân tích. Vui lòng thay đổi nội dung yêu cầu nếu bạn muốn chạy lại!");
      return;
    }
    
    setLastRequirement(requestPayload.requirement);
    setIsLoading(true);
    setError(null);
    setContext(null);
    setStoryDraft(null);
    setEvaluation(null);
    setActions(null);
    setActionExecution(null);
    try {
      const response = await generateStoriesAsync(requestPayload);
      setGenerateJobId(response.job_id);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const handlePreviewJira = async () => {
    if (!storyDraft || !evaluation) return;
    try {
      const newActions = await previewJiraAction({
        story: storyDraft,
        evaluation: evaluation,
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
      });
      setActionExecution(result);
    } catch (err) {
      alert(`Jira Execute Error: ${err.message}`);
    } finally {
      setIsPushingJira(false);
    }
  };

  return (
    <>
      {/* Top Navigation Bar */}
      <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-margin-page h-16 bg-surface border-b border-outline-variant">
        <div className="flex items-center gap-gutter">
          <span className="text-headline-md font-headline-md font-bold text-primary">AI Scrum Master</span>
          <nav className="hidden md:flex items-center gap-stack-lg ml-stack-lg">
            <a className="text-primary border-b-2 border-primary pb-1 font-label-md text-label-md" href="#">Dashboard</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors font-label-md text-label-md" href="#">Analytics</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors font-label-md text-label-md" href="#">Team</a>
          </nav>
        </div>
        <div className="flex items-center gap-stack-md">
          <button className="bg-primary text-on-primary px-container-padding py-unit rounded-lg font-label-md text-label-md hover:opacity-80 transition-all active:scale-95">Create Sprint</button>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer">notifications</span>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer">help</span>
          <div className="w-8 h-8 rounded-full bg-surface-container-high overflow-hidden border border-outline-variant">
            <img alt="User Profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYLpMm5rS4oPHKfptYorn3ApjUs8EZPpCiEzO6kWs7aHZGTK176msotL21zBJVMhIgNI-1QVAxie2jLek8BtYiteof08JuddF16FyFtG5Ry6qDpT-e69yiO3cZ3I5Pvj-EAmMkiy8tdPP8f94I3ml1VchqTIWNTSMNiTN1mRlS1L3LPq_jv7XLjRE3omju28JBSAsCVWHKPFmU-Hp5RcY1BBDtczB7dUta3AtL_4LDrEBxkoK5XJRhcyw3bp-tSursPTXAw2J0Yys" />
          </div>
        </div>
      </header>

      {/* Side Navigation Bar */}
      <aside className="fixed left-0 top-16 h-[calc(100vh-64px)] w-64 bg-surface-container-low border-r border-outline-variant flex flex-col p-stack-md z-40">
        <div className="flex items-center gap-stack-sm mb-stack-lg p-stack-sm">
          <div className="w-10 h-10 rounded bg-primary-container flex items-center justify-center text-on-primary-container">
            <span className="material-symbols-outlined" style={{fontVariationSettings: "'FILL' 1"}}>folder_open</span>
          </div>
          <div>
            <p className="font-headline-sm text-headline-sm font-extrabold text-primary">SmartLib</p>
            <p className="font-label-md text-label-md text-on-surface-variant">Sprint 14</p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto sidebar-scroll space-y-unit">
          <p className="text-[10px] uppercase tracking-wider font-bold text-outline px-stack-sm mb-unit">Main</p>
          <a className="flex items-center gap-stack-sm p-stack-sm bg-secondary-container text-on-secondary-container rounded-lg font-label-md text-label-md" href="#">
            <span className="material-symbols-outlined">folder_open</span> Dự án
          </a>
          <a className="flex items-center gap-stack-sm p-stack-sm text-on-surface-variant hover:bg-surface-container-high rounded-lg font-label-md text-label-md" href="#">
            <span className="material-symbols-outlined">skateboarding</span> Sprint
          </a>
          <p className="text-[10px] uppercase tracking-wider font-bold text-outline px-stack-sm mt-stack-md mb-unit">Settings</p>
          <div className="flex items-center justify-between p-stack-sm text-on-surface-variant hover:bg-surface-container-high rounded-lg font-label-md text-label-md cursor-pointer">
            <div className="flex items-center gap-stack-sm">
              <span className="material-symbols-outlined">settings_suggest</span> Cấu hình Jira
            </div>
            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>
          </div>
          <div className="flex items-center justify-between p-stack-sm text-on-surface-variant hover:bg-surface-container-high rounded-lg font-label-md text-label-md cursor-pointer">
            <div className="flex items-center gap-stack-sm">
              <span className="material-symbols-outlined">hub</span> Cấu hình Slack
            </div>
            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>
          </div>
          <p className="text-[10px] uppercase tracking-wider font-bold text-outline px-stack-sm mt-stack-md mb-unit">History</p>
          <div className="px-stack-sm space-y-stack-sm">
            <div className="p-stack-sm bg-surface rounded border border-outline-variant">
              <p className="text-label-md font-label-md truncate">Tính năng Login (Đã push)</p>
              <p className="text-[10px] text-outline">2 hours ago</p>
            </div>
            <div className="p-stack-sm bg-surface rounded border border-outline-variant">
              <p className="text-label-md font-label-md truncate">Báo cáo Excel (Đã push)</p>
              <p className="text-[10px] text-outline">Yesterday</p>
            </div>
          </div>
        </nav>
        <div className="mt-auto border-t border-outline-variant pt-stack-md">
          <a className="flex items-center gap-stack-sm p-stack-sm text-on-surface-variant hover:bg-surface-container-high rounded-lg font-label-md text-label-md" href="#">
            <span className="material-symbols-outlined">help</span> Help
          </a>
          <a className="flex items-center gap-stack-sm p-stack-sm text-error hover:bg-error-container rounded-lg font-label-md text-label-md" href="#">
            <span className="material-symbols-outlined">logout</span> Logout
          </a>
        </div>
      </aside>

      {/* Main Content Panel */}
      <main className="ml-64 mt-16 p-margin-page min-h-[calc(100vh-64px)] max-w-5xl mx-auto">
        <div className="space-y-stack-lg">
          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              <strong>Error:</strong> {error}
            </div>
          )}

          <RequirementInputPanel onSubmit={handleGenerate} isLoading={isLoading} />
          
          <ProcessingStatusPanel 
            isLoading={isLoading} 
            context={context} 
            storyDraft={storyDraft} 
            evaluation={evaluation} 
          />
          
          {(storyDraft || evaluation) && (
            <StoryDraftEditor 
              draft={storyDraft} 
              evaluation={evaluation}
              actions={actions}
              actionExecution={actionExecution}
              isPushingJira={isPushingJira}
              onChange={setStoryDraft}
              onPreviewJira={handlePreviewJira}
              onPushToJira={handlePushToJira}
            />
          )}
        </div>
        
        {/* Decorative Insight Component */}
        <div className="mt-stack-lg p-container-padding bg-gradient-to-r from-primary-container/5 to-secondary-container/5 rounded-2xl border border-dashed border-primary-container/30 flex items-center gap-stack-lg relative overflow-hidden">
          <div className="absolute -right-8 -bottom-8 w-32 h-32 bg-primary/5 rounded-full blur-3xl"></div>
          <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-lg border border-white shrink-0">
            <span className="material-symbols-outlined text-primary text-[28px]" style={{fontVariationSettings: "'FILL' 1"}}>auto_awesome</span>
          </div>
          <div>
            <p className="font-headline-sm text-headline-sm text-primary mb-1">AI Insight Component</p>
            <p className="text-body-md text-on-surface-variant leading-relaxed">
              Dựa trên lịch sử Sprint 13, tôi đề xuất ưu tiên task Export này vì stakeholder 'Phòng Nhân sự' đang cần báo cáo vào cuối tuần.
            </p>
          </div>
        </div>
      </main>
    </>
  );
}

export default App;
