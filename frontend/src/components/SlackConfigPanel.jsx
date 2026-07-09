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

const SLACK_WEBHOOK_URL = 'https://api.slack.com/messaging/webhooks';

export default function SlackConfigPanel({ projectId }) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    webhook_url: '',
    mention_user_id: '',
    dev_channel_id: '',
    qa_channel_id: ''
  });

  useEffect(() => {
    if (projectId) {
      setLoading(true);
      getProject(projectId)
        .then(res => {
          if (res.slack_config) {
            setConfig({
              webhook_url: res.slack_config.webhook_url || '',
              mention_user_id: res.slack_config.mention_user_id || '',
              dev_channel_id: res.slack_config.dev_channel_id || '',
              qa_channel_id: res.slack_config.qa_channel_id || ''
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
      await updateProject(projectId, { slack_config: config });
      alert(t('config.slack.saved'));
    } catch (err) {
      alert(t('config.slack.save_error') + err.message);
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
        icon="hub"
        title={t('config.slack.title')}
        subtitle={t('config.slack.subtitle')}
        badge={t('config.common.notification_ready')}
        footer={(
          <ConfigSaveBar
            saving={saving}
            label={t('config.common.save_changes')}
            savingLabel={t('config.common.saving')}
          />
        )}
      >
        <ConfigSection title={t('config.slack.webhook_section')} description={t('config.slack.webhook_desc')}>
          <ConfigField
            label={t('config.slack.webhook_url')}
            hint={t('config.slack.webhook_hint')}
            action={<ConfigLink href={SLACK_WEBHOOK_URL}>{t('config.slack.create_webhook')}</ConfigLink>}
          >
            <input type="password" name="webhook_url" value={config.webhook_url} onChange={handleChange} placeholder={t('config.slack.placeholder_webhook_url')} className={configInputClass} />
          </ConfigField>
        </ConfigSection>

        <ConfigSection title={t('config.slack.routing_section')} description={t('config.slack.routing_desc')}>
          <ConfigField label={t('config.slack.mention_user_id')} hint={t('config.slack.mention_user_hint')}>
            <input type="text" name="mention_user_id" value={config.mention_user_id} onChange={handleChange} placeholder={t('config.slack.placeholder_mention_user_id')} className={configInputClass} />
          </ConfigField>

          <div className="grid gap-4 lg:grid-cols-2">
            <ConfigField label={t('config.slack.dev_channel_id')} hint={t('config.slack.dev_channel_hint')}>
              <input type="text" name="dev_channel_id" value={config.dev_channel_id} onChange={handleChange} placeholder={t('config.slack.placeholder_dev_channel_id')} className={configInputClass} />
            </ConfigField>
            <ConfigField label={t('config.slack.qa_channel_id')} hint={t('config.slack.qa_channel_hint')}>
              <input type="text" name="qa_channel_id" value={config.qa_channel_id} onChange={handleChange} placeholder={t('config.slack.placeholder_qa_channel_id')} className={configInputClass} />
            </ConfigField>
          </div>
        </ConfigSection>
      </ConfigPanelShell>
    </form>
  );
}
