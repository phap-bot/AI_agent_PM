                                                                                                                                                        import { useState, useEffect, useRef } from 'react';
import RequirementInputPanel from './components/RequirementInputPanel';
import ProcessingStatusPanel from './components/ProcessingStatusPanel';
import StoryDraftEditor from './components/StoryDraftEditor';
import StorySplitManagerModal from './components/StorySplitManagerModal';
import { executeAllActions, generateStoriesAsync, getGenerateStatus, previewJiraAction } from './lib/api';
import { normalizeStoryDraft } from './lib/normalizers';
import HistoryPanel from './components/HistoryPanel';
import SprintBoardPanel from './components/SprintBoardPanel';
import JiraConfigPanel from './components/JiraConfigPanel';
import SlackConfigPanel from './components/SlackConfigPanel';
import ProjectDropdown from './components/ProjectDropdown';
import { getProjects, createProject, updateProject, deleteProject } from './lib/api';

function App() {
  const [currentView, setCurrentView] = useState(() => localStorage.getItem('currentView') || 'project');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [context, setContext] = useState(null);
  const [storyDraft, setStoryDraft] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [actions, setActions] = useState(null);
  const [actionExecution, setActionExecution] = useState(null);
  const [isPushingJira, setIsPushingJira] = useState(false);
  const [showSplitModal, setShowSplitModal] = useState(false);
  
  const [sprintName, setSprintName] = useState('Đang tải...');

  const [generateJobId, setGenerateJobId] = useState(null);
  const [generationMessage, setGenerationMessage] = useState('');
  const [lastRequirement, setLastRequirement] = useState(null);
  const [forcedContextDocs, setForcedContextDocs] = useState([]);
  const generatePollingRef = useRef(null);

  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(() => localStorage.getItem('activeProjectId') || '');
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');

  const [showEditProject, setShowEditProject] = useState(false);
  const [editProjectName, setEditProjectName] = useState('');
  const [showDeleteProjectConfirm, setShowDeleteProjectConfirm] = useState(false);

  const [historyItemView, setHistoryItemView] = useState(null);

  useEffect(() => {
    localStorage.setItem('currentView', currentView);
  }, [currentView]);

  useEffect(() => {
    localStorage.setItem('activeProjectId', activeProjectId);
  }, [activeProjectId]);

  useEffect(() => {
    getProjects().then(data => {
      setProjects(data);
      if (data.length > 0) {
        // If no saved ID or saved ID doesn't exist in fetched data, fallback to first project
        const savedId = localStorage.getItem('activeProjectId');
        if (!savedId || !data.some(p => p.id === savedId)) {
          setActiveProjectId(data[0].id);
        }
      }
    }).catch(err => console.error("Failed to load projects", err));
  }, []);

  const clearWorkspace = () => {
    setContext(null);
    setStoryDraft(null);
    setEvaluation(null);
    setActions(null);
    setHistoryItemView(null);
    setLastRequirement(null);
    setCurrentView('project');
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    try {
      const proj = await createProject({ name: newProjectName });
      setProjects([proj, ...projects]);
      setActiveProjectId(proj.id);
      setShowCreateProject(false);
      setNewProjectName('');
      clearWorkspace();
    } catch (err) {
      alert("Error creating project: " + err.message);
    }
  };

  const handleUpdateProject = async () => {
    if (!editProjectName.trim() || !activeProjectId) return;
    try {
      const proj = await updateProject(activeProjectId, { name: editProjectName });
      setProjects(projects.map(p => p.id === activeProjectId ? proj : p));
      setShowEditProject(false);
      setEditProjectName('');
    } catch (err) {
      alert("Error updating project: " + err.message);
    }
  };

  const handleDeleteProject = async () => {
    if (!activeProjectId) return;
    try {
      await deleteProject(activeProjectId);
      const newProjects = projects.filter(p => p.id !== activeProjectId);
      setProjects(newProjects);
      setActiveProjectId(newProjects.length > 0 ? newProjects[0].id : '');
      setShowDeleteProjectConfirm(false);
      
      // Clear current states just in case
      setContext(null);
      setStoryDraft(null);
      setEvaluation(null);
      setActions(null);
      setHistoryItemView(null);
    } catch (err) {
      alert("Error deleting project: " + err.message);
    }
  };

  useEffect(() => {
    if (!generateJobId || !isLoading) return;
    
    generatePollingRef.current = setInterval(async () => {
      try {
        const status = await getGenerateStatus(generateJobId);
        
        if (status.message) {
          setGenerationMessage(status.message);
        }
        
        if (status.partial_result?.context) setContext(status.partial_result.context);
        if (status.partial_result?.story) setStoryDraft(normalizeStoryDraft(status.partial_result.story, ""));
        
        if (status.status === 'completed') {
          clearInterval(generatePollingRef.current);
          setGenerateJobId(null);
          setIsLoading(false);
          setGenerationMessage('');
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

  useEffect(() => {
    async function loadSprintName() {
      try {
        const data = await fetchSprintBoard();
        if (data && data.sprint && data.sprint.name) {
          setSprintName(data.sprint.name);
        } else {
          setSprintName('Backlog');
        }
      } catch (err) {
        setSprintName('Backlog');
      }
    }
    loadSprintName();
  }, []);

  const handleGenerate = async (requestPayload) => {
    if (lastRequirement === requestPayload.requirement) {
      alert("Yêu cầu này đã được phân tích. Vui lòng thay đổi nội dung yêu cầu nếu bạn muốn chạy lại!");
      return;
    }
    
    // Store forced_context_docs for potential re-runs via clarification
    const docs = requestPayload.forced_context_docs || [];
    setForcedContextDocs(docs);

    setLastRequirement(requestPayload.requirement);
    setIsLoading(true);
    setGenerationMessage('Đang khởi tạo Agent...');
    setError(null);
    setContext(null);
    setStoryDraft(null);
    setEvaluation(null);
    setActions(null);
    setActionExecution(null);
    try {
      const response = await generateStoriesAsync({
        ...requestPayload,
        forced_context_docs: docs,
        project_id: activeProjectId || undefined,
      });
      setGenerateJobId(response.job_id);
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
      setGenerationMessage('');
    }
  };

  // Called when user sends a clarification response via the AI chat
  const handleClarificationSubmit = async (clarificationText) => {
    if (!clarificationText.trim() || !lastRequirement) return;

    const enrichedRequirement = `${lastRequirement}\n\n[Clarification from user]: ${clarificationText}`;
    
    // Reset lastRequirement so the duplicate check doesn't block
    setLastRequirement(null);

    handleGenerate({
      requirement: enrichedRequirement,
      n_results: 5,
      allow_fallback_without_context: true,
      forced_context_docs: forcedContextDocs,
    });
  };

  const handlePreviewJira = async () => {
    if (!storyDraft || !evaluation) return;
    try {
      const newActions = await previewJiraAction({
        story: storyDraft,
        evaluation: evaluation,
        project_id: activeProjectId || undefined,
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
      const result = await executeAllActions({
        story: storyDraft,
        evaluation: evaluation,
        project_id: activeProjectId || undefined,
      });
      setActionExecution(result);
    } catch (err) {
      alert(`Execute Error: ${err.message}`);
    } finally {
      setIsPushingJira(false);
    }
  };

  const handleReset = () => {
    setLastRequirement(null);
    setContext(null);
    setStoryDraft(null);
    setEvaluation(null);
    setActions(null);
    setActionExecution(null);
    setError(null);
    setGenerationMessage('');
  };

  const displayContext = historyItemView?.result?.context || context;
  const displayStoryDraft = historyItemView ? normalizeStoryDraft(historyItemView.result?.story, "") : storyDraft;
  const displayEvaluation = historyItemView?.result?.evaluation || evaluation;
  const displayActions = historyItemView?.result?.actions || actions;

  return (
    <>
      {/* Top Navigation Bar */}
      <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-margin-page h-16 bg-surface border-b border-outline-variant">
        <div className="flex items-center gap-gutter">
          <span className="text-headline-md font-headline-md font-bold text-primary">AI Scrum Master</span>
          <nav className="hidden md:flex items-center gap-stack-lg ml-stack-lg">
            <a className="text-primary border-b-2 border-primary pb-1 font-label-md text-label-md">Dashboard</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors font-label-md text-label-md">Analytics</a>
            <a className="text-on-surface-variant hover:text-primary transition-colors font-label-md text-label-md">Team</a>
          </nav>
        </div>
        <div className="flex items-center gap-stack-md">
          <div className="relative flex items-center gap-2">
            <span className="text-sm font-medium text-on-surface-variant">Dự án:</span>
            <ProjectDropdown
              projects={projects}
              activeProjectId={activeProjectId}
              onChange={(newId) => {
                setActiveProjectId(newId);
                clearWorkspace();
              }}
              onCreateNew={() => setShowCreateProject(true)}
              onEdit={() => {
                const proj = projects.find(p => p.id === activeProjectId);
                setEditProjectName(proj ? proj.name : '');
                setShowEditProject(true);
              }}
              onDelete={() => setShowDeleteProjectConfirm(true)}
            />
          </div>

          <button className="bg-primary text-on-primary px-container-padding py-unit rounded-lg font-label-md text-label-md hover:opacity-80 transition-all active:scale-95">Create Sprint</button>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer">notifications</span>
          <span className="material-symbols-outlined text-on-surface-variant cursor-pointer">help</span>
          <div className="w-8 h-8 rounded-full bg-surface-container-high overflow-hidden border border-outline-variant">
            <img alt="User Profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYLpMm5rS4oPHKfptYorn3ApjUs8EZPpCiEzO6kWs7aHZGTK176msotL21zBJVMhIgNI-1QVAxie2jLek8BtYiteof08JuddF16FyFtG5Ry6qDpT-e69yiO3cZ3I5Pvj-EAmMkiy8tdPP8f94I3ml1VchqTIWNTSMNiTN1mRlS1L3LPq_jv7XLjRE3omju28JBSAsCVWHKPFmU-Hp5RcY1BBDtczB7dUta3AtL_4LDrEBxkoK5XJRhcyw3bp-tSursPTXAw2J0Yys" />
          </div>
        </div>
      </header>

      {/* Create Project Modal */}
      {showCreateProject && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center">
          <div className="bg-surface rounded-xl p-6 w-[400px] shadow-xl border border-outline-variant">
            <h3 className="text-xl font-bold mb-4">Tạo dự án mới</h3>
            <input 
              autoFocus
              className="w-full px-3 py-2 border border-outline-variant rounded-lg mb-4 focus:outline-none focus:border-primary"
              placeholder="Nhập tên dự án..."
              value={newProjectName}
              onChange={e => setNewProjectName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreateProject()}
            />
            <div className="flex justify-end gap-2">
              <button 
                className="px-4 py-2 rounded-lg font-medium text-on-surface-variant hover:bg-surface-container-high"
                onClick={() => setShowCreateProject(false)}
              >
                Hủy
              </button>
              <button 
                className="px-4 py-2 bg-primary text-on-primary rounded-lg font-medium"
                onClick={handleCreateProject}
              >
                Tạo mới
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Project Modal */}
      {showEditProject && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center">
          <div className="bg-surface rounded-xl p-6 w-[400px] shadow-xl border border-outline-variant">
            <h3 className="text-xl font-bold mb-4">Đổi tên dự án</h3>
            <input 
              autoFocus
              className="w-full px-3 py-2 border border-outline-variant rounded-lg mb-4 focus:outline-none focus:border-primary"
              placeholder="Nhập tên mới..."
              value={editProjectName}
              onChange={e => setEditProjectName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleUpdateProject()}
            />
            <div className="flex justify-end gap-2">
              <button 
                className="px-4 py-2 rounded-lg font-medium text-on-surface-variant hover:bg-surface-container-high"
                onClick={() => setShowEditProject(false)}
              >
                Hủy
              </button>
              <button 
                className="px-4 py-2 bg-primary text-on-primary rounded-lg font-medium"
                onClick={handleUpdateProject}
              >
                Lưu thay đổi
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Project Confirm Modal */}
      {showDeleteProjectConfirm && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center">
          <div className="bg-surface rounded-xl p-6 w-[400px] shadow-xl border border-outline-variant">
            <h3 className="text-xl font-bold mb-2 text-error">Xóa dự án</h3>
            <p className="text-on-surface-variant mb-6 text-sm">
              Bạn có chắc chắn muốn xóa dự án này? Thao tác này không thể hoàn tác.
            </p>
            <div className="flex justify-end gap-2">
              <button 
                className="px-4 py-2 rounded-lg font-medium text-on-surface-variant hover:bg-surface-container-high"
                onClick={() => setShowDeleteProjectConfirm(false)}
              >
                Hủy
              </button>
              <button 
                className="px-4 py-2 bg-error text-on-error rounded-lg font-medium hover:opacity-90"
                onClick={handleDeleteProject}
              >
                Xóa vĩnh viễn
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Side Navigation Bar */}
      <aside className="fixed left-0 top-16 h-[calc(100vh-64px)] w-64 bg-surface-container-low border-r border-outline-variant flex flex-col p-stack-md z-40">
        <div className="flex items-center gap-stack-sm mb-stack-lg p-stack-sm">
          <div className="w-10 h-10 rounded bg-primary-container flex items-center justify-center text-on-primary-container">
            <span className="material-symbols-outlined" style={{fontVariationSettings: "'FILL' 1"}}>folder_open</span>
          </div>
          <div>
            <p className="font-headline-sm text-headline-sm font-extrabold text-primary">SmartLib</p>
            <p className="font-label-md text-label-md text-on-surface-variant">{sprintName}</p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto sidebar-scroll space-y-unit">
          <p className="text-[10px] uppercase tracking-wider font-bold text-outline px-stack-sm mb-unit">Main</p>
          <a 
            className={`flex items-center gap-stack-sm p-stack-sm rounded-lg font-label-md text-label-md cursor-pointer transition-colors ${currentView === 'project' ? 'bg-secondary-container text-on-secondary-container' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
            onClick={() => setCurrentView('project')}
          >
            <span className="material-symbols-outlined">folder_open</span> Dự án
          </a>
          <a 
            className={`flex items-center gap-stack-sm p-stack-sm rounded-lg font-label-md text-label-md cursor-pointer transition-colors ${currentView === 'sprint' ? 'bg-secondary-container text-on-secondary-container' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
            onClick={() => setCurrentView('sprint')}
          >
            <span className="material-symbols-outlined">skateboarding</span> Sprint
          </a>
          <p className="text-[10px] uppercase tracking-wider font-bold text-outline px-stack-sm mt-stack-md mb-unit">Settings</p>
          <div 
            className={`flex items-center justify-between p-stack-sm rounded-lg font-label-md text-label-md cursor-pointer transition-colors ${currentView === 'config_jira' ? 'bg-secondary-container text-on-secondary-container' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
            onClick={() => setCurrentView('config_jira')}
          >
            <div className="flex items-center gap-stack-sm">
              <span className="material-symbols-outlined">settings_suggest</span> Cấu hình Jira
            </div>
          </div>
          <div 
            className={`flex items-center justify-between p-stack-sm rounded-lg font-label-md text-label-md cursor-pointer transition-colors ${currentView === 'config_slack' ? 'bg-secondary-container text-on-secondary-container' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
            onClick={() => setCurrentView('config_slack')}
          >
            <div className="flex items-center gap-stack-sm">
              <span className="material-symbols-outlined">hub</span> Cấu hình Slack
            </div>
          </div>
          <div className="flex justify-between items-center px-stack-sm mt-stack-md mb-unit">
            <p className="text-[10px] uppercase tracking-wider font-bold text-outline">History</p>
            <button 
              onClick={() => setCurrentView('history')}
              className={`text-[10px] uppercase font-bold hover:underline ${currentView === 'history' ? 'text-primary' : 'text-outline hover:text-primary'}`}
            >
              Xem tất cả
            </button>
          </div>
          <div className="px-stack-sm space-y-stack-sm">
            <div 
              onClick={() => setCurrentView('history')}
              className="p-stack-sm bg-surface rounded border border-outline-variant cursor-pointer hover:border-primary transition-colors"
            >
              <p className="text-label-md font-label-md truncate">Nhấn để xem kho lưu trữ</p>
              <p className="text-[10px] text-outline">Tất cả lịch sử yêu cầu</p>
            </div>
          </div>
        </nav>
        <div className="mt-auto border-t border-outline-variant pt-stack-md">
          <a className="flex items-center gap-stack-sm p-stack-sm text-on-surface-variant hover:bg-surface-container-high rounded-lg font-label-md text-label-md">
            <span className="material-symbols-outlined">help</span> Help
          </a>
          <a className="flex items-center gap-stack-sm p-stack-sm text-error hover:bg-error-container rounded-lg font-label-md text-label-md">
            <span className="material-symbols-outlined">logout</span> Logout
          </a>
        </div>
      </aside>

      <main className="ml-64 mt-16 p-margin-page min-h-[calc(100vh-64px)]">
        <div style={{ display: currentView === 'project' ? 'block' : 'none' }}>
            <div className="space-y-stack-lg">
              {historyItemView && (
                <div className="bg-primary/10 text-primary p-4 rounded-xl flex items-center justify-between border border-primary/20">
                  <div>
                    <h3 className="font-bold">Đang xem lịch sử</h3>
                    <p className="text-sm">Bạn đang xem một bản phân tích từ lịch sử. Phiên làm việc hiện tại của bạn đã được ẩn đi.</p>
                  </div>
                  <button 
                    onClick={() => setHistoryItemView(null)}
                    className="px-4 py-2 bg-primary text-on-primary rounded-lg font-medium text-sm hover:opacity-90 transition-opacity"
                  >
                    Quay lại dự án đang chạy
                  </button>
                </div>
              )}
              <div className="space-y-stack-lg" style={{ display: historyItemView ? 'none' : 'block' }}>
                <RequirementInputPanel 
                  onSubmit={handleGenerate} 
                  isLoading={isLoading} 
                  generationMessage={generationMessage}
                  projectId={activeProjectId} 
                />
                {isLoading && <ProcessingStatusPanel isLoading={isLoading} context={displayContext} storyDraft={displayStoryDraft} evaluation={displayEvaluation} />}
                {error && (
                  <div className="bg-error-container text-on-error-container p-4 rounded-xl shadow-sm border border-error/20 flex gap-3">
                    <span className="material-symbols-outlined text-error">error</span>
                    <div>
                      <h3 className="font-bold">Lỗi sinh luồng</h3>
                      <p className="text-sm">{error}</p>
                    </div>
                  </div>
                )}
              </div>
              {displayStoryDraft && displayEvaluation && (
                <StoryDraftEditor
                  draft={displayStoryDraft}
                  evaluation={displayEvaluation}
                  actions={displayActions}
                  actionExecution={actionExecution}
                  isPushingJira={isPushingJira}
                  isRegenerating={isLoading}
                  onChange={setStoryDraft}
                  onPreviewJira={handlePreviewJira}
                  onPushToJira={handlePushToJira}
                  onProvideClarification={handleClarificationSubmit}
                  onSelectSplit={(splitText) => {
                    handleGenerate({
                      requirement: `Tập trung phân tích và viết Story cho tính năng này: ${splitText}`,
                      n_results: 5,
                      allow_fallback_without_context: true,
                      forced_context_docs: forcedContextDocs,
                    });
                  }}
                  onOpenSplitManager={() => setShowSplitModal(true)}
                  onReset={handleReset}
                  projectId={activeProjectId}
                />
              )}
            </div>
        </div>

        <div style={{ display: currentView === 'history' ? 'block' : 'none' }}>
          <HistoryPanel 
            isActive={currentView === 'history'} 
            projectId={activeProjectId}
            onSelectHistory={(item) => {
              setHistoryItemView(item);
              setCurrentView('project');
            }}
          />
        </div>

        <div style={{ display: currentView === 'sprint' ? 'block' : 'none' }}>
          <SprintBoardPanel isActive={currentView === 'sprint'} projectId={activeProjectId} />
        </div>

        <div style={{ display: currentView === 'config_jira' ? 'block' : 'none' }}>
          <JiraConfigPanel projectId={activeProjectId} />
        </div>

        <div style={{ display: currentView === 'config_slack' ? 'block' : 'none' }}>
          <SlackConfigPanel projectId={activeProjectId} />
        </div>
      </main>

      {/* Story Split Manager Modal */}
      {showSplitModal && displayStoryDraft?.story_splits && (
        <StorySplitManagerModal 
          splits={displayStoryDraft.story_splits}
          projectId={activeProjectId}
          forcedContextDocs={forcedContextDocs}
          onClose={() => setShowSplitModal(false)}
        />
      )}
    </>
  );
}

export default App;
