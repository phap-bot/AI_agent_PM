import React, { useState, useEffect, useRef } from 'react';
import { fetchSprintBoard, deleteSprintIssue, updateSprintIssueStatus, completeSprint } from '../lib/api';
import { useTranslation } from 'react-i18next';

const COLUMN_STATUS_MAP = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done',
};

function classifyIssue(status) {
  const s = status.toLowerCase();
  if (s.includes('done') || s.includes('closed')) return 'done';
  if (s.includes('in progress')) return 'in_progress';
  return 'todo';
}

export default function SprintBoardPanel({ isActive, projectId }) {
  const { t } = useTranslation();
  const [boardData, setBoardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [draggingKey, setDraggingKey] = useState(null);
  const [dropTarget, setDropTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  // New features state
  const [groupBy, setGroupBy] = useState('none'); // 'none' or 'subtask'
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [completeLoading, setCompleteLoading] = useState(false);
  const [moveOpenTo, setMoveOpenTo] = useState('new_sprint');

  const isInteracting = useRef(false);

  useEffect(() => {
    let intervalId;
    if (isActive) {
      loadBoard(true);
      intervalId = setInterval(() => {
        if (!isInteracting.current && !actionLoading && !confirmDelete && !showCompleteModal) {
          loadBoard(false);
        }
      }, 5000);
    }
    return () => clearInterval(intervalId);
  }, [isActive, projectId]);

  // Track interaction state to pause polling
  useEffect(() => {
    isInteracting.current = (draggingKey !== null || dropTarget !== null);
  }, [draggingKey, dropTarget]);

  const loadBoard = async (showLoading = false) => {
    try {
      if (showLoading) setLoading(true);
      setError(null);
      const data = await fetchSprintBoard(projectId);
      // Only update if not actively dragging to prevent drag drop interruption
      if (!isInteracting.current) {
        setBoardData(data);
      }
    } catch (err) {
      if (showLoading) setError(err.message);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  const handleDelete = async (issueKey) => {
    setActionLoading(issueKey);
    setConfirmDelete(null);
    try {
      const result = await deleteSprintIssue(issueKey, projectId);
      if (result.success) {
        setBoardData(prev => ({
          ...prev,
          issues: prev.issues.filter(i => i.key !== issueKey),
        }));
      } else {
        alert(t('sprint_board.delete_fail') + (result.error || t('common.unknown_error')));
      }
    } catch (err) {
      alert(t('sprint_board.delete_fail') + err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDrop = async (issueKey, targetColumn) => {
    const targetStatus = COLUMN_STATUS_MAP[targetColumn];
    if (!targetStatus) return;

    const issue = boardData?.issues?.find(i => i.key === issueKey);
    if (!issue) return;
    if (classifyIssue(issue.status) === targetColumn) return;

    const previousStatus = issue.status;
    setBoardData(prev => ({
      ...prev,
      issues: prev.issues.map(i =>
        i.key === issueKey ? { ...i, status: targetStatus } : i
      ),
    }));

    setActionLoading(issueKey);
    try {
      const result = await updateSprintIssueStatus(issueKey, targetStatus, projectId);
      if (!result.success) {
        setBoardData(prev => ({
          ...prev,
          issues: prev.issues.map(i =>
            i.key === issueKey ? { ...i, status: previousStatus } : i
          ),
        }));
        alert(t('sprint_board.status_change_fail') + (result.error || t('common.unknown_error')));
      }
    } catch (err) {
      setBoardData(prev => ({
        ...prev,
        issues: prev.issues.map(i =>
          i.key === issueKey ? { ...i, status: previousStatus } : i
        ),
      }));
      alert(t('sprint_board.status_change_fail') + err.message);
    } finally {
      setActionLoading(null);
      setDraggingKey(null);
      setDropTarget(null);
    }
  };

  const handleCompleteSprint = async () => {
    setCompleteLoading(true);
    try {
      const openIssues = boardData.issues
        .filter(i => classifyIssue(i.status) !== 'done')
        .map(i => i.key);

      const result = await completeSprint(boardData.sprint.id, {
        move_open_to: moveOpenTo,
        open_issues: openIssues
      }, projectId);

      if (result.success) {
        setShowCompleteModal(false);
        loadBoard();
      } else {
        alert(t('sprint_board.complete_fail') + (result.error || t('common.unknown_error')));
      }
    } catch (err) {
      alert(t('sprint_board.complete_fail') + err.message);
    } finally {
      setCompleteLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[320px] items-center justify-center rounded-lg border border-slate-200 bg-white">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-800">
        {t('sprint_board.load_error')} {error}
      </div>
    );
  }

  if (!boardData?.sprint) {
    return (
      <div className="flex min-h-[320px] flex-col items-center justify-center gap-4 rounded-lg border border-slate-200 bg-white p-12 text-center text-slate-700">
        <span className="material-symbols-outlined text-4xl text-slate-500">calendar_month</span>
        <p className="max-w-md text-sm font-medium">{t('sprint_board.no_active_sprint_desc')}</p>
        <button
          onClick={loadBoard}
          className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-900 transition-colors hover:bg-slate-50"
        >
          <span className="material-symbols-outlined text-sm">sync</span>
          {t('sprint_board.reload_data')}
        </button>
      </div>
    );
  }

  const { sprint, issues } = boardData;
  const completedCount = issues.filter(i => classifyIssue(i.status) === 'done').length;
  const openCount = issues.length - completedCount;

  // Render a single column
  const renderColumn = (colKey, colIssues, dropPrefix = '', colLabel = null) => {
    const targetDropId = dropPrefix ? `${dropPrefix}-${colKey}` : colKey;
    const displayLabel = colLabel || t(`sprint_board.column_${colKey}`);
    return (
      <section
        key={targetDropId}
        className={`flex min-w-[320px] flex-1 flex-col rounded-lg border bg-slate-50 transition-colors ${dropTarget === targetDropId
            ? 'border-blue-500 bg-blue-50/70 ring-2 ring-blue-100'
            : 'border-slate-200'
          }`}
        onDragOver={(e) => {
          e.preventDefault();
          setDropTarget(targetDropId);
        }}
        onDragLeave={() => setDropTarget(null)}
        onDrop={(e) => {
          e.preventDefault();
          setDropTarget(null);
          const issueKey = e.dataTransfer.getData('text/plain');
          if (issueKey) handleDrop(issueKey, colKey);
        }}
      >
        <div className="flex min-h-12 items-center justify-between border-b border-slate-200 px-4">
          <h3 className="text-xs font-black uppercase tracking-[0.16em] text-slate-800">{displayLabel}</h3>
          <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-white px-2 text-xs font-black text-slate-700 ring-1 ring-slate-200">
            {colIssues.length}
          </span>
        </div>

        <div className="custom-scrollbar min-h-[160px] flex-1 space-y-3 p-3">
          {colIssues.map(issue => renderIssueCard(issue))}

          {colIssues.length === 0 && (
            <div className={`flex h-28 items-center justify-center rounded-lg border border-dashed text-sm font-semibold transition-colors ${dropTarget === targetDropId
                ? 'border-blue-400 bg-blue-50 text-blue-700'
                : 'border-slate-300 text-slate-400'
              }`}>
              {dropTarget === targetDropId ? t('sprint_board.drop_here') : ''}
            </div>
          )}
        </div>
      </section>
    );
  };

  // Render a single issue card
  const renderIssueCard = (issue) => {
    let displayId = issue.key;
    let displaySummary = issue.summary;

    // Extract custom ID like [BE-001] or [FE-02] from the beginning of the summary
    const match = issue.summary?.match(/^\[(.*?)\]\s*(.*)/);
    if (match) {
      displayId = match[1];
      displaySummary = match[2];
    }

    return (
      <article
        key={issue.key}
        draggable={actionLoading !== issue.key}
        onDragStart={(e) => {
          e.dataTransfer.setData('text/plain', issue.key);
          e.dataTransfer.effectAllowed = 'move';
          setDraggingKey(issue.key);
        }}
        onDragEnd={() => {
          setDraggingKey(null);
          setDropTarget(null);
        }}
        className={`group relative cursor-grab rounded-lg border bg-white p-4 shadow-sm transition-colors active:cursor-grabbing ${draggingKey === issue.key
            ? 'scale-[0.98] border-blue-300 opacity-50'
            : actionLoading === issue.key
              ? 'pointer-events-none border-slate-200 opacity-60'
              : 'border-slate-200 hover:border-slate-400'
          }`}
      >
        {actionLoading === issue.key && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/70">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
          </div>
        )}

        <div className="mb-3 flex items-start justify-between gap-3">
          <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-black text-blue-800 ring-1 ring-blue-100" title={displayId !== issue.key ? `Jira Key: ${issue.key}` : ''}>
            {displayId}
          </span>
          <div className="flex items-center gap-1">
            {confirmDelete === issue.key ? (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => handleDelete(issue.key)}
                  className="rounded-md bg-red-600 px-2 py-1 text-[11px] font-bold text-white transition-colors hover:bg-red-700"
                  title={t('sprint_board.confirm_delete')}
                >
                      {t('common.delete')}
                </button>
                <button
                  onClick={() => setConfirmDelete(null)}
                  className="rounded-md bg-slate-100 px-2 py-1 text-[11px] font-bold text-slate-700 transition-colors hover:bg-slate-200"
                  title={t('common.cancel')}
                >
                    {t('common.cancel')}
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(issue.key)}
                className="rounded-md p-1 text-slate-500 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-600 group-hover:opacity-100 focus:opacity-100"
                title={t('sprint_board.delete_issue')}
              >
                <span className="material-symbols-outlined text-[16px]">delete</span>
              </button>
            )}
            <span className="material-symbols-outlined text-[16px] text-slate-500" title={issue.type}>
              {issue.type === 'Story' ? 'bookmark' : 'task'}
            </span>
          </div>
        </div>
        <p className="mb-4 line-clamp-3 text-sm font-semibold leading-6 text-slate-950" title={displaySummary}>
          {displaySummary}
        </p>
        <div className="flex items-center justify-between gap-3">
          <div className="inline-flex h-7 min-w-7 items-center justify-center rounded-full bg-slate-100 px-2 text-[10px] font-black text-slate-700 ring-1 ring-slate-200" title={issue.assignee ? (issue.assignee.displayName || issue.assignee.name || issue.assignee) : t('sprint_board.unassigned')}>
            {issue.assignee ? (typeof issue.assignee === 'string' ? issue.assignee : (issue.assignee.displayName || issue.assignee.name || 'UA')).substring(0, 2).toUpperCase() : 'UA'}
          </div>
          {issue.parent_key && groupBy === 'none' && (
            <span className="max-w-[96px] truncate rounded-md border border-slate-200 px-1.5 py-0.5 text-[10px] font-bold text-slate-600" title={`${t('sprint_board.parent_label')}: ${issue.parent_key}`}>
              {issue.parent_key}
            </span>
          )}
        </div>
      </article>
    );
  };

  return (
    <div className="flex h-full flex-col space-y-5">
      <header className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0">
          <h2 className="flex items-center gap-2 text-2xl font-black tracking-[-0.02em] text-slate-950">
            <span className="material-symbols-outlined text-[26px] text-slate-700">view_kanban</span>
            {sprint.name}
          </h2>
            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm font-semibold text-slate-700">
              <span className="inline-flex items-center gap-1.5"><span className="material-symbols-outlined text-[16px] text-slate-500">flag</span>{t('sprint_board.goal')}: {sprint.goal || t('sprint_board.none')}</span>
              <span className="inline-flex items-center gap-1.5"><span className="material-symbols-outlined text-[16px] text-slate-500">calendar_today</span>{t('sprint_board.start_date')}: {sprint.start_date ? new Date(sprint.start_date).toLocaleDateString() : t('common.not_available')}</span>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
            <label className="flex min-h-11 items-center rounded-lg border border-slate-300 bg-white px-3 text-sm shadow-sm">
              <span className="mr-2 whitespace-nowrap font-semibold text-slate-700">{t('sprint_board.group_by')}</span>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
                className="cursor-pointer border-none bg-transparent py-0 pl-0 pr-8 text-sm font-bold text-slate-950 focus:ring-0"
            >
              <option value="none">{t('sprint_board.none_group')}</option>
              <option value="subtask">{t('sprint_board.subtask')}</option>
            </select>
            </label>

          <button
            onClick={loadBoard}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-sm font-bold text-slate-800 shadow-sm transition-colors hover:bg-slate-50 sm:w-11 sm:px-0"
            title={t('sprint_board.sync_jira')}
          >
              <span className="material-symbols-outlined text-[20px]">sync</span>
              <span className="sm:sr-only">{t('sprint_board.sync_jira')}</span>
          </button>

          <button
            onClick={() => setShowCompleteModal(true)}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-blue-700 px-5 text-sm font-black text-white shadow-sm shadow-blue-700/20 transition-colors hover:bg-blue-800"
          >
            <span className="material-symbols-outlined text-[18px]">done_all</span>
            {t('sprint_board.complete_sprint')}
          </button>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-x-auto overflow-y-auto">
        {groupBy === 'none' ? (
          /* Flat Board */
          <div className="flex h-full min-w-max gap-4 pb-4">
            {[['todo', t('sprint_board.column_todo')], ['in_progress', t('sprint_board.column_in_progress')], ['done', t('sprint_board.column_done')]].map(([colKey, colLabel]) => {
              // Hide subtasks in flat board view to reduce clutter
              const flatIssues = issues.filter(i => classifyIssue(i.status) === colKey && i.type !== 'Subtask');
              return renderColumn(colKey, flatIssues, '', colLabel);
            })}
          </div>
        ) : (
          /* Grouped by Subtask (Swimlanes) */
          <div className="min-w-[900px] space-y-4 pb-4">
            {(() => {
              // Extract unique parent keys (including those that don't have parents)
              const groups = {};
              // Group issues
              issues.forEach(issue => {
                const isStory = issue.type === 'Story' || !issue.parent_key;
                const groupKey = isStory ? issue.key : (issue.parent_key || 'Unparented');

                if (!groups[groupKey]) {
                  groups[groupKey] = {
                    parent: isStory ? issue : issues.find(i => i.key === groupKey), // Try to find parent object if it's in the sprint
                    items: []
                  };
                }
                if (!isStory) {
                  groups[groupKey].items.push(issue);
                }
              });

              return Object.entries(groups).map(([groupKey, data]) => (
                <section key={groupKey} className="flex flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                  {/* Swimlane Header (Parent) */}
                  <div className="flex min-h-12 items-center gap-3 border-b border-slate-200 bg-slate-50 px-4 py-3">
                    <span className="material-symbols-outlined text-[20px] text-slate-600">
                      {data.parent?.type === 'Story' ? 'bookmark' : 'folder'}
                    </span>
                    <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-black text-blue-800 ring-1 ring-blue-100">
                      {groupKey}
                    </span>
                    <span className="max-w-xl truncate text-sm font-semibold text-slate-900">
                      {data.parent?.summary || t('sprint_board.other_issues')}
                    </span>
                  </div>

                  {/* Swimlane Columns */}
                  <div className="flex divide-x divide-slate-200">
                    {[['todo', t('sprint_board.column_todo')], ['in_progress', t('sprint_board.column_in_progress')], ['done', t('sprint_board.column_done')]].map(([colKey, colLabel]) => {
                      const colIssues = data.items.filter(i => classifyIssue(i.status) === colKey);
                      // Custom inline column renderer for swimlanes
                      const targetDropId = `${groupKey}-${colKey}`;
                      return (
                        <div
                          key={colKey}
                          className={`min-h-[140px] flex-1 p-3 transition-colors ${dropTarget === targetDropId ? 'bg-blue-50' : 'bg-white'
                            }`}
                          onDragOver={(e) => {
                            e.preventDefault();
                            setDropTarget(targetDropId);
                          }}
                          onDragLeave={() => setDropTarget(null)}
                          onDrop={(e) => {
                            e.preventDefault();
                            setDropTarget(null);
                            const issueKey = e.dataTransfer.getData('text/plain');
                            if (issueKey) handleDrop(issueKey, colKey);
                          }}
                        >
                          <div className="mb-3 flex items-center justify-between">
                            <span className="text-xs font-black uppercase tracking-[0.14em] text-slate-700">{colLabel}</span>
                            {colIssues.length > 0 && (
                              <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-black text-slate-700">
                                {colIssues.length}
                              </span>
                            )}
                          </div>
                          <div className="space-y-2">
                            {colIssues.map(issue => renderIssueCard(issue))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              ));
            })()}
          </div>
        )}
      </div>

      {/* Complete Sprint Modal */}
      {showCompleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 p-4">
          <div className="w-full max-w-lg overflow-hidden rounded-lg border border-slate-200 bg-white shadow-2xl shadow-slate-950/20">
            <div className="border-b border-slate-200 px-6 py-5">
              <div className="flex items-start gap-3">
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-700">
                  <span className="material-symbols-outlined text-[22px]">done_all</span>
                </div>
                <div className="min-w-0">
                  <h2 className="text-lg font-black text-slate-950">
                    {t('sprint_board.complete_sprint')} {sprint.name}
                  </h2>
                  <p className="mt-1 text-sm font-medium leading-6 text-slate-700">
                    {t('sprint_board.sprint_contains')} <strong>{completedCount} {t('sprint_board.completed')}</strong> {t('sprint_board.work_items_and')} <strong>{openCount} {t('sprint_board.open')}</strong> {t('sprint_board.work_items')}
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-5 p-6">
              {openCount > 0 && (
                <div className="space-y-2">
                  <label className="block text-sm font-bold text-slate-900">
                    {t('sprint_board.move_open_to')}
                  </label>
                  <select
                    value={moveOpenTo}
                    onChange={(e) => setMoveOpenTo(e.target.value)}
                    className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-950 outline-none transition focus:border-blue-400 focus:ring-4 focus:ring-blue-100"
                  >
                    <option value="new_sprint">{t('sprint_board.new_sprint')}</option>
                    <option value="backlog">{t('sprint_board.backlog')}</option>
                  </select>
                </div>
              )}

              <div className="flex justify-end gap-3 border-t border-slate-200 pt-5">
                <button
                  onClick={() => setShowCompleteModal(false)}
                  disabled={completeLoading}
                  className="inline-flex min-h-10 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 text-sm font-bold text-slate-800 transition-colors hover:bg-slate-50 disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={handleCompleteSprint}
                  disabled={completeLoading}
                  className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 text-sm font-black text-white shadow-sm shadow-blue-700/20 transition-colors hover:bg-blue-800 disabled:opacity-50"
                >
                  {completeLoading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />}
                  {t('sprint_board.complete_sprint')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
