import React, { useEffect, useState } from 'react';
import { fetchAnalyticsOverview } from '../lib/api';
import { useTranslation } from 'react-i18next';

export default function AnalyticsPanel({ projectId }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [animate, setAnimate] = useState(false);
  const notAvailable = t('common.not_available');

  useEffect(() => {
    let intervalId;
    async function loadData(showLoading = false) {
      if (showLoading) {
        setLoading(true);
        setAnimate(false);
      }
      try {
        const response = await fetchAnalyticsOverview(projectId);
        setData(response);
      } catch (err) {
        console.error("Failed to load analytics data:", err);
      } finally {
        if (showLoading) {
          setLoading(false);
          // Trigger animations after a short delay
          setTimeout(() => setAnimate(true), 100);
        }
      }
    }
    
    // Initial load with loading spinner
    loadData(true);
    
    // Auto-refresh every 5 seconds without triggering loading animations again
    intervalId = setInterval(() => loadData(false), 5000);

    return () => clearInterval(intervalId);
  }, [projectId]);

  return (
    <div className="p-margin-page max-w-[1600px] w-full mx-auto space-y-stack-lg">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="font-display-lg text-display-lg">{t('analytics.title')}</h2>
          <p className="text-on-surface-variant mt-1">{t('analytics.subtitle')}</p>
        </div>
        <div className="flex gap-stack-sm">
          <button className="flex items-center gap-unit px-4 py-2 bg-white border border-outline-variant rounded-lg hover:bg-surface-container transition-all">
            <span className="material-symbols-outlined text-[18px]">calendar_today</span>
            <span className="font-label-md">{t('analytics.last_30_days')}</span>
          </button>
          <button className="flex items-center gap-unit px-4 py-2 bg-primary text-on-primary rounded-lg hover:brightness-110 transition-all">
            <span className="material-symbols-outlined text-[18px]">download</span>
            <span className="font-label-md">{t('analytics.export_report')}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-gutter">
        <div className="col-span-12 lg:col-span-8 bg-white rounded-xl border border-outline-variant p-container-padding shadow-sm" style={{borderLeft: "4px solid #4b41e1"}}>
          <div className="flex justify-between items-start mb-stack-lg">
            <div>
              <span className="px-2 py-0.5 bg-secondary-container text-on-secondary-container text-[10px] rounded uppercase font-bold tracking-wider">{t('analytics.ai_insight')}</span>
              <h3 className="font-headline-sm text-headline-sm mt-2">{t('analytics.accuracy_trend')}</h3>
            </div>
            <div className="text-right">
              <span className="text-display-lg font-bold text-primary">{data?.accuracy || 0}%</span>
              <p className="text-label-md text-on-surface-variant">{data?.accuracyTrend || notAvailable}</p>
              {data?.jiraConnected && (
                <span className="mt-1 inline-flex px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px] font-bold border border-green-200 gap-1 items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                  {t('analytics.jira_live')}
                </span>
              )}
            </div>
          </div>
          <div className="h-64 relative bg-surface-container-lowest rounded-lg border border-dashed border-outline-variant flex items-center justify-center overflow-hidden">
            <div className="absolute inset-0 opacity-10 pointer-events-none">
              <svg className="w-full h-full" viewBox="0 0 800 200">
                <path d="M0,150 Q100,100 200,130 T400,80 T600,110 T800,40" fill="none" stroke="currentColor" strokeWidth="4"></path>
              </svg>
            </div>
            <div className={`z-10 text-center transition-all duration-1000 transform ${animate ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}`}>
              <p className="font-mono-sm text-outline">{t('analytics.insight_label')}</p>
              <p className="text-body-md mt-2 text-on-surface-variant italic max-w-lg mx-auto">
                "{data?.aiInsightText || t('analytics.loading_insights')}"
              </p>
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 bg-white rounded-xl border border-outline-variant p-container-padding shadow-sm flex flex-col">
          <h3 className="font-label-md text-label-md text-outline uppercase tracking-widest mb-stack-md">{t('analytics.team_velocity')}</h3>
          <div className="flex-1 flex flex-col justify-between">
            <div className="space-y-stack-md">
              {data?.teamVelocityDetails?.length > 0 ? data.teamVelocityDetails.map((tv, i) => (
                <div key={i} className="flex justify-between items-end border-b border-outline-variant pb-2">
                  <span className="font-body-md">{tv.name}</span>
                  <div className="text-right">
                    <span className="font-headline-sm text-primary">{tv.pts} <span className="text-label-md text-on-surface-variant font-normal">{t('dashboard.pts')}</span></span>
                    {tv.total_pts > 0 && (
                      <p className="text-[10px] text-on-surface-variant">{tv.done_pts?.toFixed(0) || 0}/{tv.total_pts?.toFixed(0) || 0} {t('dashboard.sp')}</p>
                    )}
                  </div>
                </div>
              )) : (
                <div className="text-on-surface-variant text-sm py-4">{t('analytics.no_data')}</div>
              )}
            </div>
            <div className="mt-stack-lg pt-stack-md border-t border-outline-variant">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-primary"></div>
                <span className="text-label-md">{t('analytics.average_velocity').replace('{{velocity}}', data?.averageVelocity || 0)}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-12 md:col-span-6 bg-white rounded-xl border border-outline-variant p-container-padding shadow-sm">
          <div className="flex justify-between mb-stack-md">
            <h3 className="font-headline-sm text-headline-sm">{t('analytics.ticket_lead_time')}</h3>
            <span className="material-symbols-outlined text-outline">info</span>
          </div>
          <div className="grid grid-cols-4 items-end gap-2 h-40">
            <div 
              className="bg-primary/20 rounded-t flex flex-col justify-end items-center pb-2 transition-all duration-1000 ease-out" 
              style={{ height: animate ? `${Math.max(10, data?.leadTimeData?.['1d']?.percentage || 0)}%` : '0%' }}>
              <span className="text-[10px] font-bold">{data?.leadTimeData?.['1d']?.count || 0}</span>
            </div>
            <div 
              className="bg-primary/40 rounded-t flex flex-col justify-end items-center pb-2 transition-all duration-1000 ease-out delay-100" 
              style={{ height: animate ? `${Math.max(10, data?.leadTimeData?.['2d']?.percentage || 0)}%` : '0%' }}>
              <span className="text-[10px] font-bold">{data?.leadTimeData?.['2d']?.count || 0}</span>
            </div>
            <div 
              className="bg-primary rounded-t flex flex-col justify-end items-center pb-2 text-white transition-all duration-1000 ease-out delay-200" 
              style={{ height: animate ? `${Math.max(10, data?.leadTimeData?.['3d']?.percentage || 0)}%` : '0%' }}>
              <span className="text-[10px] font-bold">{data?.leadTimeData?.['3d']?.count || 0}</span>
            </div>
            <div 
              className="bg-primary/30 rounded-t flex flex-col justify-end items-center pb-2 transition-all duration-1000 ease-out delay-300" 
              style={{ height: animate ? `${Math.max(10, data?.leadTimeData?.['5d']?.percentage || 0)}%` : '0%' }}>
              <span className="text-[10px] font-bold">{data?.leadTimeData?.['5d']?.count || 0}</span>
            </div>
          </div>
          <div className="mt-4 flex justify-between text-label-md text-on-surface-variant">
            <span>&lt;1d</span>
            <span>2d</span>
            <span>3d-4d</span>
            <span>5d+</span>
          </div>
        </div>

        <div className="col-span-12 md:col-span-6 bg-white rounded-xl border border-outline-variant p-container-padding shadow-sm">
          <div className="flex justify-between mb-stack-md">
            <h3 className="font-headline-sm text-headline-sm">{t('analytics.active_burndown')}</h3>
            <div className="flex gap-2">
              <span className="flex items-center gap-1 text-label-md">
                <span className="w-3 h-0.5 bg-outline-variant"></span> {t('analytics.ideal')}
              </span>
              <span className="flex items-center gap-1 text-label-md">
                <span className="w-3 h-0.5 bg-primary"></span> {t('analytics.actual')}
              </span>
            </div>
          </div>
          <div className="h-40 w-full bg-surface-container relative rounded overflow-hidden">
            <svg className="w-full h-full" preserveAspectRatio="none">
              <line stroke="#c3c6d7" strokeDasharray="4" strokeWidth="1" x1="0" x2="100%" y1="0" y2="100%"></line>
              <path 
                d={data?.activeBurndownPath || "M0,100 L100,100"} 
                fill="none" 
                stroke="#004ac6" 
                strokeWidth="3"
                style={{
                  strokeDasharray: 1000,
                  strokeDashoffset: animate ? 0 : 1000,
                  transition: "stroke-dashoffset 2s ease-in-out"
                }}
              ></path>
            </svg>
          </div>
          <div className="mt-4 flex justify-between text-label-md text-on-surface-variant font-mono-sm">
            <span>{t('analytics.start')}</span>
            <span>{t('analytics.mid')}</span>
            <span>{t('analytics.end')}</span>
          </div>
        </div>

        <div className="col-span-12 bg-white rounded-xl border border-outline-variant shadow-sm overflow-hidden">
          <div className="px-container-padding py-stack-md border-b border-outline-variant flex justify-between items-center bg-surface-container-low">
            <h3 className="font-headline-sm text-headline-sm">{t('analytics.resource_efficiency')}</h3>
            <div className="flex gap-stack-sm">
              <span className={`px-3 py-1 text-[11px] rounded-full font-bold ${data?.jiraConnected ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}>
                {data?.jiraConnected ? t('analytics.live_data') : t('analytics.offline')}
              </span>
            </div>
          </div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface text-outline font-label-md border-b border-outline-variant">
                <th className="p-4 font-semibold">{t('analytics.col_project_name')}</th>
                <th className="p-4 font-semibold">{t('analytics.col_cycle_time')}</th>
                <th className="p-4 font-semibold">{t('analytics.col_blocker_ratio')}</th>
                <th className="p-4 font-semibold">{t('analytics.col_status')}</th>
                <th className="p-4 font-semibold">{t('analytics.col_ai_automation')}</th>
                <th className="p-4 font-semibold">{t('analytics.col_trend')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant text-body-md">
              {data?.resourceEfficiency?.length > 0 ? data.resourceEfficiency.map((item, idx) => (
                <tr key={idx} className="hover:bg-surface-container-low transition-colors">
                  <td className="p-4 font-semibold">{item.name}</td>
                  <td className="p-4">{item.cycleTime}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-surface-variant rounded-full overflow-hidden">
                        <div className={`h-full transition-all duration-1000 ease-out ${item.blockerRatio > 30 ? 'bg-error' : item.blockerRatio > 15 ? 'bg-amber-500' : 'bg-tertiary'}`} style={{ width: animate ? `${item.blockerRatio}%` : '0%' }}></div>
                      </div>
                      <span className={`text-label-md ${item.blockerRatio > 30 ? 'text-error' : ''}`}>{item.blockerRatio}%</span>
                    </div>
                  </td>
                  <td className="p-4">
                    {(item.done > 0 || item.in_progress > 0 || item.todo > 0) ? (
                      <div className="flex gap-1 items-center text-[11px]">
                        <span className="px-1.5 py-0.5 rounded bg-green-100 text-green-700 font-bold">{item.done} {t('dashboard.done')}</span>
                        <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-bold">{item.in_progress} {t('dashboard.wip')}</span>
                        <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 font-bold">{item.todo} {t('dashboard.todo')}</span>
                      </div>
                    ) : (
                      <span className="text-on-surface-variant text-sm">{notAvailable}</span>
                    )}
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-[11px] font-bold ${item.aiAutomation.includes('100%') ? 'bg-primary-fixed text-on-primary-fixed-variant' : 'bg-surface-variant text-on-surface-variant'}`}>{item.aiAutomation}</span>
                  </td>
                  <td className={`p-4 ${item.trend === 'up' ? 'text-green-600' : 'text-error'}`}>
                    <span className="material-symbols-outlined">
                      {item.trend === 'up' ? 'trending_up' : 'trending_down'}
                    </span>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan="6" className="p-4 text-center text-on-surface-variant">{t('analytics.no_resource_data')}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
