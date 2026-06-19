import { useState, useEffect } from 'react';
import { getProject, updateProject } from '../lib/api';

export default function JiraConfigPanel({ projectId }) {
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
    if (!projectId) return alert("Vui lòng chọn Dự án trước");
    setSaving(true);
    try {
      await updateProject(projectId, { jira_config: config });
      alert("Đã lưu cấu hình Jira");
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
        <span className="material-symbols-outlined">settings_suggest</span> Cấu hình Jira
      </h2>
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Base URL</label>
          <input type="text" name="base_url" value={config.base_url} onChange={handleChange} placeholder="https://your-domain.atlassian.net" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Project Key</label>
          <input type="text" name="project_key" value={config.project_key} onChange={handleChange} placeholder="e.g. ALP" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input type="email" name="email" value={config.email} onChange={handleChange} placeholder="Email Atlassian" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1 flex justify-between">
            <span>API Token</span>
            <a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noreferrer" className="text-primary hover:underline font-normal">Lấy mã Token tại đây &rarr;</a>
          </label>
          <input type="password" name="api_token" value={config.api_token} onChange={handleChange} placeholder="Token" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Issue Type</label>
            <input type="text" name="issue_type" value={config.issue_type} onChange={handleChange} placeholder="Mặc định: Task" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Subtask Type</label>
            <input type="text" name="subtask_issue_type" value={config.subtask_issue_type} onChange={handleChange} placeholder="Mặc định: Sub-task" className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Board ID (Tùy chọn)</label>
          <input type="text" name="board_id" value={config.board_id} onChange={handleChange} className="w-full px-3 py-2 border border-outline-variant rounded-lg focus:outline-none focus:border-primary" />
        </div>
        <button type="submit" disabled={saving} className="mt-4 px-4 py-2 bg-primary text-on-primary rounded-lg font-medium disabled:opacity-50 flex items-center gap-2">
          {saving && <span className="material-symbols-outlined animate-spin text-sm">refresh</span>}
          Lưu cấu hình
        </button>
      </form>
    </div>
  );
}
