import { useState, useEffect, useRef } from 'react';
import RequirementInputPanel from './components/RequirementInputPanel';
import ProcessingStatusPanel from './components/ProcessingStatusPanel';
import StoryDraftEditor from './components/StoryDraftEditor';
import StorySplitManagerModal from './components/StorySplitManagerModal';
import { createSprint, executeAllActions, fetchSprintBoard, generateStoriesAsync, getGenerateStatus, previewJiraAction, sendGenerateCancelBeacon } from './lib/api';
import { normalizeStoryDraft } from './lib/normalizers';
import HistoryPanel from './components/HistoryPanel';
import SprintBoardPanel from './components/SprintBoardPanel';
import JiraConfigPanel from './components/JiraConfigPanel';
import SlackConfigPanel from './components/SlackConfigPanel';
import GithubConfigPanel from './components/GithubConfigPanel';
import ProjectDropdown from './components/ProjectDropdown';
import { getProjects, createProject, updateProject, deleteProject } from './lib/api';
import DashboardPanel from './components/DashboardPanel';
import AnalyticsPanel from './components/AnalyticsPanel';
import TeamPanel from './components/TeamPanel';
import { useTranslation } from 'react-i18next';
import LanguageSwitcher from './components/LanguageSwitcher';
import LandingPage from './components/LandingPage';

const GENERATE_POLL_INITIAL_MS = 3000;
const GENERATE_POLL_MAX_MS = 10000;
const APP_CURRENT_VIEW_KEY = 'pmAgentCurrentView';
const APP_VIEWS = new Set([
  'dashboard',
  'analytics',
  'team',
  'project',
  'sprint',
  'config_jira',
  'config_slack',
  'config_github',
  'history',
]);

function getStoredCurrentView() {
  const storedView = localStorage.getItem(APP_CURRENT_VIEW_KEY);
  return APP_VIEWS.has(storedView) ? storedView : 'dashboard';
}

function App() {
  const { t } = useTranslation();
  const [showLanding, setShowLanding] = useState(() => localStorage.getItem('skipLanding') !== 'true');
  const [currentView, setCurrentView] = useState(getStoredCurrentView);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [context, setContext] = useState(null);
  const [storyDraft, setStoryDraft] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [actions, setActions] = useState(null);
  const [actionExecution, setActionExecution] = useState(null);
  const [isPushingJira, setIsPushingJira] = useState(false);
  const [showSplitModal, setShowSplitModal] = useState(false);
  
  const [sprintName, setSprintName] = useState(t('common.loading'));

  const [generateJobId, setGenerateJobId] = useState(null);
  const [generationMessage, setGenerationMessage] = useState('');
  const [lastRequirement, setLastRequirement] = useState(null);
  const [forcedContextDocs, setForcedContextDocs] = useState([]);
  const generatePollingRef = useRef(null);
  const generatePollDelayRef = useRef(GENERATE_POLL_INITIAL_MS);
  const generateJobIdRef = useRef(null);

  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(() => localStorage.getItem('activeProjectId') || '');
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');

  const [showEditProject, setShowEditProject] = useState(false);
  const [editProjectName, setEditProjectName] = useState('');
  const [showDeleteProjectConfirm, setShowDeleteProjectConfirm] = useState(false);

  const [historyItemView, setHistoryItemView] = useState(null);

  const handleEnterApp = () => {
    localStorage.setItem('skipLanding', 'true');
    setShowLanding(false);
    setCurrentView('project');
  };

  const handleOpenLanding = () => {
    localStorage.removeItem('skipLanding');
    setShowLanding(true);
  };

  useEffect(() => {
    localStorage.setItem('activeProjectId', activeProjectId);
  }, [activeProjectId]);

  useEffect(() => {
    if (APP_VIEWS.has(currentView)) {
      localStorage.setItem(APP_CURRENT_VIEW_KEY, currentView);
    }
  }, [currentView]);

  useEffect(() => {
    generateJobIdRef.current = generateJobId;
  }, [generateJobId]);

  useEffect(() => {
    const cancelActiveGenerateJob = () => {
      if (generateJobIdRef.current) {
        sendGenerateCancelBeacon(generateJobIdRef.current);
      }
    };

    window.addEventListener('pagehide', cancelActiveGenerateJob);
    window.addEventListener('beforeunload', cancelActiveGenerateJob);

    return () => {
      window.removeEventListener('pagehide', cancelActiveGenerateJob);
      window.removeEventListener('beforeunload', cancelActiveGenerateJob);
    };
  }, []);

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
      alert(`${t('app.project_modal.create_error')}${err.message}`);
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
      alert(`${t('app.project_modal.update_error')}${err.message}`);
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
      alert(`${t('app.project_modal.delete_error')}${err.message}`);
    }
  };

  useEffect(() => {
    if (!generateJobId || !isLoading) return;
    let cancelled = false;
    generatePollDelayRef.current = GENERATE_POLL_INITIAL_MS;
    
    const clearGeneratePoll = () => {
      if (generatePollingRef.current) {
        clearTimeout(generatePollingRef.current);
        generatePollingRef.current = null;
      }
    };

    const finishPolling = () => {
      cancelled = true;
      clearGeneratePoll();
      generateJobIdRef.current = null;
      setGenerateJobId(null);
      setIsLoading(false);
      setGenerationMessage('');
    };

    const scheduleNextPoll = () => {
      if (cancelled) return;
      generatePollingRef.current = setTimeout(pollGenerateStatus, generatePollDelayRef.current);
      generatePollDelayRef.current = Math.min(generatePollDelayRef.current + 1000, GENERATE_POLL_MAX_MS);
    };

    async function pollGenerateStatus() {
      try {
        const status = await getGenerateStatus(generateJobId);
        
        if (status.message) {
          setGenerationMessage(status.message);
        }
        
        if (status.partial_result?.context) setContext(status.partial_result.context);
        if (status.partial_result?.story) setStoryDraft(normalizeStoryDraft(status.partial_result.story, ""));
        
        if (status.status === 'completed') {
          finishPolling();
          const finalResult = status.result;
          if (finalResult) {
             setContext(finalResult.context);
             setStoryDraft(normalizeStoryDraft(finalResult.story, finalResult.story?.requirement || ""));
             setEvaluation(finalResult.evaluation);
             setActions(finalResult.actions);
          }
        } else if (status.status === 'cancelled') {
          finishPolling();
          setGenerationMessage('');
        } else if (status.status === 'failed') {
          finishPolling();
          setError(status.message);
        } else {
          scheduleNextPoll();
        }
      } catch (err) {
         console.error("Polling error:", err);
         scheduleNextPoll();
      }
    }

    scheduleNextPoll();

    return () => {
      cancelled = true;
      clearGeneratePoll();
    }
  }, [generateJobId, isLoading]);

  useEffect(() => {
    async function loadSprintName() {
      try {
        const data = await fetchSprintBoard(activeProjectId || undefined);
        if (data && data.sprint && data.sprint.name) {
          setSprintName(data.sprint.name);
        } else {
          setSprintName(t('sprint_board.backlog'));
        }
      } catch (err) {
        setSprintName(t('sprint_board.backlog'));
      }
    }
    loadSprintName();
  }, [activeProjectId, t]);

  const handleGenerate = async (requestPayload) => {
    if (lastRequirement === requestPayload.requirement) {
      alert(t('app.requirement.duplicate_alert'));
      return;
    }
    
    // Store forced_context_docs for potential re-runs via clarification
    const docs = requestPayload.forced_context_docs || [];
    setForcedContextDocs(docs);

    setLastRequirement(requestPayload.requirement);
    setIsLoading(true);
    setGenerationMessage(t('app.requirement.initializing_agent'));
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
      alert(`${t('app.actions.jira_preview_error')}${err.message}`);
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
      alert(`${t('app.actions.execute_error')}${err.message}`);
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
  const topNavClass = (view) => `cursor-pointer rounded-full px-3.5 py-1.5 font-label-md text-label-md transition-all ${
    currentView === view ? 'bg-slate-200 text-slate-950 shadow-sm' : 'text-slate-700 hover:bg-slate-100 hover:text-slate-950'
  }`;
  const sideNavClass = (view) => `group flex min-h-11 w-full cursor-pointer items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-sm font-bold transition-all ${
    currentView === view
      ? 'bg-slate-900 text-white shadow-sm shadow-slate-950/10'
      : 'text-slate-800 hover:bg-slate-100 hover:text-slate-950'
  }`;
  const mobileNavClass = (view) => `flex flex-1 flex-col items-center justify-center gap-1 rounded-2xl px-2 py-2 text-[10px] font-black transition ${
    currentView === view ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-700'
  }`;

  if (showLanding) {
    return <LandingPage onEnterApp={handleEnterApp} />;
  }

  return (
    <>
      {/* Top Navigation Bar */}
      <header className="fixed left-0 top-0 z-50 flex h-14 w-full items-center justify-between gap-3 border-b border-slate-200 bg-white/90 px-3 shadow-sm backdrop-blur-xl sm:px-5">
        <div className="flex items-center gap-gutter">
          <button
            type="button"
            onClick={handleOpenLanding}
            className="flex min-h-11 items-center gap-3 rounded-2xl px-1.5 pr-3 text-left transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2"
            aria-label="Open PM Agent landing page"
            title="Open PM Agent landing page"
          >
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-slate-800 text-sm font-black text-white shadow-sm">PM</span>
            <span className="hidden text-headline-sm font-black tracking-normal text-slate-950 sm:inline">PM Agent</span>
          </button>
          <nav className="ml-stack-lg hidden items-center gap-4 lg:flex xl:gap-stack-lg">
            <a 
              onClick={() => setCurrentView('dashboard')}
              className={topNavClass('dashboard')}>
              {t('header.dashboard')}
            </a>
            <a 
              onClick={() => setCurrentView('analytics')}
              className={topNavClass('analytics')}>
              {t('header.analytics')}
            </a>
            <a 
              onClick={() => setCurrentView('team')}
              className={topNavClass('team')}>
              {t('header.team')}
            </a>
            <a 
              onClick={() => setCurrentView('project')}
              className={topNavClass('project')}>
              {t('header.smart_lib')}
            </a>
          </nav>
        </div>
        <div className="flex min-w-0 items-center gap-2 sm:gap-stack-md">
          <div className="relative flex items-center gap-2">
            <span className="hidden text-sm font-semibold text-slate-800 sm:inline">{t('header.project')}</span>
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

          <button 
            onClick={async () => {
              try {
                const res = await createSprint(activeProjectId);
                alert(`${t('app.sprint.create_success')}${res.sprint?.name || t('common.success')}`);
                setCurrentView('sprint');
              } catch (err) {
                alert(`${t('app.sprint.create_error')}${err.message}`);
              }
            }}
            className="hidden min-h-9 rounded-xl bg-slate-800 px-4 py-2 text-sm font-bold text-white shadow-sm transition-all hover:-translate-y-0.5 hover:bg-slate-900 active:scale-95 sm:inline-flex"
          >
            {t('header.create_sprint')}
          </button>
          <button className="hidden h-9 w-9 place-items-center rounded-xl text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 sm:grid" aria-label="Notifications">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
          </button>
          <button className="hidden h-9 w-9 place-items-center rounded-xl text-slate-700 transition hover:bg-slate-100 hover:text-slate-950 sm:grid" aria-label="Help">
            <span className="material-symbols-outlined text-[20px]">help</span>
          </button>
          <div className="hidden h-9 w-9 overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm sm:block">
            <img alt="User Profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAYLpMm5rS4oPHKfptYorn3ApjUs8EZPpCiEzO6kWs7aHZGTK176msotL21zBJVMhIgNI-1QVAxie2jLek8BtYiteof08JuddF16FyFtG5Ry6qDpT-e69yiO3cZ3I5Pvj-EAmMkiy8tdPP8f94I3ml1VchqTIWNTSMNiTN1mRlS1L3LPq_jv7XLjRE3omju28JBSAsCVWHKPFmU-Hp5RcY1BBDtczB7dUta3AtL_4LDrEBxkoK5XJRhcyw3bp-tSursPTXAw2J0Yys" />
          </div>
        </div>
      </header>

      {/* Create Project Modal */}
      {showCreateProject && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center">
          <div className="bg-surface rounded-xl p-6 w-[400px] shadow-xl border border-outline-variant">
            <h3 className="text-xl font-bold mb-4">{t('app.project_modal.create_title')}</h3>
            <input 
              autoFocus
              className="w-full px-3 py-2 border border-outline-variant rounded-lg mb-4 focus:outline-none focus:border-primary"
              placeholder={t('app.project_modal.create_placeholder')}
              value={newProjectName}
              onChange={e => setNewProjectName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleCreateProject()}
            />
            <div className="flex justify-end gap-2">
              <button 
                className="px-4 py-2 rounded-lg font-medium text-on-surface-variant hover:bg-surface-container-high"
                onClick={() => setShowCreateProject(false)}
              >
                {t('common.cancel')}
              </button>
              <button 
                className="px-4 py-2 bg-primary text-on-primary rounded-lg font-medium"
                onClick={handleCreateProject}
              >
                {t('app.project_modal.create_confirm')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Project Modal */}
      {showEditProject && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center">
          <div className="bg-surface rounded-xl p-6 w-[400px] shadow-xl border border-outline-variant">
            <h3 className="text-xl font-bold mb-4">{t('app.project_modal.edit_title')}</h3>
            <input 
              autoFocus
              className="w-full px-3 py-2 border border-outline-variant rounded-lg mb-4 focus:outline-none focus:border-primary"
              placeholder={t('app.project_modal.edit_placeholder')}
              value={editProjectName}
              onChange={e => setEditProjectName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleUpdateProject()}
            />
            <div className="flex justify-end gap-2">
              <button 
                className="px-4 py-2 rounded-lg font-medium text-on-surface-variant hover:bg-surface-container-high"
                onClick={() => setShowEditProject(false)}
              >
                {t('common.cancel')}
              </button>
              <button 
                className="px-4 py-2 bg-primary text-on-primary rounded-lg font-medium"
                onClick={handleUpdateProject}
              >
                {t('app.project_modal.edit_confirm')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Project Confirm Modal */}
      {showDeleteProjectConfirm && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center">
          <div className="bg-surface rounded-xl p-6 w-[400px] shadow-xl border border-outline-variant">
            <h3 className="text-xl font-bold mb-2 text-error">{t('app.project_modal.delete_title')}</h3>
            <p className="text-on-surface-variant mb-6 text-sm">
              {t('app.project_modal.delete_message')}
            </p>
            <div className="flex justify-end gap-2">
              <button 
                className="px-4 py-2 rounded-lg font-medium text-on-surface-variant hover:bg-surface-container-high"
                onClick={() => setShowDeleteProjectConfirm(false)}
              >
                {t('common.cancel')}
              </button>
              <button 
                className="px-4 py-2 bg-error text-on-error rounded-lg font-medium hover:opacity-90"
                onClick={handleDeleteProject}
              >
                {t('app.project_modal.delete_confirm')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Side Navigation Bar */}
      <aside className="fixed left-0 top-14 z-40 hidden h-[calc(100vh-56px)] w-56 flex-col border-r border-slate-200 bg-white/90 p-3 shadow-sm backdrop-blur-xl lg:flex">
        <div className="mb-4 rounded-[22px] border border-slate-200 bg-gradient-to-br from-white via-slate-50 to-blue-50/60 p-3 shadow-sm shadow-slate-950/5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-white shadow-sm shadow-slate-950/15">
              <span className="material-symbols-outlined text-[23px]" style={{fontVariationSettings: "'FILL' 1"}}>folder_open</span>
            </div>
            <div className="min-w-0">
              <p className="truncate text-base font-black tracking-[-0.02em] text-slate-950">{t('header.smart_lib')}</p>
              <p className="mt-0.5 truncate text-xs font-bold text-slate-700">{sprintName}</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto sidebar-scroll space-y-1">
          <p className="px-3 pb-2 pt-1 text-[10px] font-black uppercase tracking-[0.24em] text-slate-600">{t('sidebar.main')}</p>
          <button
            type="button"
            className={sideNavClass('project')}
            onClick={() => setCurrentView('project')}
          >
            <span className="material-symbols-outlined text-[22px]">folder_open</span>
            <span className="truncate">{t('sidebar.projects')}</span>
          </button>
          <button
            type="button"
            className={sideNavClass('sprint')}
            onClick={() => setCurrentView('sprint')}
          >
            <span className="material-symbols-outlined text-[22px]">view_kanban</span>
            <span className="truncate">{t('sidebar.sprint')}</span>
          </button>
          <p className="mt-5 px-3 pb-2 text-[10px] font-black uppercase tracking-[0.24em] text-slate-600">{t('sidebar.settings')}</p>
          <button
            type="button"
            className={sideNavClass('config_jira')}
            onClick={() => setCurrentView('config_jira')}
          >
            <span className="material-symbols-outlined text-[22px]">settings_suggest</span>
            <span className="truncate">{t('sidebar.jira_config')}</span>
          </button>
          <button
            type="button"
            className={sideNavClass('config_slack')}
            onClick={() => setCurrentView('config_slack')}
          >
            <span className="material-symbols-outlined text-[22px]">hub</span>
            <span className="truncate">{t('sidebar.slack_config')}</span>
          </button>
          <button
            type="button"
            className={sideNavClass('config_github')}
            onClick={() => setCurrentView('config_github')}
          >
            <span className="material-symbols-outlined text-[22px]">code</span>
            <span className="truncate">{t('sidebar.github_config')}</span>
          </button>
          <p className="mt-5 px-3 pb-2 text-[10px] font-black uppercase tracking-[0.24em] text-slate-600">{t('sidebar.history')}</p>
          <button
            type="button"
            className={sideNavClass('history')}
            onClick={() => setCurrentView('history')}
          >
            <span className="material-symbols-outlined text-[22px]">history</span>
            <span className="truncate">{t('sidebar.query_history')}</span>
          </button>
        </nav>
        <div className="mt-auto flex flex-col gap-2 border-t border-slate-200 pt-4">
          <div className="px-stack-sm mb-2">
            <LanguageSwitcher />
          </div>
          <button type="button" className="flex min-h-11 w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-sm font-bold text-slate-800 transition hover:bg-slate-100 hover:text-slate-950">
            <span className="material-symbols-outlined text-[22px]">help</span>
            <span>{t('sidebar.help')}</span>
          </button>
          <button type="button" className="flex min-h-11 w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-sm font-bold text-red-600 transition hover:bg-red-50">
            <span className="material-symbols-outlined text-[22px]">logout</span>
            <span>{t('sidebar.logout')}</span>
          </button>
        </div>
      </aside>

      <nav className="fixed bottom-3 left-3 right-3 z-50 flex gap-2 rounded-[24px] border border-slate-200 bg-white/90 p-2 shadow-xl shadow-slate-950/10 backdrop-blur-xl lg:hidden" aria-label="Mobile navigation">
        <button className={mobileNavClass('dashboard')} onClick={() => setCurrentView('dashboard')}>
          <span className="material-symbols-outlined text-[20px]">dashboard</span>
          {t('header.dashboard')}
        </button>
        <button className={mobileNavClass('project')} onClick={() => setCurrentView('project')}>
          <span className="material-symbols-outlined text-[20px]">folder_open</span>
          {t('header.smart_lib')}
        </button>
        <button className={mobileNavClass('sprint')} onClick={() => setCurrentView('sprint')}>
          <span className="material-symbols-outlined text-[20px]">view_kanban</span>
          {t('sidebar.sprint')}
        </button>
        <button className={mobileNavClass('history')} onClick={() => setCurrentView('history')}>
          <span className="material-symbols-outlined text-[20px]">history</span>
          {t('sidebar.history')}
        </button>
      </nav>

      <main className="mt-14 min-h-[calc(100vh-56px)] bg-[radial-gradient(circle_at_18%_0%,rgba(71,85,105,0.10),transparent_28%),linear-gradient(180deg,#f3f4f6_0%,#f8fafc_44%,#ffffff_100%)] p-3 pb-28 sm:p-4 lg:ml-56 lg:p-5 xl:p-6">
        <div style={{ display: currentView === 'project' ? 'block' : 'none' }}>
            <div className="mx-auto max-w-7xl space-y-6">
              {historyItemView && (
                <div className="bg-primary/10 text-primary p-4 rounded-xl flex items-center justify-between border border-primary/20">
                  <div>
                    <h3 className="font-bold">{t('app.history_view.title')}</h3>
                    <p className="text-sm">{t('app.history_view.description')}</p>
                  </div>
                  <button 
                    onClick={() => setHistoryItemView(null)}
                    className="px-4 py-2 bg-primary text-on-primary rounded-lg font-medium text-sm hover:opacity-90 transition-opacity"
                  >
                    {t('app.history_view.back_to_current')}
                  </button>
                </div>
              )}
              <div className="space-y-stack-lg" style={{ display: historyItemView ? 'none' : 'block' }}>
                <RequirementInputPanel 
                  onSubmit={handleGenerate} 
                  isLoading={isLoading} 
                  generationMessage={generationMessage}
                  context={displayContext}
                  storyDraft={displayStoryDraft}
                  evaluation={displayEvaluation}
                  projectId={activeProjectId} 
                />
                {isLoading && <ProcessingStatusPanel isLoading={isLoading} context={displayContext} storyDraft={displayStoryDraft} evaluation={displayEvaluation} />}
                {error && (
                  <div className="bg-error-container text-on-error-container p-4 rounded-xl shadow-sm border border-error/20 flex gap-3">
                    <span className="material-symbols-outlined text-error">error</span>
                    <div>
                      <h3 className="font-bold">{t('app.errors.flow_generation')}</h3>
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
                      requirement: `${t('app.requirement.split_focus_prefix')} ${splitText}`,
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

        <div style={{ display: currentView === 'dashboard' ? 'block' : 'none' }}>
          <DashboardPanel projectId={activeProjectId} />
        </div>

        <div style={{ display: currentView === 'history' ? 'block' : 'none' }} className="h-full">
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

        <div style={{ display: currentView === 'config_github' ? 'block' : 'none' }}>
          <GithubConfigPanel projectId={activeProjectId} />
        </div>

        <div style={{ display: currentView === 'analytics' ? 'block' : 'none' }}>
          <AnalyticsPanel projectId={activeProjectId} />
        </div>

        <div style={{ display: currentView === 'team' ? 'block' : 'none' }}>
          <TeamPanel projectId={activeProjectId} />
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
