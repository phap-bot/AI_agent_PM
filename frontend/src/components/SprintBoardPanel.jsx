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
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-error-container text-on-error-container rounded-lg">
        {t('sprint_board.load_error')} {error}
      </div>
    );
  }

  if (!boardData?.sprint) {
    return (
      <div className="text-center p-12 bg-surface-container-lowest rounded-2xl border border-outline-variant/30 text-on-surface-variant flex flex-col items-center justify-center gap-4">
        <span className="material-symbols-outlined text-4xl text-outline">calendar_month</span>
        <p>{t('sprint_board.no_active_sprint_desc')}</p>
        <button
          onClick={loadBoard}
          className="flex items-center gap-2 bg-primary/10 text-primary hover:bg-primary/20 px-4 py-2 rounded-full transition-colors"
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
      <div
        key={targetDropId}
        className={`flex-1 flex flex-col min-w-[300px] rounded-2xl p-4 border transition-all duration-200 ${dropTarget === targetDropId
            ? 'bg-primary/5 border-primary/50 ring-2 ring-primary/20'
            : 'bg-surface-container-low border-outline-variant'
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
        <div className="flex justify-between items-center mb-4 px-2">
          <h3 className="font-bold text-title-md text-on-surface uppercase tracking-wider text-sm">{displayLabel}</h3>
          <span className="bg-surface-container-high px-2 py-1 rounded-full text-xs font-bold text-on-surface-variant">
            {colIssues.length}
          </span>
        </div>

        <div className="flex-1 space-y-3 custom-scrollbar px-2 pb-2 min-h-[100px]">
          {colIssues.map(issue => renderIssueCard(issue))}

          {colIssues.length === 0 && (
            <div className={`h-24 border-2 border-dashed rounded-xl flex items-center justify-center text-sm transition-colors ${dropTarget === targetDropId
                ? 'border-primary/50 text-primary bg-primary/5'
                : 'border-outline-variant/50 text-outline'
              }`}>
              {dropTarget === targetDropId ? t('sprint_board.drop_here') : ''}
            </div>
          )}
        </div>
      </div>
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
      <div
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
        className={`bg-surface p-4 rounded-xl shadow-sm border transition-all duration-200 cursor-grab active:cursor-grabbing relative group ${draggingKey === issue.key
            ? 'opacity-40 scale-95 border-primary/30'
            : actionLoading === issue.key
              ? 'opacity-60 pointer-events-none border-outline-variant'
              : 'border-outline-variant hover:border-primary/50 hover:shadow-md'
          }`}
      >
        {actionLoading === issue.key && (
          <div className="absolute inset-0 flex items-center justify-center bg-surface/60 rounded-xl z-10">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
          </div>
        )}

        <div className="flex justify-between items-start mb-2">
          <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded" title={displayId !== issue.key ? `Jira Key: ${issue.key}` : ''}>
            {displayId}
          </span>
          <div className="flex items-center gap-1">
            {confirmDelete === issue.key ? (
              <div className="flex items-center gap-1 animate-in fade-in duration-150">
                <button
                  onClick={() => handleDelete(issue.key)}
                  className="text-[11px] px-2 py-0.5 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                  title={t('sprint_board.confirm_delete')}
                >
                      {t('common.delete')}
                </button>
                <button
                  onClick={() => setConfirmDelete(null)}
                  className="text-[11px] px-2 py-0.5 bg-surface-container-high text-on-surface-variant rounded hover:bg-surface-container-highest transition-colors"
                  title={t('common.cancel')}
                >
                    {t('common.cancel')}
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(issue.key)}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-outline hover:text-red-500 p-0.5 rounded"
                title={t('sprint_board.delete_issue')}
              >
                <span className="material-symbols-outlined text-[16px]">delete</span>
              </button>
            )}
            <span className="material-symbols-outlined text-outline text-[16px]" title={issue.type}>
              {issue.type === 'Story' ? 'bookmark' : 'task'}
            </span>
          </div>
        </div>
        <p className="text-body-md text-on-surface font-medium line-clamp-3 mb-3" title={displaySummary}>
          {displaySummary}
        </p>
        <div className="flex justify-between items-center">
          <div className="w-6 h-6 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container text-[10px] font-bold" title={issue.assignee ? (issue.assignee.displayName || issue.assignee.name || issue.assignee) : t('sprint_board.unassigned')}>
            {issue.assignee ? (typeof issue.assignee === 'string' ? issue.assignee : (issue.assignee.displayName || issue.assignee.name || '??')).substring(0, 2).toUpperCase() : '??'}
          </div>
          {issue.parent_key && groupBy === 'none' && (
            <span className="text-[10px] font-bold text-outline border border-outline-variant px-1 rounded truncate max-w-[80px]" title={`${t('sprint_board.parent_label')}: ${issue.parent_key}`}>
              {issue.parent_key}
            </span>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 h-full flex flex-col">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-surface-container-low p-4 rounded-2xl border border-outline-variant/50">
        <div>
          <h2 className="text-headline-md font-headline-md text-primary flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">skateboarding</span>
            {sprint.name}
          </h2>
          <div className="flex items-center gap-4 text-on-surface-variant text-label-md mt-1">
            <span className="flex items-center gap-1"><span className="material-symbols-outlined text-[16px]">flag</span> {t('sprint_board.goal')}: {sprint.goal || t('sprint_board.none')}</span>
            <span className="flex items-center gap-1"><span className="material-symbols-outlined text-[16px]">calendar_today</span> {t('sprint_board.start_date')}: {sprint.start_date ? new Date(sprint.start_date).toLocaleDateString() : t('common.not_available')}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-surface rounded-full border border-outline-variant p-1">
            <span className="text-xs font-medium text-on-surface-variant px-2">{t('sprint_board.group_by')}</span>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="text-sm bg-transparent border-none py-1 pr-6 focus:ring-0 cursor-pointer text-on-surface font-medium"
            >
              <option value="none">{t('sprint_board.none_group')}</option>
              <option value="subtask">{t('sprint_board.subtask')}</option>
            </select>
          </div>

          <button
            onClick={loadBoard}
            className="flex items-center justify-center p-2 rounded-full bg-surface-container border border-outline-variant hover:bg-surface-container-high transition-colors text-on-surface-variant tooltip-trigger"
            title={t('sprint_board.sync_jira')}
          >
            <span className="material-symbols-outlined text-xl">sync</span>
          </button>

          <button
            onClick={() => setShowCompleteModal(true)}
            className="flex items-center gap-2 bg-primary text-on-primary hover:bg-primary/90 px-4 py-2 rounded-full transition-colors shadow-sm font-medium text-sm"
          >
            <span className="material-symbols-outlined text-[18px]">done_all</span>
            {t('sprint_board.complete_sprint')}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-x-auto overflow-y-auto">
        {groupBy === 'none' ? (
          /* Flat Board */
          <div className="flex gap-6 h-full min-w-max pb-4">
            {[['todo', t('sprint_board.column_todo')], ['in_progress', t('sprint_board.column_in_progress')], ['done', t('sprint_board.column_done')]].map(([colKey, colLabel]) => {
              // Hide subtasks in flat board view to reduce clutter
              const flatIssues = issues.filter(i => classifyIssue(i.status) === colKey && i.type !== 'Subtask');
              return renderColumn(colKey, flatIssues, '', colLabel);
            })}
          </div>
        ) : (
          /* Grouped by Subtask (Swimlanes) */
          <div className="space-y-6 pb-4 min-w-[900px]">
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
                <div key={groupKey} className="flex flex-col bg-surface rounded-2xl border border-outline-variant overflow-hidden">
                  {/* Swimlane Header (Parent) */}
                  <div className="bg-surface-container-lowest border-b border-outline-variant p-3 flex items-center gap-3">
                    <span className="material-symbols-outlined text-primary text-[20px]">
                      {data.parent?.type === 'Story' ? 'bookmark' : 'folder'}
                    </span>
                    <span className="font-bold text-primary bg-primary/10 px-2 py-0.5 rounded text-xs">
                      {groupKey}
                    </span>
                    <span className="font-medium text-on-surface text-sm truncate max-w-xl">
                      {data.parent?.summary || t('sprint_board.other_issues')}
                    </span>
                  </div>

                  {/* Swimlane Columns */}
                  <div className="flex gap-0 divide-x divide-outline-variant/30">
                    {[['todo', t('sprint_board.column_todo')], ['in_progress', t('sprint_board.column_in_progress')], ['done', t('sprint_board.column_done')]].map(([colKey, colLabel]) => {
                      const colIssues = data.items.filter(i => classifyIssue(i.status) === colKey);
                      // Custom inline column renderer for swimlanes
                      const targetDropId = `${groupKey}-${colKey}`;
                      return (
                        <div
                          key={colKey}
                          className={`flex-1 p-3 min-h-[120px] transition-colors ${dropTarget === targetDropId ? 'bg-primary/5' : 'bg-surface/50'
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
                          <div className="flex justify-between items-center mb-3">
                            <span className="text-xs font-bold text-on-surface-variant uppercase">{colLabel}</span>
                            {colIssues.length > 0 && (
                              <span className="text-[10px] font-bold bg-surface-container-high px-1.5 py-0.5 rounded text-on-surface-variant">
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
                </div>
              ));
            })()}
          </div>
        )}
      </div>

      {/* Complete Sprint Modal */}
      {showCompleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in">
          <div className="bg-surface rounded-3xl shadow-xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
            {/* Header with image/gradient */}
            <div className="h-32 bg-gradient-to-br from-primary to-tertiary relative flex items-center justify-center">
              {/* Star/Trophy Icon */}
              <div className="w-16 h-16 bg-white rounded-full shadow-lg flex items-center justify-center border-4 border-yellow-400 text-yellow-500">
                <span className="material-symbols-outlined text-3xl">trophy</span>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <h2 className="text-headline-sm font-bold text-on-surface">
                {t('sprint_board.complete_sprint')} {sprint.name}
              </h2>

              <p className="text-body-md text-on-surface-variant">
                {t('sprint_board.sprint_contains')} <strong>{completedCount} {t('sprint_board.completed')}</strong> {t('sprint_board.work_items_and')} <strong>{openCount} {t('sprint_board.open')}</strong> {t('sprint_board.work_items')}
              </p>

              {openCount > 0 && (
                <div className="space-y-2">
                  <label className="text-label-md font-medium text-on-surface block">
                    {t('sprint_board.move_open_to')}
                  </label>
                  <select
                    value={moveOpenTo}
                    onChange={(e) => setMoveOpenTo(e.target.value)}
                    className="w-full rounded-xl border-outline-variant bg-surface px-4 py-3 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all"
                  >
                    <option value="new_sprint">{t('sprint_board.new_sprint')}</option>
                    <option value="backlog">{t('sprint_board.backlog')}</option>
                  </select>
                </div>
              )}

              <div className="pt-6 flex justify-end gap-3">
                <button
                  onClick={() => setShowCompleteModal(false)}
                  disabled={completeLoading}
                  className="px-5 py-2.5 rounded-full text-primary hover:bg-primary/10 font-medium transition-colors disabled:opacity-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={handleCompleteSprint}
                  disabled={completeLoading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-on-primary hover:bg-primary/90 font-medium transition-colors shadow-sm disabled:opacity-50"
                >
                  {completeLoading && <span className="material-symbols-outlined animate-spin text-[18px]">sync</span>}
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
