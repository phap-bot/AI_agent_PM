import React, { useState, useEffect } from 'react';
import { fetchTeamMembers } from '../lib/api';
import { useTranslation } from 'react-i18next';

export default function TeamPanel({ projectId }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let intervalId;
    async function loadData(showLoading = false) {
      if (showLoading) setLoading(true);
      try {
        const response = await fetchTeamMembers(projectId);
        setData(response);
      } catch (err) {
        console.error("Failed to load team data:", err);
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

  return (
    <div className="p-margin-page space-y-stack-lg w-full">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="font-display-lg text-display-lg text-on-surface">{t('team.title')}</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant">{t('team.subtitle')}</p>
        </div>
        <div className="flex gap-stack-md">
          <button className="px-stack-lg py-stack-sm rounded-lg border border-outline text-on-surface font-label-md text-label-md flex items-center gap-stack-sm hover:bg-surface-variant transition-all">
            <span className="material-symbols-outlined">smart_toy</span> {t('team.agent_roles')}
          </button>
          <button className="px-stack-lg py-stack-sm rounded-lg bg-primary text-on-primary font-label-md text-label-md flex items-center gap-stack-sm hover:opacity-90 transition-all active:scale-95">
            <span className="material-symbols-outlined">person_add</span> {t('team.invite_member')}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-gutter">
        <div className="col-span-12 lg:col-span-4 space-y-gutter">
          <div className="bg-surface-container-low p-container-padding rounded-xl shadow-sm" style={{borderLeft: "4px solid #4b41e1"}}>
            <div className="flex items-center gap-stack-sm mb-stack-md">
              <span className="material-symbols-outlined text-secondary">auto_awesome</span>
              <h3 className="font-headline-sm text-headline-sm">{t('team.agent_velocity')}</h3>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant mb-stack-lg">
              {data?.agentVelocityAudit || t('common.loading')}
            </p>
            <div className="space-y-stack-sm">
              <div className="flex justify-between items-center text-label-md font-label-md">
                <span className="text-on-surface-variant">{t('team.agent_efficiency')}</span>
                <span className="text-primary">{data?.agentEfficiency || 0}%</span>
              </div>
              <div className="w-full bg-surface-variant h-2 rounded-full overflow-hidden">
                <div className="bg-primary h-full" style={{ width: `${data?.agentEfficiency || 0}%` }}></div>
              </div>
            </div>
          </div>
          
          <div className="bg-white border border-outline-variant rounded-xl p-container-padding">
            <h3 className="font-label-md text-label-md uppercase tracking-wider text-outline mb-stack-md">{t('team.active_nodes')}</h3>
            <div className="space-y-stack-md">
              {data?.activeAgentNodes?.map((node, i) => (
                <div key={i} className="flex items-center gap-stack-sm p-stack-sm hover:bg-surface-container rounded-lg transition-colors cursor-pointer">
                  <div className={`w-10 h-10 rounded flex items-center justify-center ${node.name.includes('Refactor') ? 'bg-tertiary-fixed text-tertiary' : 'bg-primary-fixed text-primary'}`}>
                    <span className="material-symbols-outlined">{node.name.includes('Refactor') ? 'terminal' : 'description'}</span>
                  </div>
                  <div className="flex-1">
                    <div className="font-label-md text-label-md">{node.name}</div>
                    <div className="text-on-surface-variant text-[10px]">{node.task}</div>
                  </div>
                  <span className={`w-2 h-2 rounded-full bg-green-500 ${node.status === 'processing' ? 'animate-pulse' : ''}`}></span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-8 bg-white border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-container-padding py-stack-md border-b border-outline-variant flex items-center justify-between">
            <div className="flex items-center gap-stack-lg">
              <button className="font-label-md text-label-md text-primary border-b-2 border-primary pb-1">{t('team.all_members')} ({data?.members?.length || 0})</button>
              <button className="font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors">{t('team.humans')}</button>
              <button className="font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors">{t('team.agents')}</button>
            </div>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
              <input className="pl-8 pr-stack-md py-1.5 border border-outline-variant rounded-full text-body-md focus:ring-2 focus:ring-primary focus:border-primary bg-surface-container-low w-64 outline-none" placeholder={t('team.search_team')} type="text" />
            </div>
          </div>
          <table className="w-full text-left border-collapse">
            <thead className="bg-surface-container-low font-label-md text-label-md text-on-surface-variant border-b border-outline-variant">
              <tr>
                <th className="px-container-padding py-3 font-semibold">{t('team.member')}</th>
                <th className="px-gutter py-3 font-semibold">{t('team.role')}</th>
                <th className="px-gutter py-3 font-semibold">{t('team.workload')}</th>
                <th className="px-gutter py-3 font-semibold">{t('team.permissions')}</th>
                <th className="px-container-padding py-3 font-semibold text-right">{t('team.actions')}</th>
              </tr>
            </thead>
            <tbody className="font-body-md text-body-md divide-y divide-outline-variant">
              {data?.members?.map((member, idx) => (
                <tr key={idx} className="hover:bg-surface-bright transition-colors group">
                  <td className="px-container-padding py-stack-md">
                    <div className="flex items-center gap-stack-md">
                      {member.type === 'human' ? (
                        <div className="relative">
                          <img alt="Team Member" className="w-10 h-10 rounded-full object-cover" src={member.avatar} />
                          <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></span>
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container">
                          <span className="material-symbols-outlined">smart_toy</span>
                        </div>
                      )}
                      <div>
                        <div className="font-semibold text-on-surface">{member.name}</div>
                        <div className={`text-xs ${member.type === 'agent' ? 'text-secondary font-mono-sm' : 'text-on-surface-variant'}`}>{member.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-gutter py-stack-md">
                    <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-tighter ${member.type === 'human' ? 'bg-secondary-container/10 text-secondary' : 'bg-tertiary-container/10 text-tertiary'}`}>{member.role}</span>
                  </td>
                  <td className="px-gutter py-stack-md">
                    <div className="flex flex-col gap-1">
                      <div className="flex justify-between text-[10px]">
                        <span>{member.type === 'human' ? `${member.workload.current}/${member.workload.total} ${t('team.tickets')}` : `${member.workload.current} ${t('team.tasks_monitor')}`}</span>
                        <span className={`font-bold ${member.workload.status === 'High' || member.workload.status === 'Cao' ? 'text-error' : 'text-green-600'}`}>{member.workload.status === 'High' ? t('team.high') : member.workload.status}</span>
                      </div>
                      <div className="w-24 h-1.5 bg-surface-variant rounded-full">
                        <div className={`${member.workload.status === 'High' ? 'bg-error' : 'bg-green-500'} h-full rounded-full`} style={{ width: `${member.workload.percentage}%` }}></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-gutter py-stack-md">
                    <span className="text-on-surface-variant text-xs">{member.permissions}</span>
                  </td>
                  <td className="px-container-padding py-stack-md text-right">
                    <button className="p-1 hover:bg-surface-variant rounded transition-colors text-on-surface-variant">
                      <span className="material-symbols-outlined">{member.type === 'human' ? 'more_vert' : 'settings_input_component'}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="p-container-padding border-t border-outline-variant flex items-center justify-between text-label-md font-label-md text-on-surface-variant">
            <span>{t('team.showing')} {data?.members?.length || 0} {t('team.of')} {data?.members?.length || 0} {t('team.members_count')}</span>
            <div className="flex gap-stack-sm">
              <button className="px-3 py-1 rounded border border-outline-variant hover:bg-surface-variant transition-colors">{t('team.previous')}</button>
              <button className="px-3 py-1 rounded border border-outline-variant hover:bg-surface-variant transition-colors">{t('team.next')}</button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter mt-stack-md">
        <div className="bg-white border border-outline-variant p-stack-md rounded-xl flex items-center gap-stack-md">
          <div className="w-12 h-12 rounded-lg bg-surface-container flex items-center justify-center text-primary">
            <span className="material-symbols-outlined text-2xl">groups</span>
          </div>
          <div>
            <div className="text-on-surface-variant font-label-md text-label-md">{t('team.total_seats')}</div>
            <div className="text-headline-sm font-headline-sm">{data?.teamSeats?.used || 0} / {data?.teamSeats?.total || 0}</div>
          </div>
        </div>
        <div className="bg-white border border-outline-variant p-stack-md rounded-xl flex items-center gap-stack-md">
          <div className="w-12 h-12 rounded-lg bg-surface-container flex items-center justify-center text-secondary">
            <span className="material-symbols-outlined text-2xl">precision_manufacturing</span>
          </div>
          <div>
            <div className="text-on-surface-variant font-label-md text-label-md">{t('team.ai_tokens')}</div>
            <div className="text-headline-sm font-headline-sm">{data?.aiAgentTokens || 0} {t('team.active')}</div>
          </div>
        </div>
        <div className="bg-white border border-outline-variant p-stack-md rounded-xl flex items-center gap-stack-md">
          <div className="w-12 h-12 rounded-lg bg-surface-container flex items-center justify-center text-tertiary">
            <span className="material-symbols-outlined text-2xl">pending_actions</span>
          </div>
          <div>
            <div className="text-on-surface-variant font-label-md text-label-md">{t('team.pending_invites')}</div>
            <div className="text-headline-sm font-headline-sm">{data?.pendingInvites || 0} {t('team.sent')}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
