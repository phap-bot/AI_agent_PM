import React, { useState, useEffect } from 'react';
import { getProject, updateProject } from '../lib/api';
import { useTranslation } from 'react-i18next';
import {
  ConfigField,
  ConfigLink,
  ConfigNotice,
  ConfigPanelShell,
  ConfigSaveBar,
  ConfigSection,
  configInputClass,
} from './ConfigPanelLayout';

const GITHUB_TOKEN_URL = 'https://github.com/settings/tokens/new';

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
      alert(t('config.github.save_error') + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <ConfigNotice icon="progress_activity" title={t('common.loading')} description={t('config.common.loading_hint')} />;
  }

  if (!projectId) {
    return <ConfigNotice icon="folder_open" title={t('config.common.no_project_title')} description={t('config.please_select_project')} />;
  }

  return (
    <form onSubmit={handleSave}>
      <ConfigPanelShell
        icon="code"
        title={t('config.github.title')}
        subtitle={t('config.github.subtitle')}
        badge={t('config.common.branch_ready')}
        footer={(
          <ConfigSaveBar
            saving={saving}
            label={t('config.common.save_changes')}
            savingLabel={t('config.common.saving')}
          />
        )}
      >
        <ConfigSection title={t('config.github.repository_section')} description={t('config.github.repository_desc')}>
          <ConfigField label={t('config.github.repo')} hint={t('config.github.repo_hint')}>
            <input type="text" name="repository" value={config.repository} onChange={handleChange} placeholder={t('config.github.placeholder_repo')} className={configInputClass} />
          </ConfigField>

          <ConfigField label={t('config.github.base_branch')} hint={t('config.github.base_branch_desc')}>
            <input type="text" name="base_branch" value={config.base_branch} onChange={handleChange} placeholder={t('config.github.placeholder_base_branch')} className={configInputClass} />
          </ConfigField>
        </ConfigSection>

        <ConfigSection title={t('config.github.token_section')} description={t('config.github.token_desc')}>
          <ConfigField
            label={t('config.github.token')}
            hint={t('config.github.token_hint')}
            action={<ConfigLink href={GITHUB_TOKEN_URL}>{t('config.github.get_token')}</ConfigLink>}
          >
            <input type="password" name="api_token" value={config.api_token} onChange={handleChange} placeholder={t('config.github.placeholder_api_token')} className={configInputClass} />
          </ConfigField>
        </ConfigSection>
      </ConfigPanelShell>
    </form>
  );
}
