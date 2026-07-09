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

const ATLASSIAN_TOKEN_URL = 'https://id.atlassian.com/manage-profile/security/api-tokens';

export default function JiraConfigPanel({ projectId }) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    base_url: '',
    project_key: '',
    email: '',
    api_token: '',
    issue_type: '',
    subtask_issue_type: '',
    board_id: ''
  });

  useEffect(() => {
    if (projectId) {
      setLoading(true);
      getProject(projectId)
        .then(res => {
          if (res.jira_config) {
            setConfig({
              base_url: res.jira_config.base_url || '',
              project_key: res.jira_config.project_key || '',
              email: res.jira_config.email || '',
              api_token: res.jira_config.api_token || '',
              issue_type: res.jira_config.issue_type === 'Task' ? '' : (res.jira_config.issue_type || ''),
              subtask_issue_type: res.jira_config.subtask_issue_type === 'Sub-task' ? '' : (res.jira_config.subtask_issue_type || ''),
              board_id: res.jira_config.board_id || ''
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
      await updateProject(projectId, { jira_config: config });
      alert(t('config.jira.saved'));
    } catch (err) {
      alert(t('config.jira.save_error') + err.message);
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
        icon="settings_suggest"
        title={t('config.jira.title')}
        subtitle={t('config.jira.subtitle')}
        badge={t('config.common.project_scoped')}
        footer={(
          <ConfigSaveBar
            saving={saving}
            label={t('config.common.save_changes')}
            savingLabel={t('config.common.saving')}
          />
        )}
      >
        <ConfigSection title={t('config.jira.connection_section')} description={t('config.jira.connection_desc')}>
          <ConfigField label={t('config.jira.base_url')}>
            <input type="text" name="base_url" value={config.base_url} onChange={handleChange} placeholder={t('config.jira.placeholder_base_url')} className={configInputClass} />
          </ConfigField>

          <div className="grid gap-4 lg:grid-cols-2">
            <ConfigField label={t('config.jira.project_key')}>
              <input type="text" name="project_key" value={config.project_key} onChange={handleChange} placeholder={t('config.jira.placeholder_project_key')} className={configInputClass} />
            </ConfigField>
            <ConfigField label={t('config.jira.email')}>
              <input type="email" name="email" value={config.email} onChange={handleChange} placeholder={t('config.jira.placeholder_email')} className={configInputClass} />
            </ConfigField>
          </div>

          <ConfigField
            label={t('config.jira.api_token')}
            hint={t('config.jira.api_token_hint')}
            action={<ConfigLink href={ATLASSIAN_TOKEN_URL}>{t('config.jira.get_token')}</ConfigLink>}
          >
            <input type="password" name="api_token" value={config.api_token} onChange={handleChange} placeholder={t('config.jira.placeholder_api_token')} className={configInputClass} />
          </ConfigField>
        </ConfigSection>

        <ConfigSection title={t('config.jira.work_item_section')} description={t('config.jira.work_item_desc')}>
          <div className="grid gap-4 lg:grid-cols-2">
            <ConfigField label={t('config.jira.issue_type')} hint={t('config.jira.issue_type_hint')}>
              <input type="text" name="issue_type" value={config.issue_type} onChange={handleChange} placeholder={t('config.jira.default_task')} className={configInputClass} />
            </ConfigField>
            <ConfigField label={t('config.jira.subtask_type')} hint={t('config.jira.subtask_type_hint')}>
              <input type="text" name="subtask_issue_type" value={config.subtask_issue_type} onChange={handleChange} placeholder={t('config.jira.default_subtask')} className={configInputClass} />
            </ConfigField>
          </div>

          <ConfigField label={t('config.jira.board_id')} hint={t('config.jira.board_id_hint')}>
            <input type="text" name="board_id" value={config.board_id} onChange={handleChange} placeholder={t('config.jira.placeholder_board_id')} className={configInputClass} />
          </ConfigField>
        </ConfigSection>
      </ConfigPanelShell>
    </form>
  );
}
