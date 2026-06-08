import { useState, useEffect } from 'react';
import { getProject, updateProject } from '../lib/api';

export default function SlackConfigPanel({ projectId }) {
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
    if (!projectId) return alert("Vui lòng chọn Dự án trước");
    setSaving(true);
    try {
      await updateProject(projectId, { slack_config: config });
      alert("Đã lưu cấu hình Slack");
    } catch (err) {
      alert("Lỗi khi lưu cấu hình: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Đang tải...</div>;
  if (!projectId) return <div>Vui lòng chọn hoặc tạo dự án để cấu hình</div>;

  return (
    <div className="bg-surface p-6 rounded-xl border border-outline-variant shadow-sm max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-6 text-primary flex items-center gap-2">
        <span className="material-symbols-outlined">hub</span> Cấu hình Slack
      </h2>
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Webhook URL</label>
          <input type="password" name="webhook_url" value={config.webhook_url} onChange={handleChange} placeholder="https://hooks.slack.com/..." className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Mention User ID (Tùy chọn)</label>
          <input type="text" name="mention_user_id" value={config.mention_user_id} onChange={handleChange} placeholder="e.g. U123456" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Dev Channel ID (Tùy chọn)</label>
          <input type="text" name="dev_channel_id" value={config.dev_channel_id} onChange={handleChange} placeholder="e.g. C11111" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">QA Channel ID (Tùy chọn)</label>
          <input type="text" name="qa_channel_id" value={config.qa_channel_id} onChange={handleChange} placeholder="e.g. C22222" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        
        <button type="submit" disabled={saving} className="mt-4 px-4 py-2 bg-primary text-on-primary rounded-lg font-medium disabled:opacity-50 flex items-center gap-2">
          {saving && <span className="material-symbols-outlined animate-spin text-sm">refresh</span>}
          Lưu cấu hình
        </button>
      </form>
    </div>
  );
}
