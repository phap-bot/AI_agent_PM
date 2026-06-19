import React, { useEffect, useState } from 'react';
import { fetchManagementDashboard } from '../lib/api';

export default function DashboardPanel({ projectId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const response = await fetchManagementDashboard(projectId);
        setData(response);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [projectId]);

  return (
    <div className="flex-1 overflow-y-auto p-container-padding custom-scrollbar">
      {/* Welcome Header */}
      <section className="mb-stack-lg flex justify-between items-end">
        <div>
          <h3 className="font-display-lg text-display-lg text-on-surface mb-2">Welcome back, Scrum Lead</h3>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 bg-secondary-container text-on-secondary-container rounded-full font-label-md">{data?.sprintName || 'No Active Sprint'}</span>
            <div className="flex items-center gap-2">
              <div className="w-48 h-2 bg-surface-container-highest rounded-full overflow-hidden">
                <div className="bg-primary h-full transition-all duration-1000 ease-out" style={{ width: `${data?.sprintProgress || 0}%` }}></div>
              </div>
              <span className="font-label-md text-on-surface-variant">{data?.sprintProgress || 0}% Complete</span>
            </div>
          </div>
        </div>
        <div className="text-right">
          <p className="font-label-md text-on-surface-variant">Estimated Finish</p>
          <p className="font-headline-sm text-headline-sm text-on-surface">{data?.sprintEndDate || '--'}</p>
        </div>
      </section>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-stack-md mb-stack-lg">
        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">Total Tickets Created</p>
            <p className="font-display-lg text-display-lg text-on-surface">{data?.totalTickets || 0}</p>
          </div>
          <div className="mt-4 flex items-center gap-1 text-tertiary font-label-md">
            <span className="material-symbols-outlined text-sm">trending_up</span>
            <span>{data?.totalTicketsTrend || '--'}</span>
          </div>
        </div>

        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">AI Confidence Score</p>
            <p className="font-display-lg text-display-lg text-primary">{data?.aiConfidenceScore || 0}%</p>
          </div>
          <div className="mt-4 flex items-center gap-1 text-on-surface-variant font-label-md">
            <span className="material-symbols-outlined text-sm">verified</span>
            <span>High Precision Active</span>
          </div>
        </div>

        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">Team Velocity</p>
            <p className="font-display-lg text-display-lg text-on-surface">{data?.teamVelocity || 0}<span className="text-label-md text-on-surface-variant font-normal">pts/s</span></p>
          </div>
          <div className="mt-4 flex items-center gap-1 text-tertiary font-label-md">
            <span className="material-symbols-outlined text-sm">bolt</span>
            <span>Optimal Performance</span>
          </div>
        </div>

        <div className="bg-surface border border-outline-variant p-4 rounded-xl flex flex-col justify-between overflow-hidden relative">
          <div>
            <p className="font-label-md text-on-surface-variant mb-1">Sprint Burndown</p>
          </div>
          <div className="h-16 w-full flex items-end gap-1 mt-2">
            <div className="bg-outline-variant w-full h-[90%] rounded-t-sm"></div>
            <div className="bg-outline-variant w-full h-[80%] rounded-t-sm"></div>
            <div className="bg-outline-variant w-full h-[75%] rounded-t-sm"></div>
            <div className="bg-outline-variant w-full h-[60%] rounded-t-sm"></div>
            <div className="bg-primary w-full h-[50%] rounded-t-sm"></div>
            <div className="bg-primary w-full h-[35%] rounded-t-sm"></div>
            <div className="bg-primary w-full h-[20%] rounded-t-sm"></div>
          </div>
        </div>
      </div>

      {/* Bento Layout Content */}
      <div className="grid grid-cols-12 gap-stack-md">
        {/* Active Tickets Table (8/12) */}
        <div className="col-span-12 lg:col-span-8 bg-surface border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-gutter py-4 border-b border-outline-variant flex justify-between items-center">
            <h4 className="font-headline-sm text-headline-sm text-on-surface">Active Sprint Tickets</h4>
            <button className="text-primary font-label-md flex items-center gap-1">
              View All <span className="material-symbols-outlined text-sm">chevron_right</span>
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left font-body-md">
              <thead className="bg-surface-container-low text-on-surface-variant">
                <tr>
                  <th className="px-gutter py-3 font-label-md">Ticket Title</th>
                  <th className="px-gutter py-3 font-label-md">AI Agents</th>
                  <th className="px-gutter py-3 font-label-md">Priority</th>
                  <th className="px-gutter py-3 font-label-md">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {data?.activeSprintTickets?.map((ticket, idx) => (
                  <tr key={idx}>
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
                      <span className={`px-2 py-0.5 rounded font-label-md ${ticket.priority === 'CRITICAL' ? 'bg-error-container text-on-error-container' : 'bg-surface-container-highest text-on-surface-variant'}`}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-gutter py-4">
                      <span className="flex items-center gap-1.5">
                        <span className={`w-2 h-2 rounded-full ${ticket.status === 'In Progress' ? 'bg-primary' : 'bg-tertiary'}`}></span>
                        {ticket.status}
                      </span>
                    </td>
                  </tr>
                ))}
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
              <h4 className="font-headline-sm text-headline-sm">AI Agent Insight</h4>
            </div>
            <p className="font-body-lg text-body-lg text-on-surface mb-6">
              {data?.agentInsight || "Loading insights..."}
            </p>
            <div className="space-y-3">
              <button className="w-full py-2 px-4 bg-secondary text-on-secondary rounded-lg font-label-md flex justify-between items-center group transition-all">
                Review Suggested Tasks
                <span className="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
              </button>
              <button className="w-full py-2 px-4 border border-outline-variant text-on-surface-variant rounded-lg font-label-md hover:bg-surface-container-low">
                Dismiss Suggestion
              </button>
            </div>
          </div>

          <div className="bg-surface border border-outline-variant rounded-xl p-container-padding">
            <h4 className="font-label-md text-on-surface-variant uppercase tracking-wider mb-4">Agent System Health</h4>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${data?.agentHealth?.researcher === 'Active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-amber-500 animate-pulse'}`}></div>
                  <span className="font-body-md">Researcher Agent</span>
                </div>
                <span className="font-mono-sm text-on-surface-variant">{data?.agentHealth?.researcher || '...'}</span>
              </div>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${data?.agentHealth?.planner === 'Active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-amber-500 animate-pulse'}`}></div>
                  <span className="font-body-md">Planner Agent</span>
                </div>
                <span className="font-mono-sm text-on-surface-variant">{data?.agentHealth?.planner || '...'}</span>
              </div>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${data?.agentHealth?.evaluator === 'Active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]' : 'bg-amber-500 animate-pulse'}`}></div>
                  <span className="font-body-md">Evaluator Agent</span>
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
