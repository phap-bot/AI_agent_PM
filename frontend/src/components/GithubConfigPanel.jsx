import React, { useState, useEffect } from 'react';
import { getProject, updateProject } from '../lib/api';
import { useTranslation } from 'react-i18next';

export default function GithubConfigPanel({ projectId }) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    repository: '',
    base_branch: '',
    api_token: ''
  });

  useEffect(() => {
    if (projectId) {
      setLoading(true);
      getProject(projectId)
        .then(res => {
          if (res.github_config) {
            // If base_branch is 'main' from backend default, we can show it as empty to show placeholder
            const branch = res.github_config.base_branch === 'main' ? '' : (res.github_config.base_branch || '');
            setConfig({
              repository: res.github_config.repository || '',
              base_branch: branch,
              api_token: res.github_config.api_token || ''
            });
          }
        })
        .catch(err => console.error(err))
        .finally(() => setLoading(false));
    }
  }, [projectId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!projectId) return alert(t('config.please_select_project'));
    setSaving(true);
    try {
      await updateProject(projectId, { github_config: config });
      alert(t('config.github.saved'));
    } catch (err) {
      alert(t('config.jira.save_error') + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>{t('common.loading')}</div>;
  if (!projectId) return <div>{t('config.please_select_project')}</div>;

  return (
    <div className="bg-surface p-6 rounded-xl border border-outline-variant shadow-sm max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-6 text-primary flex items-center gap-2">
        <span className="material-symbols-outlined">code</span> {t('config.github.title')}
      </h2>
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">{t('config.github.repo')}</label>
          <input type="text" name="repository" value={config.repository} onChange={handleChange} placeholder="VD: phap-bot/AI_agent_PM hoặc https://github.com/..." className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">{t('config.github.base_branch')}</label>
          <input type="text" name="base_branch" value={config.base_branch} onChange={handleChange} placeholder="main" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
          <p className="text-xs text-on-surface-variant mt-1">{t('config.github.base_branch_desc')}</p>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 flex justify-between">
            <span>{t('config.github.token')}</span>
            <a href="https://github.com/settings/tokens/new" target="_blank" rel="noreferrer" className="text-primary hover:underline font-normal">{t('config.github.get_token')}</a>
          </label>
          <input type="password" name="api_token" value={config.api_token} onChange={handleChange} placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxx" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        
        <button type="submit" disabled={saving} className="mt-4 px-4 py-2 bg-primary text-on-primary rounded-lg font-medium disabled:opacity-50 flex items-center gap-2">
          {saving && <span className="material-symbols-outlined animate-spin text-sm">refresh</span>}
          {t('common.save')}
        </button>
      </form>
    </div>
  );
}
