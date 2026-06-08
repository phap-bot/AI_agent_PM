import { useState, useRef, useEffect } from 'react';
import { fetchJiraPriorities } from '../lib/api';

export default function StoryDraftEditor({ draft, evaluation, actions, actionExecution, isPushingJira, isRegenerating,  onChange,
  onPreviewJira,
  onPushToJira,
  onProvideClarification,
  onSelectSplit,
  projectId
}) {
  const [clarificationInput, setClarificationInput] = useState('');
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

  const handleSendClarification = () => {
    const text = clarificationInput.trim();
    if (!text || isRegenerating) return;

    // Add user reply to chat history
    setChatHistory(prev => [...prev, { role: 'user', text }]);
    setClarificationInput('');

    // Trigger re-generation with the clarification
    if (onProvideClarification) {
      onProvideClarification(text);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendClarification();
    }
  };

  // Build the list of AI messages to show
  const aiMessages = [];
  if (draft.clarification_questions?.length > 0) {
    draft.clarification_questions.forEach(q => aiMessages.push(q));
  }
  if (evaluation?.issues?.length > 0) {
    evaluation.issues.forEach(issue => {
      if (!aiMessages.includes(issue)) aiMessages.push(issue);
    });
  }
  if (aiMessages.length === 0) {
    aiMessages.push("Mọi thứ đã rõ ràng, bạn có thể duyệt để push lên Jira.");
  }

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
        {evaluation && evaluation.issues && evaluation.issues.length > 0 && (
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
              Yêu cầu này chứa quá nhiều tính năng để đưa vào một Ticket duy nhất. Dưới đây là đề xuất phân tách (Story Splits) thành các Ticket nhỏ hơn:
            </p>

            {draft.story_splits?.length > 0 ? (
              <div className="space-y-4">
                {draft.story_splits.map(split => (
                  <div key={split.id} className="p-4 border border-outline-variant/50 rounded-xl bg-surface hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <h5 className="font-bold text-primary">{split.title}</h5>
                      <span className={`text-[12px] px-2 py-1 rounded-full font-bold uppercase tracking-wider ${
                        split.priority === 'high' ? 'bg-red-100 text-red-700' : 
                        split.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' : 
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {split.priority}
                      </span>
                    </div>
                    <p className="text-body-md text-on-surface-variant mb-4">{split.description}</p>
                    
                    <div className="flex flex-wrap gap-4 text-[12px] text-outline border-t border-outline-variant/30 pt-3">
                      <span className="flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">confirmation_number</span>Points: <strong>{split.estimated_points}</strong></span>
                      <span className="flex items-center gap-1"><span className="material-symbols-outlined text-[14px]">skateboarding</span>Sprint đề xuất: <strong>{
                        draft.sprint_allocation?.find(a => a.story_split_id === split.id)?.recommended_sprint || 'N/A'
                      }</strong></span>
                    </div>
                    {split.related_endpoints?.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {split.related_endpoints.map((ep, i) => (
                          <span key={i} className="text-[10px] bg-surface-container-high px-2 py-1 rounded-md text-on-surface-variant font-mono">
                            {ep}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
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

            {/* Chat Messages */}
            <div className="space-y-stack-md max-h-64 overflow-y-auto mb-stack-md px-2 scroll-smooth">
              {/* AI Messages */}
              {aiMessages.map((msg, idx) => (
                <div key={`ai-${idx}`} className="flex gap-stack-sm">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <span className="material-symbols-outlined text-primary text-[18px]">smart_toy</span>
                  </div>
                  <div className="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm text-body-md border border-outline-variant/10 max-w-[85%]">
                    {msg}
                  </div>
                </div>
              ))}

              {/* Chat History (user replies) */}
              {chatHistory.map((entry, idx) => (
                <div key={`chat-${idx}`} className={`flex gap-stack-sm ${entry.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${entry.role === 'user' ? 'bg-secondary-container' : 'bg-primary/10'}`}>
                    <span className={`material-symbols-outlined text-[18px] ${entry.role === 'user' ? 'text-on-secondary-container' : 'text-primary'}`}>
                      {entry.role === 'user' ? 'person' : 'smart_toy'}
                    </span>
                  </div>
                  <div className={`p-3 rounded-2xl shadow-sm text-body-md border max-w-[85%] ${
                    entry.role === 'user' 
                      ? 'bg-primary/10 border-primary/20 rounded-tr-none text-on-surface' 
                      : 'bg-white border-outline-variant/10 rounded-tl-none'
                  }`}>
                    {entry.text}
                  </div>
                </div>
              ))}

              {/* Regeneration loading indicator */}
              {isRegenerating && (
                <div className="flex gap-stack-sm">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <span className="material-symbols-outlined text-primary text-[18px] animate-spin">progress_activity</span>
                  </div>
                  <div className="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm text-body-md border border-outline-variant/10 italic text-on-surface-variant">
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '0ms'}}></span>
                      <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '150ms'}}></span>
                      <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{animationDelay: '300ms'}}></span>
                      AI đang phân tích lại với thông tin bổ sung...
                    </span>
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <div className="flex gap-2">
              <input 
                className="flex-1 bg-white border border-outline-variant/50 rounded-xl px-4 py-2 font-body-md focus:ring-2 focus:ring-primary/20 outline-none disabled:opacity-50 disabled:cursor-not-allowed transition-all" 
                placeholder={isRegenerating ? "Đang xử lý..." : "Phản hồi để làm rõ yêu cầu..."} 
                type="text"
                value={clarificationInput}
                onChange={(e) => setClarificationInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isRegenerating}
              />
              <button 
                className={`p-2 rounded-xl transition-all ${
                  clarificationInput.trim() && !isRegenerating
                    ? 'bg-primary text-on-primary hover:opacity-90 active:scale-95 shadow-md'
                    : 'bg-outline/20 text-outline cursor-not-allowed'
                }`}
                onClick={handleSendClarification}
                disabled={!clarificationInput.trim() || isRegenerating}
              >
                <span className="material-symbols-outlined">send</span>
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

        {/* Story Splits Suggestion */}
        {draft.story_splits && draft.story_splits.length > 0 && (
          <div className="mt-stack-lg p-stack-md bg-blue-50 border border-blue-200 rounded-xl">
            <div className="flex items-center gap-2 mb-unit">
              <span className="material-symbols-outlined text-blue-500" style={{fontVariationSettings: "'FILL' 1"}}>call_split</span>
              <h4 className="text-label-md font-bold text-blue-700 uppercase tracking-wider">AI Gợi Ý Tách Ticket</h4>
            </div>
            <p className="text-body-sm text-blue-800 mb-stack-sm">
              Yêu cầu của bạn khá lớn (Epic), AI đề xuất nên tách thành các Ticket con dưới đây. Bạn có thể click vào để AI tập trung viết riêng cho ticket đó:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {draft.story_splits.map((split, idx) => {
                const splitTitle = typeof split === 'string' ? split : (split.title || split.name || `Sub-ticket ${idx+1}`);
                const splitDesc = typeof split === 'string' ? '' : (split.description || split.reason || '');
                const splitText = splitTitle + (splitDesc ? `: ${splitDesc}` : '');
                
                return (
                  <button 
                    key={idx}
                    onClick={() => onSelectSplit(splitText)}
                    disabled={isRegenerating || isPushingJira}
                    className="text-left bg-white p-3 rounded-lg border border-blue-200 hover:border-blue-400 hover:shadow-md transition-all active:scale-[0.98] disabled:opacity-50"
                  >
                    <div className="font-bold text-label-sm text-blue-900 mb-1">{splitTitle}</div>
                    {splitDesc && <div className="text-body-sm text-blue-700 line-clamp-2">{splitDesc}</div>}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Footer Buttons */}
        <div className="flex gap-gutter pt-stack-lg">
          <button 
            className="flex-1 py-4 border border-outline-variant text-on-surface-variant font-bold text-label-md rounded-xl hover:bg-surface-container-high transition-colors disabled:opacity-50"
            onClick={onPreviewJira}
            disabled={isRegenerating}
          >
            ↻ TẠO LẠI BẢN NHÁP (PREVIEW)
          </button>
          <button
            disabled={isPushingJira || !isApproved || (actions && !isJiraReady) || isRegenerating}
            onClick={onPushToJira}
            className={`flex-[2] py-4 font-bold text-label-md rounded-xl shadow-lg transition-all ${(isPushingJira || !isApproved || (actions && !isJiraReady) || isRegenerating) ? 'bg-gray-400 text-gray-200 cursor-not-allowed' : 'bg-primary text-on-primary shadow-primary/20 hover:opacity-90 active:scale-95'}`}
          >
            {isPushingJira ? '⏳ PUSHING TO JIRA...' : '✅ PUSH TO JIRA'}
          </button>
        </div>
        
      </div>
    </section>
  );
}
