import { useState, useRef, useEffect } from 'react';
import { fetchJiraPriorities } from '../lib/api';

export default function StoryDraftEditor({ draft, evaluation, actions, actionExecution, isPushingJira, isRegenerating,  onChange,
  onPreviewJira,
  onPushToJira,
  onProvideClarification,
  onSelectSplit,
  onOpenSplitManager,
  onReset,
  projectId
}) {
  const [clarificationInput, setClarificationInput] = useState('');
  const [answers, setAnswers] = useState({});
  const [chatHistory, setChatHistory] = useState([]);
  const [priorities, setPriorities] = useState([]);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (projectId) {
      fetchJiraPriorities(projectId).then(data => {
        if (data && data.length > 0) {
          setPriorities(data);
        }
      }).catch(err => console.error("Failed to load Jira priorities:", err));
    }
  }, [projectId]);

  if (!draft) return null;

  const handleChange = (field, value) => {
    onChange({ ...draft, [field]: value });
  };

  const handleArrayChange = (field, index, value) => {
    const newArr = [...draft[field]];
    newArr[index] = value;
    onChange({ ...draft, [field]: newArr });
  };

  const handleAddArrayItem = (field, defaultValue = '') => {
    const newArr = [...(draft[field] || [])];
    newArr.push(defaultValue);
    onChange({ ...draft, [field]: newArr });
  };

  const handleRemoveArrayItem = (field, index) => {
    const newArr = [...(draft[field] || [])];
    newArr.splice(index, 1);
    onChange({ ...draft, [field]: newArr });
  };

  const handleTaskChange = (group, index, value) => {
    const newTasks = { ...draft.tasks };
    newTasks[group] = [...(newTasks[group] || [])];
    newTasks[group][index] = value;
    onChange({ ...draft, tasks: newTasks });
  };

  const handleAddTask = (group) => {
    const newTasks = { ...draft.tasks };
    newTasks[group] = [...(newTasks[group] || []), ''];
    onChange({ ...draft, tasks: newTasks });
  };

  const handleRemoveTask = (group, index) => {
    const newTasks = { ...draft.tasks };
    newTasks[group] = [...(newTasks[group] || [])];
    newTasks[group].splice(index, 1);
    onChange({ ...draft, tasks: newTasks });
  };

  const isApproved = evaluation?.status === 'APPROVED';
  const isJiraReady = actions?.jira?.ready;
  const needsClarification = evaluation?.status === 'NEEDS_CONTEXT' 
    || evaluation?.status === 'REVISION'
    || (draft.clarification_questions?.length > 0);

  const unansweredQuestions = draft.clarification_questions || [];

  const handleSendClarification = () => {
    let combinedText = '';
    
    unansweredQuestions.forEach((q, idx) => {
      const ans = answers[idx]?.trim();
      if (ans) {
         combinedText += `Câu hỏi: ${q}\nTrả lời: ${ans}\n\n`;
      }
    });

    if (clarificationInput.trim()) {
       combinedText += `Thông tin bổ sung: ${clarificationInput.trim()}\n`;
    }

    if (!combinedText || isRegenerating) return;

    // Add user reply to chat history
    setChatHistory(prev => [...prev, { role: 'user', text: combinedText }]);
    setAnswers({});
    setClarificationInput('');

    // Trigger re-generation with the clarification
    if (onProvideClarification) {
      onProvideClarification(combinedText);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendClarification();
    }
  };

  const hasIssues = evaluation?.issues?.length > 0;
  const showAllClear = unansweredQuestions.length === 0 && !hasIssues;

  return (
    <section className="bg-white/40 glass-panel rounded-2xl border border-white/40 overflow-hidden shadow-[0_8px_32px_rgba(0,0,0,0.08)] border-l-4 border-l-primary-container max-h-[800px] overflow-y-auto">
      
      {/* Header */}
      <div className="bg-white/60 p-container-padding border-b border-outline-variant/30 flex justify-between items-center backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-stack-sm">
          <div className="bg-primary-container/10 text-primary-container p-stack-sm rounded-xl">
            <span className="material-symbols-outlined text-[24px]" style={{fontVariationSettings: "'FILL' 1"}}>auto_awesome</span>
          </div>
          <div>
            <h3 className="font-headline-sm text-headline-sm font-bold text-primary">Human Approval</h3>
            <p className="text-[12px] text-on-surface-variant font-medium">(Bản nháp cần duyệt trước khi đẩy lên Jira)</p>
          </div>
        </div>
        <div className="flex items-center gap-stack-sm">
          <span className="ai-badge-pulse bg-green-50/80 text-green-700 text-[10px] font-bold px-3 py-1.5 rounded-full border border-green-200 uppercase tracking-widest flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
            AI Generated
          </span>
        </div>
      </div>

      <div className="p-container-padding space-y-stack-lg">
        {/* Error/Warning Issues from Evaluator */}
        {evaluation && evaluation.issues && evaluation.issues.length > 0 && !(draft.story_type === 'oversized_request' || draft.planning_status === 'SPLIT_RECOMMENDED') && (
          <div className="bg-red-50 border border-red-200 p-4 rounded-xl text-red-800 text-body-md">
            <strong>Issues Identified:</strong>
            <ul className="list-disc ml-5 mt-2">
              {evaluation.issues.map((issue, i) => <li key={i}>{issue}</li>)}
            </ul>
          </div>
        )}

        {/* Ticket Content */}
        {draft.story_type === 'oversized_request' || draft.planning_status === 'SPLIT_RECOMMENDED' ? (
          <div className="bg-white/80 rounded-2xl border-2 border-amber-300 p-container-padding shadow-sm relative space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-amber-600 text-[24px]">warning</span>
              <h3 className="text-title-lg font-bold text-amber-700">Yêu cầu quá lớn (Oversized Request)</h3>
            </div>
            <p className="text-body-md text-on-surface-variant">
              Yêu cầu này chứa quá nhiều tính năng để đưa vào một Ticket duy nhất. Hệ thống đề xuất phân tách (Story Splits) thành các Ticket nhỏ hơn.
            </p>

            {draft.story_splits?.length > 0 ? (
              <div className="bg-amber-50 p-6 rounded-xl border border-amber-200 flex flex-col items-center text-center space-y-4">
                <p className="text-amber-800 font-medium">Có {draft.story_splits.length} split được đề xuất cho yêu cầu này.</p>
                {onOpenSplitManager && (
                  <button 
                    onClick={onOpenSplitManager}
                    className="bg-primary text-on-primary px-6 py-3 rounded-xl font-bold hover:opacity-90 active:scale-95 shadow-lg flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined">splitscreen</span>
                    Mở Popup Quản Lý Splits
                  </button>
                )}
              </div>
            ) : (
              <p className="text-body-md italic text-outline">Chưa có đề xuất phân tách nào.</p>
            )}
          </div>
        ) : (
        <div className="space-y-stack-lg" id="ticket-list">
          <div className="bg-white/80 rounded-2xl border border-outline-variant/30 p-container-padding shadow-sm relative">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-gutter mb-stack-lg">
              <div className="md:col-span-2">
                <label className="text-label-md font-bold text-on-surface-variant mb-unit block">Tiêu đề Ticket</label>
                <input 
                  className="w-full bg-white/50 border border-outline-variant/50 rounded-xl px-4 py-3 font-headline-sm focus:ring-2 focus:ring-primary/20 outline-none" 
                  type="text" 
                  value={draft.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                />
              </div>
              <div>
                <label className="text-label-md font-bold text-on-surface-variant mb-unit block">Story Points</label>
                <input 
                  type="number"
                  className="w-full bg-white/50 border border-outline-variant/50 rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary/20 outline-none" 
                  value={draft.story_points || ''}
                  onChange={(e) => handleChange('story_points', parseInt(e.target.value, 10))}
                />
              </div>
              <div>
                <label className="text-label-md font-bold text-on-surface-variant mb-unit block">Độ ưu tiên</label>
                <select 
                  className="w-full bg-white/50 border border-outline-variant/50 rounded-xl px-4 py-3 font-bold text-red-600 focus:ring-2 focus:ring-primary/20 outline-none"
                  value={draft.priority || (priorities.length > 0 ? priorities[0].name : 'Medium')}
                  onChange={(e) => handleChange('priority', e.target.value)}
                >
                  {priorities.length > 0 ? (
                    priorities.map(p => (
                      <option key={p.id} value={p.name}>{p.name}</option>
                    ))
                  ) : (
                    <>
                      <option value="High">High</option>
                      <option value="Medium">Medium</option>
                      <option value="Low">Low</option>
                    </>
                  )}
                </select>
              </div>
            </div>

            <div className="space-y-stack-md">
              <div>
                <p className="text-label-md font-bold text-on-surface-variant mb-stack-sm uppercase">User Stories</p>
                <div className="space-y-2">
                  <textarea 
                    className="w-full p-3 bg-white/40 border border-outline-variant/20 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 outline-none resize-none h-24"
                    value={draft.user_story}
                    onChange={(e) => handleChange('user_story', e.target.value)}
                  />
                </div>
              </div>
              
              <div>
                <p className="text-label-md font-bold text-on-surface-variant mb-stack-sm uppercase">Acceptance Criteria</p>
                <div className="space-y-2">
                  {(draft.acceptance_criteria || []).map((ac, i) => (
                    <div key={i} className="flex gap-2">
                      <textarea 
                        className="flex-1 p-3 bg-white/40 border border-outline-variant/20 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 outline-none resize-none"
                        value={ac}
                        onChange={(e) => handleArrayChange('acceptance_criteria', i, e.target.value)}
                        rows={2}
                      />
                      <button onClick={() => handleRemoveArrayItem('acceptance_criteria', i)} className="text-red-400 hover:text-red-600 p-2"><span className="material-symbols-outlined text-[18px]">delete</span></button>
                    </div>
                  ))}
                  <button onClick={() => handleAddArrayItem('acceptance_criteria')} className="text-primary text-[12px] font-bold flex items-center gap-1 hover:underline"><span className="material-symbols-outlined text-[16px]">add</span>Thêm Acceptance Criteria</button>
                </div>
              </div>

              <div>
                <p className="text-label-md font-bold text-on-surface-variant mb-stack-sm uppercase">Sub-Tasks</p>
                <div className="space-y-2">
                  {draft.tasks?.be?.map((task, i) => (
                    <div key={`be-${i}`} className="flex items-center gap-2 p-2 bg-white/40 border border-outline-variant/20 rounded-lg">
                      <span className="text-[10px] font-bold text-primary">BE</span>
                      <input className="bg-transparent border-none outline-none flex-1 text-body-md" value={task} onChange={(e) => handleTaskChange('be', i, e.target.value)} />
                      <button onClick={() => handleRemoveTask('be', i)} className="text-red-400 hover:text-red-600 p-1"><span className="material-symbols-outlined text-[14px]">close</span></button>
                    </div>
                  ))}
                  <button onClick={() => handleAddTask('be')} className="text-primary text-[12px] font-bold flex items-center gap-1 hover:underline"><span className="material-symbols-outlined text-[16px]">add</span>Thêm task BE</button>
                  
                  {draft.tasks?.fe?.map((task, i) => (
                    <div key={`fe-${i}`} className="flex items-center gap-2 p-2 bg-white/40 border border-outline-variant/20 rounded-lg">
                      <span className="text-[10px] font-bold text-green-600">FE</span>
                      <input className="bg-transparent border-none outline-none flex-1 text-body-md" value={task} onChange={(e) => handleTaskChange('fe', i, e.target.value)} />
                      <button onClick={() => handleRemoveTask('fe', i)} className="text-red-400 hover:text-red-600 p-1"><span className="material-symbols-outlined text-[14px]">close</span></button>
                    </div>
                  ))}
                  <button onClick={() => handleAddTask('fe')} className="text-green-600 text-[12px] font-bold flex items-center gap-1 hover:underline"><span className="material-symbols-outlined text-[16px]">add</span>Thêm task FE</button>
                  
                  {draft.tasks?.qa?.map((task, i) => (
                    <div key={`qa-${i}`} className="flex items-center gap-2 p-2 bg-white/40 border border-outline-variant/20 rounded-lg">
                      <span className="text-[10px] font-bold text-orange-600">QA</span>
                      <input className="bg-transparent border-none outline-none flex-1 text-body-md" value={task} onChange={(e) => handleTaskChange('qa', i, e.target.value)} />
                      <button onClick={() => handleRemoveTask('qa', i)} className="text-red-400 hover:text-red-600 p-1"><span className="material-symbols-outlined text-[14px]">close</span></button>
                    </div>
                  ))}
                  <button onClick={() => handleAddTask('qa')} className="text-orange-600 text-[12px] font-bold flex items-center gap-1 hover:underline"><span className="material-symbols-outlined text-[16px]">add</span>Thêm task QA</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        )}

        {/* AI Clarification Chat Section */}
        <div className="mt-stack-lg border-t border-outline-variant/30 pt-stack-lg">
          <div className="bg-surface-container-low rounded-2xl p-stack-md border border-outline-variant/20">
            <div className="flex items-center gap-2 mb-stack-md">
              <span className="material-symbols-outlined text-primary" style={{fontVariationSettings: "'FILL' 1"}}>forum</span>
              <h4 className="text-label-md font-bold text-primary uppercase tracking-wider">AI Clarification</h4>
              {needsClarification && (
                <span className="ml-auto bg-amber-100 text-amber-700 text-[10px] font-bold px-2 py-1 rounded-full border border-amber-300 uppercase tracking-wider animate-pulse">
                  Cần làm rõ
                </span>
              )}
            </div>

            {/* Chat History (Past Iterations) */}
            {chatHistory.length > 0 && (
              <div className="space-y-stack-md max-h-64 overflow-y-auto mb-stack-md px-2 scroll-smooth">
                {chatHistory.map((entry, idx) => (
                  <div key={`chat-${idx}`} className="flex gap-stack-sm flex-row-reverse">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-secondary-container">
                      <span className="material-symbols-outlined text-[18px] text-on-secondary-container">person</span>
                    </div>
                    <div className="p-3 rounded-2xl shadow-sm text-body-md border max-w-[85%] bg-primary/10 border-primary/20 rounded-tr-none text-on-surface whitespace-pre-wrap">
                      {entry.text}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Error/Warning Issues */}
            {hasIssues && (
              <div className="mb-stack-md space-y-2 px-2">
                {evaluation.issues.map((issue, idx) => (
                  <div key={`issue-${idx}`} className="flex gap-stack-sm">
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center shrink-0">
                      <span className="material-symbols-outlined text-red-600 text-[18px]">error</span>
                    </div>
                    <div className="bg-red-50 p-3 rounded-2xl rounded-tl-none shadow-sm text-body-md border border-red-100 max-w-[85%] text-red-800">
                      {issue}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Clarification Questions Form */}
            {unansweredQuestions.length > 0 && (
              <div className="space-y-4 mb-stack-md px-2">
                <p className="text-sm font-bold text-on-surface-variant flex items-center gap-2">
                  <span className="material-symbols-outlined text-primary text-[20px]">smart_toy</span>
                  AI cần bạn làm rõ các câu hỏi sau để hoàn thiện Story:
                </p>
                {unansweredQuestions.map((q, idx) => (
                  <div key={`q-${idx}`} className="bg-white p-4 rounded-xl border border-primary/20 shadow-sm space-y-3 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-primary/40"></div>
                    <div className="flex gap-2 text-on-surface font-medium text-body-md">
                      <span className="bg-primary/10 text-primary w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0">{idx + 1}</span>
                      <p>{q}</p>
                    </div>
                    <textarea
                      className="w-full bg-surface-container-lowest border border-outline-variant/50 rounded-lg px-3 py-3 text-body-md focus:ring-2 focus:ring-primary/40 outline-none resize-none transition-all placeholder:text-outline-variant"
                      rows={2}
                      placeholder="Nhập câu trả lời của bạn cho câu hỏi này..."
                      value={answers[idx] || ''}
                      onChange={(e) => setAnswers(prev => ({ ...prev, [idx]: e.target.value }))}
                      disabled={isRegenerating}
                    />
                  </div>
                ))}
              </div>
            )}

            {/* All Clear Message */}
            {showAllClear && !isRegenerating && (
              <div className="flex gap-stack-sm mb-stack-md px-2">
                <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-green-600 text-[18px]">check_circle</span>
                </div>
                <div className="bg-green-50 p-3 rounded-2xl rounded-tl-none shadow-sm text-body-md border border-green-100 max-w-[85%] text-green-800">
                  Mọi thứ đã rõ ràng, bạn có thể duyệt để push lên Jira.
                </div>
              </div>
            )}

            {/* Regeneration loading indicator */}
            {isRegenerating && (
              <div className="flex gap-stack-sm mb-stack-md px-2">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-primary text-[18px] animate-spin">progress_activity</span>
                </div>
                <div className="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm text-body-md border border-outline-variant/10 italic text-on-surface-variant">
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                    <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                    AI đang phân tích lại với thông tin phản hồi của bạn...
                  </span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />

            {/* Chat Input */}
            <div className="flex gap-2 mt-4 px-2">
              <input 
                className="flex-1 bg-white border border-outline-variant/50 rounded-xl px-4 py-2 font-body-md focus:ring-2 focus:ring-primary/20 outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all" 
                placeholder={isRegenerating ? "Đang xử lý..." : "Nhập thông tin bổ sung chung (nếu cần)..."} 
                type="text"
                value={clarificationInput}
                onChange={(e) => setClarificationInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isRegenerating}
              />
              <button 
                className={`px-4 py-2 rounded-xl font-bold flex items-center gap-2 transition-all ${
                  (Object.keys(answers).some(k => answers[k].trim()) || clarificationInput.trim()) && !isRegenerating
                    ? 'bg-primary text-on-primary hover:opacity-90 active:scale-95 shadow-md'
                    : 'bg-outline/20 text-outline cursor-not-allowed'
                }`}
                onClick={handleSendClarification}
                disabled={(!Object.keys(answers).some(k => answers[k].trim()) && !clarificationInput.trim()) || isRegenerating}
              >
                <span className="material-symbols-outlined text-[20px]">send</span>
                Gửi Phản Hồi
              </button>
            </div>
          </div>
        </div>

        {actionExecution?.jira && (
          <div className={`p-4 rounded-xl border text-body-md ${actionExecution.jira.executed ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
            <strong>{actionExecution.jira.executed ? 'Jira issue created.' : 'Jira push failed.'}</strong>
            {actionExecution.jira.created?.story?.key && (
              <p className="mt-1">
                Issue: <a className="underline font-bold" href={actionExecution.jira.created.story.url} target="_blank" rel="noreferrer">{actionExecution.jira.created.story.key}</a>
              </p>
            )}
            {actionExecution.jira.warnings?.length > 0 && (
              <ul className="list-disc ml-5 mt-2">
                {actionExecution.jira.warnings.map((warning, i) => <li key={i}>{warning}</li>)}
              </ul>
            )}
          </div>
        )}

        {actionExecution?.slack && (
          <div className={`p-4 rounded-xl border text-body-md mt-2 ${actionExecution.slack.executed ? 'bg-blue-50 border-blue-200 text-blue-800' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
            <strong>{actionExecution.slack.executed ? 'Slack notification sent.' : 'Slack notification failed or skipped.'}</strong>
            {actionExecution.slack.warnings?.length > 0 && (
              <ul className="list-disc ml-5 mt-2">
                {actionExecution.slack.warnings.map((warning, i) => <li key={i}>{warning}</li>)}
              </ul>
            )}
          </div>
        )}

        {actionExecution?.github && (
          <div className={`p-4 rounded-xl border text-body-md mt-2 ${actionExecution.github.executed ? 'bg-purple-50 border-purple-200 text-purple-800' : 'bg-red-50 border-red-200 text-red-800'}`}>
            <strong>{actionExecution.github.executed ? 'GitHub feature branch created.' : 'GitHub action failed.'}</strong>
            {actionExecution.github.created?.branch_url && (
              <p className="mt-1">
                Branch: <a className="underline font-bold" href={actionExecution.github.created.branch_url} target="_blank" rel="noreferrer">{actionExecution.github.payload?.branch_name || 'View Branch'}</a>
              </p>
            )}
            {actionExecution.github.warnings?.length > 0 && (
              <ul className="list-disc ml-5 mt-2">
                {actionExecution.github.warnings.map((warning, i) => <li key={i}>{warning}</li>)}
              </ul>
            )}
          </div>
        )}

        {/* Story Splits Suggestion */}
        {draft.story_splits && draft.story_splits.length > 0 && onOpenSplitManager && (
          <div className="mt-stack-lg p-stack-md bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="material-symbols-outlined text-blue-500" style={{fontVariationSettings: "'FILL' 1"}}>call_split</span>
                <h4 className="text-label-md font-bold text-blue-700 uppercase tracking-wider">AI Gợi Ý Tách Ticket</h4>
              </div>
              <p className="text-body-sm text-blue-800">
                Yêu cầu của bạn có thể tách thành {draft.story_splits.length} ticket con (Epic).
              </p>
            </div>
            <button 
              onClick={onOpenSplitManager}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-blue-700 transition-colors flex items-center gap-2 shadow-sm"
            >
              <span className="material-symbols-outlined text-[18px]">splitscreen</span>
              Xử Lý Splits
            </button>
          </div>
        )}

        {/* Footer Buttons */}
        <div className="flex gap-gutter pt-stack-lg">
          {actionExecution?.jira?.executed ? (
            <button 
              className="flex-1 py-4 border-2 border-primary text-primary font-bold text-label-md rounded-xl hover:bg-primary/5 transition-colors"
              onClick={onReset}
            >
              + TẠO YÊU CẦU MỚI
            </button>
          ) : (
            <button 
              className="flex-1 py-4 border border-outline-variant text-on-surface-variant font-bold text-label-md rounded-xl hover:bg-surface-container-high transition-colors disabled:opacity-50"
              onClick={onPreviewJira}
              disabled={isRegenerating}
            >
              ↻ TẠO LẠI BẢN NHÁP (PREVIEW)
            </button>
          )}
          <button
            disabled={isPushingJira || !isApproved || (actions && !isJiraReady) || isRegenerating}
            onClick={onPushToJira}
            className={`flex-[2] py-4 font-bold text-label-md rounded-xl shadow-lg transition-all ${(isPushingJira || !isApproved || (actions && !isJiraReady) || isRegenerating) ? 'bg-gray-400 text-gray-200 cursor-not-allowed' : 'bg-primary text-on-primary shadow-primary/20 hover:opacity-90 active:scale-95'}`}
          >
            {isPushingJira ? '⏳ EXECUTING ACTIONS...' : '✅ EXECUTE ACTIONS (JIRA & SLACK)'}
          </button>
        </div>
        
      </div>
    </section>
  );
}
