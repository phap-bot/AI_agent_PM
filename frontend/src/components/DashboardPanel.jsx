import React, { useState, useEffect } from 'react';
import { fetchManagementDashboard } from '../lib/api';
import { useTranslation } from 'react-i18next';

// ── Helpers ──

function statusDotColor(statusCategory) {
  if (statusCategory === 'done') return 'bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.5)]';
  if (statusCategory === 'indeterminate') return 'bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.5)]';
  return 'bg-gray-400';
}

function priorityBadge(priority) {
  const p = (priority || '').toUpperCase();
  if (p === 'HIGHEST' || p === 'CRITICAL')
    return 'bg-red-100 text-red-700 border border-red-200';
  if (p === 'HIGH')
    return 'bg-orange-100 text-orange-700 border border-orange-200';
  if (p === 'MEDIUM')
    return 'bg-yellow-100 text-yellow-700 border border-yellow-200';
  if (p === 'LOW')
    return 'bg-green-100 text-green-700 border border-green-200';
  if (p === 'LOWEST')
    return 'bg-slate-100 text-slate-600 border border-slate-200';
  return 'bg-surface-container-highest text-on-surface-variant';
}

export default function DashboardPanel({ projectId }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let intervalId;
    async function loadData(showLoading = false) {
      if (showLoading) setLoading(true);
      try {
        const response = await fetchManagementDashboard(projectId);
        console.log("Dashboard API Data:", response);
        setData(response);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        if (showLoading) setLoading(false);
      }
    }
    
    // Initial load with loading spinner
    loadData(true);
    
    // Auto-refresh every 5 seconds without showing loading spinner
    intervalId = setInterval(() => loadData(false), 5000);

    return () => clearInterval(intervalId);
  }, [projectId]);

  const sb = data?.statusBreakdown || { todo: 0, in_progress: 0, done: 0 };
  const totalIssues = sb.todo + sb.in_progress + sb.done;
  const burndownMax = Math.max(totalIssues, 1);

  return (
    <div className="flex-1 overflow-y-auto p-container-padding custom-scrollbar">
      {/* Welcome Header */}
      <section className="mb-stack-lg flex justify-between items-end">
        <div>
          <h3 className="font-display-lg text-display-lg text-on-surface mb-2">{t('dashboard.welcome')}</h3>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full font-label-md">{data?.sprintName || t('dashboard.no_active_sprint')}</span>
            {data?.jiraConnected && (
              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px] font-bold border border-green-200 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                {t('dashboard.jira_live')}
              </span>
            )}
            <div className="flex items-center gap-2">
              <div className="w-48 h-2 bg-surface-container-highest rounded-full overflow-hidden">
                <div className="bg-primary h-full transition-all duration-1000 ease-out" style={{ width: `${data?.sprintProgress || 0}%` }}></div>
              </div>
              <span className="font-label-md text-on-surface-variant">{data?.sprintProgress || 0}% {t('dashboard.complete')}</span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <p className="font-label-md text-on-surface-variant">{t('dashboard.estimated_finish')}</p>
          <p className="font-headline-sm text-headline-sm text-on-surface">{data?.sprintEndDate || '--'}</p>
        </div>
      </section>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-stack-md mb-stack-lg">
        {/* Total Tickets */}
        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">{t('dashboard.total_tickets')}</p>
            <p className="font-display-lg text-display-lg text-on-surface">{data?.totalTickets || 0}</p>
          </div>
          <div className="mt-4 flex items-center gap-1 text-tertiary font-label-md">
            <span className="material-symbols-outlined text-sm">trending_up</span>
            <span>{data?.totalTicketsTrend || '--'}</span>
          </div>
        </div>

        {/* AI Confidence */}
        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">{t('dashboard.ai_confidence')}</p>
            <p className="font-display-lg text-display-lg text-primary">{data?.aiConfidenceScore || 0}%</p>
          </div>
          <div className="mt-4 flex items-center gap-1 text-on-surface-variant font-label-md">
            <span className="material-symbols-outlined text-sm">verified</span>
            <span>{t('dashboard.high_precision')}</span>
          </div>
        </div>

        {/* Team Velocity (with sprint points) */}
        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">{t('dashboard.team_velocity')}</p>
            <p className="font-display-lg text-display-lg text-on-surface">{data?.teamVelocity || 0}<span className="text-label-md text-on-surface-variant font-normal">{t('dashboard.pts')}</span></p>
          </div>
          <div className="mt-4 flex items-center gap-1 text-tertiary font-label-md">
            <span className="material-symbols-outlined text-sm">bolt</span>
            {data?.jiraConnected ? (
              <span>{data?.doneSprintPoints?.toFixed(0) || 0}/{data?.totalSprintPoints?.toFixed(0) || 0} {t('dashboard.sp_done')}</span>
            ) : (
              <span>{t('dashboard.optimal_performance')}</span>
            )}
          </div>
        </div>

        {/* Sprint Burndown (real data) */}
        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between overflow-hidden relative">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">{t('dashboard.sprint_burndown')}</p>
          </div>
          {totalIssues > 0 ? (
            <div className="flex gap-2 mt-2 h-20 w-full">
              {/* To Do bar */}
              <div className="flex-1 h-full flex flex-col items-center">
                <span className="text-[9px] font-bold text-on-surface-variant h-4">{sb.todo}</span>
                <div className="w-full flex-1 relative">
                  <div
                    className="bg-gray-400 absolute bottom-0 w-full rounded-t-sm transition-all duration-700"
                    style={{ height: `${(sb.todo / burndownMax) * 100}%`, minHeight: sb.todo > 0 ? '4px' : '0px' }}
                  ></div>
                </div>
                <span className="text-[8px] text-on-surface-variant h-3 mt-1">{t('dashboard.todo')}</span>
              </div>
              {/* In Progress bar */}
              <div className="flex-1 h-full flex flex-col items-center">
                <span className="text-[9px] font-bold text-on-surface-variant h-4">{sb.in_progress}</span>
                <div className="w-full flex-1 relative">
                  <div
                    className="bg-blue-500 absolute bottom-0 w-full rounded-t-sm transition-all duration-700"
                    style={{ height: `${(sb.in_progress / burndownMax) * 100}%`, minHeight: sb.in_progress > 0 ? '4px' : '0px' }}
                  ></div>
                </div>
                <span className="text-[8px] text-on-surface-variant h-3 mt-1">{t('dashboard.wip')}</span>
              </div>
              {/* Done bar */}
              <div className="flex-1 h-full flex flex-col items-center">
                <span className="text-[9px] font-bold text-on-surface-variant h-4">{sb.done}</span>
                <div className="w-full flex-1 relative">
                  <div
                    className="bg-green-500 absolute bottom-0 w-full rounded-t-sm transition-all duration-700"
                    style={{ height: `${(sb.done / burndownMax) * 100}%`, minHeight: sb.done > 0 ? '4px' : '0px' }}
                  ></div>
                </div>
                <span className="text-[8px] text-on-surface-variant h-3 mt-1">{t('dashboard.done')}</span>
              </div>
            </div>
          ) : (
            <div className="h-16 w-full flex items-end gap-1 mt-2">
              <div className="bg-outline-variant w-full h-[90%] rounded-t-sm"></div>
              <div className="bg-outline-variant w-full h-[80%] rounded-t-sm"></div>
              <div className="bg-outline-variant w-full h-[75%] rounded-t-sm"></div>
              <div className="bg-outline-variant w-full h-[60%] rounded-t-sm"></div>
              <div className="bg-primary w-full h-[50%] rounded-t-sm"></div>
              <div className="bg-primary w-full h-[35%] rounded-t-sm"></div>
              <div className="bg-primary w-full h-[20%] rounded-t-sm"></div>
            </div>
          )}
        </div>
      </div>

      {/* Bento Layout Content */}
      <div className="grid grid-cols-12 gap-stack-md">
        {/* Active Tickets Table (8/12) */}
        <div className="col-span-12 lg:col-span-8 bg-surface border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-gutter py-4 border-b border-outline-variant flex justify-between items-center">
            <h4 className="font-headline-sm text-headline-sm text-on-surface">{t('dashboard.active_tickets')}</h4>
            <button className="text-primary font-label-md flex items-center gap-1">
              {t('dashboard.view_all')} <span className="material-symbols-outlined text-sm">chevron_right</span>
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-body-md">
              <thead className="bg-surface-container-low text-on-surface-variant">
                <tr>
                  <th className="px-gutter py-3 font-label-md">{t('dashboard.ticket_title')}</th>
                  <th className="px-gutter py-3 font-label-md">{t('dashboard.ai_agents')}</th>
                  <th className="px-gutter py-3 font-label-md">{t('dashboard.priority')}</th>
                  <th className="px-gutter py-3 font-label-md">{t('dashboard.sp')}</th>
                  <th className="px-gutter py-3 font-label-md">{t('dashboard.status')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {data?.activeSprintTickets?.length > 0 ? (
                  data.activeSprintTickets.map((ticket, idx) => (
                    <tr key={ticket.key || idx} className="hover:bg-surface-container-low transition-colors">
                      <td className="px-gutter py-4 font-semibold text-on-surface">{ticket.title}</td>
                      <td className="px-gutter py-4">
                        <div className="flex gap-1">
                          {ticket.agents.map((agent, i) => {
                            const bg = agent === 'R' ? 'bg-blue-100 text-blue-700 border-blue-200' : 
                                       agent === 'P' ? 'bg-indigo-100 text-indigo-700 border-indigo-200' :
                                       agent === 'E' ? 'bg-green-100 text-green-700 border-green-200' :
                                       'bg-gray-100 text-gray-700 border-gray-200';
                            return (
                              <span key={i} className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border ${bg}`}>{agent}</span>
                            );
                          })}
                        </div>
                      </td>
                      <td className="px-gutter py-4">
                        <span className={`px-2 py-0.5 rounded font-label-md text-[11px] ${priorityBadge(ticket.priority)}`}>
                          {ticket.priority}
                        </span>
                      </td>
                      <td className="px-gutter py-4 text-center">
                        <span className="font-mono text-sm font-semibold text-on-surface-variant">
                          {ticket.story_points > 0 ? ticket.story_points : '-'}
                        </span>
                      </td>
                      <td className="px-gutter py-4">
                        <span className="flex items-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${statusDotColor(ticket.status_category)}`}></span>
                          {ticket.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-gutter py-8 text-center text-on-surface-variant">
                      {t('dashboard.no_tickets_found')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Insights Section (4/12) */}
        <div className="col-span-12 lg:col-span-4 space-y-stack-md">
          <div className="bg-surface border border-outline-variant rounded-xl p-container-padding ai-insight-accent relative overflow-hidden" style={{borderLeft: "4px solid #4b41e1"}}>
            <div className="absolute top-2 right-2 opacity-10">
              <span className="material-symbols-outlined text-6xl">smart_toy</span>
            </div>
            <div className="flex items-center gap-2 text-secondary mb-4">
              <span className="material-symbols-outlined">auto_awesome</span>
              <h4 className="font-headline-sm text-headline-sm">{t('dashboard.ai_insight')}</h4>
            </div>
            <p className="font-body-lg text-body-lg text-on-surface mb-6">
              {data?.agentInsight || t('dashboard.loading_insights')}
            </p>
            <div className="space-y-3">
              <button className="w-full py-2 px-4 bg-secondary text-on-secondary rounded-lg font-label-md flex justify-between items-center group transition-all">
                {t('dashboard.review_tasks')}
                <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
              </button>
              <button className="w-full py-2 px-4 border border-outline-variant text-on-surface-variant rounded-lg font-label-md hover:bg-surface-container-low">
                {t('dashboard.dismiss_suggestion')}
              </button>
            </div>
          </div>

          <div className="bg-surface border border-outline-variant rounded-xl p-container-padding">
            <h4 className="font-label-md text-on-surface-variant uppercase tracking-wider mb-4">{t('dashboard.system_health')}</h4>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${data?.agentHealth?.researcher === 'Active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-amber-500 animate-pulse'}`}></div>
                  <span className="font-body-md">{t('dashboard.researcher_agent')}</span>
                </div>
                <span className="font-mono-sm text-on-surface-variant">{data?.agentHealth?.researcher || '...'}</span>
              </div>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${data?.agentHealth?.planner === 'Active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-amber-500 animate-pulse'}`}></div>
                  <span className="font-body-md">{t('dashboard.planner_agent')}</span>
                </div>
                <span className="font-mono-sm text-on-surface-variant">{data?.agentHealth?.planner || '...'}</span>
              </div>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${data?.agentHealth?.evaluator === 'Active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-amber-500 animate-pulse'}`}></div>
                  <span className="font-body-md">{t('dashboard.evaluator_agent')}</span>
                </div>
                <span className="font-mono-sm text-on-surface-variant">{data?.agentHealth?.evaluator || '...'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
