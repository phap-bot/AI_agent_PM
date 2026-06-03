import { useState } from 'react';

export default function StoryDraftEditor({ draft, evaluation, actions, actionExecution, isPushingJira, onChange, onPreviewJira, onPushToJira }) {
  if (!draft) return null;

  const handleChange = (field, value) => {
    onChange({ ...draft, [field]: value });
  };

  const handleArrayChange = (field, index, value) => {
    const newArr = [...draft[field]];
    newArr[index] = value;
    onChange({ ...draft, [field]: newArr });
  };

  const isApproved = evaluation?.status === 'APPROVED';
  const isJiraReady = actions?.jira?.ready;

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
                <select className="w-full bg-white/50 border border-outline-variant/50 rounded-xl px-4 py-3 font-bold text-red-600 focus:ring-2 focus:ring-primary/20 outline-none">
                  <option defaultValue>High</option>
                  <option>Medium</option>
                  <option>Low</option>
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
                  {draft.acceptance_criteria.map((ac, i) => (
                    <textarea 
                      key={i}
                      className="w-full p-3 bg-white/40 border border-outline-variant/20 rounded-lg text-body-md focus:ring-2 focus:ring-primary/20 outline-none resize-none"
                      value={ac}
                      onChange={(e) => handleArrayChange('acceptance_criteria', i, e.target.value)}
                      rows={2}
                    />
                  ))}
                </div>
              </div>

              <div>
                <p className="text-label-md font-bold text-on-surface-variant mb-stack-sm uppercase">Sub-Tasks</p>
                <div className="space-y-2">
                  {draft.tasks?.be?.map((task, i) => (
                    <div key={`be-${i}`} className="flex items-center gap-2 p-2 bg-white/40 border border-outline-variant/20 rounded-lg">
                      <span className="text-[10px] font-bold text-primary">BE</span>
                      <input className="bg-transparent border-none outline-none flex-1 text-body-md" value={task} readOnly/>
                    </div>
                  ))}
                  {draft.tasks?.fe?.map((task, i) => (
                    <div key={`fe-${i}`} className="flex items-center gap-2 p-2 bg-white/40 border border-outline-variant/20 rounded-lg">
                      <span className="text-[10px] font-bold text-green-600">FE</span>
                      <input className="bg-transparent border-none outline-none flex-1 text-body-md" value={task} readOnly/>
                    </div>
                  ))}
                  {draft.tasks?.qa?.map((task, i) => (
                    <div key={`qa-${i}`} className="flex items-center gap-2 p-2 bg-white/40 border border-outline-variant/20 rounded-lg">
                      <span className="text-[10px] font-bold text-orange-600">QA</span>
                      <input className="bg-transparent border-none outline-none flex-1 text-body-md" value={task} readOnly/>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI Clarification Section */}
        <div className="mt-stack-lg border-t border-outline-variant/30 pt-stack-lg">
          <div className="bg-surface-container-low rounded-2xl p-stack-md border border-outline-variant/20">
            <div className="flex items-center gap-2 mb-stack-md">
              <span className="material-symbols-outlined text-primary" style={{fontVariationSettings: "'FILL' 1"}}>forum</span>
              <h4 className="text-label-md font-bold text-primary uppercase tracking-wider">AI Clarification</h4>
            </div>
            <div className="space-y-stack-md max-h-48 overflow-y-auto mb-stack-md px-2">
              <div className="flex gap-stack-sm">
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                  <span className="material-symbols-outlined text-primary text-[18px]">smart_toy</span>
                </div>
                <div className="bg-white p-3 rounded-2xl rounded-tl-none shadow-sm text-body-md border border-outline-variant/10">
                  {draft.clarification_questions?.length > 0 
                    ? draft.clarification_questions[0] 
                    : "Mọi thứ đã rõ ràng, bạn có thể duyệt để push lên Jira."}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <input className="flex-1 bg-white border border-outline-variant/50 rounded-xl px-4 py-2 font-body-md focus:ring-2 focus:ring-primary/20 outline-none" placeholder="Phản hồi tại đây..." type="text"/>
              <button className="bg-primary text-on-primary p-2 rounded-xl">
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

        {/* Footer Buttons */}
        <div className="flex gap-gutter pt-stack-lg">
          <button 
            className="flex-1 py-4 border border-outline-variant text-on-surface-variant font-bold text-label-md rounded-xl hover:bg-surface-container-high transition-colors"
            onClick={onPreviewJira}
          >
            ↻ TẠO LẠI BẢN NHÁP (PREVIEW)
          </button>
          <button
            disabled={isPushingJira || !isApproved || (actions && !isJiraReady)}
            onClick={onPushToJira}
            className={`flex-[2] py-4 font-bold text-label-md rounded-xl shadow-lg transition-all ${(isPushingJira || !isApproved || (actions && !isJiraReady)) ? 'bg-gray-400 text-gray-200 cursor-not-allowed' : 'bg-primary text-on-primary shadow-primary/20 hover:opacity-90 active:scale-95'}`}
          >
            {isPushingJira ? '⏳ PUSHING TO JIRA...' : '✅ PUSH TO JIRA'}
          </button>
        </div>
        
      </div>
    </section>
  );
}
