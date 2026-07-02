import React, { useState, useEffect } from 'react';
import { fetchHistory, deleteHistory } from '../lib/api';
import { useTranslation } from 'react-i18next';

export default function HistoryPanel({ projectId, onSelectHistory }) {
  const { t } = useTranslation();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    if (projectId) {
      setLoading(true);
      fetchHistory(projectId)
        .then(res => setHistory(res || []))
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [projectId]);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (window.confirm(t('history.confirm_delete'))) {
      try {
        await deleteHistory(id);
        setHistory(prev => prev.filter(item => item.id !== id));
      } catch (err) {
        alert(t('history.delete_fail') + err.message);
      }
    }
  };

  const filteredHistory = history.filter(item => {
    if (filter === 'all') return true;
    if (filter === '7d') {
      const itemDate = new Date(item.created_at);
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      return itemDate >= sevenDaysAgo;
    }
    return true; // 'custom' fallback
  });

  const getBtnClass = (active) => active 
    ? "px-4 py-1.5 rounded-md font-label-md bg-secondary-container text-on-secondary-container" 
    : "px-4 py-1.5 rounded-md font-label-md text-on-surface-variant hover:bg-surface-variant";

  return (
    <div className="flex-1 p-margin-page bg-background h-full overflow-y-auto">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-stack-md mb-stack-lg">
          <div>
            <h2 className="font-display-lg text-display-lg text-on-surface">{t('history.title')}</h2>
            <p className="font-body-lg text-body-lg text-on-surface-variant">{t('history.subtitle')}</p>
          </div>
          <div className="flex items-center gap-stack-sm">
            <div className="flex bg-surface border border-outline-variant rounded-lg p-1">
              <button className={getBtnClass(filter === 'all')} onClick={() => setFilter('all')}>{t('history.all_time')}</button>
              <button className={getBtnClass(filter === '7d')} onClick={() => setFilter('7d')}>{t('history.last_7d')}</button>
              <button className={getBtnClass(filter === 'custom')} onClick={() => alert(t('history.feature_in_development'))}>{t('history.custom')}</button>
            </div>
          </div>
        </div>

        <div className="relative pl-12 space-y-stack-lg min-h-[500px]">
          <div className="absolute left-6 top-0 bottom-0 w-[2px] bg-outline-variant opacity-30 z-0"></div>

          {loading ? (
            <div className="py-8 text-center text-on-surface-variant">{t('history.loading')}</div>
          ) : filteredHistory.length === 0 ? (
            <div className="py-8 text-center text-on-surface-variant relative z-10">{t('history.no_history')}</div>
          ) : (
            filteredHistory.map((item, idx) => {
              const date = new Date(item.created_at);
              const isNewDay = idx === 0 || new Date(filteredHistory[idx-1].created_at).toDateString() !== date.toDateString();
              
              return (
                <div key={idx} className="relative z-10">
                  {isNewDay && (
                    <div className="relative -ml-12 flex items-center gap-4 mb-stack-md">
                      <div className="bg-surface-container text-on-surface-variant px-4 py-1 rounded-full font-label-md border border-outline-variant z-10">
                        {date.toLocaleDateString()}
                      </div>
                      <div className="h-[1px] flex-1 bg-outline-variant opacity-30"></div>
                    </div>
                  )}
                  
                  <div className="relative group mb-stack-lg">
                    <div className="absolute -left-12 top-0 w-12 flex justify-center z-10">
                      <div className="w-8 h-8 rounded-full bg-secondary text-on-secondary flex items-center justify-center border-4 border-background">
                        <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                      </div>
                    </div>
                    
                    <div 
                      className="history-card bg-surface border border-outline-variant rounded-xl p-container-padding cursor-pointer transition-transform hover:-translate-y-1 hover:shadow-md border-l-4 border-l-secondary"
                      onClick={() => onSelectHistory && onSelectHistory(item)}
                    >
                      <div className="flex justify-between items-start mb-stack-sm">
                        <div>
                          <span className="font-label-md text-label-md text-secondary uppercase tracking-wider">{t('history.ai_action')}</span>
                          <h3 className="font-headline-sm text-headline-sm mt-1">{item.jira_key ? t('history.generated_jira').replace('{{key}}', item.jira_key) : t('history.generated_backlog')}</h3>
                        </div>
                        <div className="text-right">
                          <p className="font-mono-sm text-mono-sm text-on-surface-variant">{date.toLocaleTimeString()}</p>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-green-100 text-green-700 font-label-md text-[10px] uppercase">{t('history.automated')}</span>
                        </div>
                      </div>
                      <p className="text-on-surface-variant mb-stack-md max-w-2xl line-clamp-2">
                        {item.story?.title || item.requirement}
                      </p>
                      <div className="flex items-center gap-stack-md">
                        <div className="flex -space-x-2">
                          <div className="w-6 h-6 rounded-full bg-primary-fixed border border-white flex items-center justify-center text-[10px] font-bold">SA</div>
                        </div>
                        <span className="font-label-md text-on-surface-variant">{t('history.type')} {item.story?.story_type || t('history.unknown')}</span>
                        <div className="ml-auto flex items-center gap-2">
                          <button 
                            className="text-error hover:bg-error-container p-1 rounded-full flex items-center justify-center transition-colors"
                            onClick={(e) => handleDelete(e, item.id)}
                            title={t('history.delete_tooltip')}
                          >
                            <span className="material-symbols-outlined text-sm">delete</span>
                          </button>
                          <button className="text-primary font-label-md flex items-center gap-1 hover:underline">
                            {t('history.view_details')} <span className="material-symbols-outlined text-sm">arrow_forward</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
