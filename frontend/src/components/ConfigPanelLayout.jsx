import React from 'react';

export const configInputClass = "h-12 w-full rounded-2xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-950 shadow-inner shadow-slate-950/[0.03] outline-none transition-all placeholder:text-slate-600 focus:border-blue-300 focus:bg-white focus:ring-4 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-60";

export function ConfigNotice({ icon = 'info', title, description }) {
  return (
    <section className="mx-auto max-w-3xl rounded-[28px] border border-slate-200 bg-white/88 p-6 text-center shadow-sm shadow-slate-950/5">
      <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-slate-100 text-slate-600">
        <span className="material-symbols-outlined text-[24px]">{icon}</span>
      </div>
      <h2 className="mt-4 text-lg font-black text-slate-950">{title}</h2>
      {description && <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">{description}</p>}
    </section>
  );
}

export function ConfigPanelShell({ icon, title, badge, children, footer }) {
  return (
    <section className="mx-auto max-w-4xl">
      <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-white/90 shadow-[0_18px_50px_rgba(15,23,42,0.07)] backdrop-blur-xl">
        <div className="border-b border-slate-200 bg-gradient-to-br from-white via-slate-50 to-blue-50/50 px-5 py-5 sm:px-7">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex min-w-0 items-start gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-slate-900 text-white shadow-sm shadow-slate-950/15">
                <span className="material-symbols-outlined text-[25px]">{icon}</span>
              </div>
              <div className="min-w-0">
                <h2 className="text-2xl font-black tracking-[-0.02em] text-slate-950">{title}</h2>
              </div>
            </div>
            {badge && (
              <span className="inline-flex min-h-9 shrink-0 items-center justify-center rounded-full border border-blue-200 bg-white px-3 text-xs font-black text-blue-800 shadow-sm">
                {badge}
              </span>
            )}
          </div>
        </div>

        <div className="space-y-5 p-4 sm:p-6">
          {children}
        </div>

        {footer && (
          <div className="border-t border-slate-200 bg-slate-50/70 px-4 py-4 sm:px-6">
            {footer}
          </div>
        )}
      </div>
    </section>
  );
}

export function ConfigSection({ title, children }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-950/[0.03] sm:p-5">
      <div className="mb-4">
        <h3 className="text-sm font-black uppercase tracking-[0.16em] text-slate-700">{title}</h3>
      </div>
      <div className="grid gap-4">
        {children}
      </div>
    </div>
  );
}

export function ConfigField({ label, action, children }) {
  return (
    <label className="block">
      <div className="mb-1.5 flex min-h-6 items-center justify-between gap-3">
        <span className="text-sm font-extrabold text-slate-950">{label}</span>
        {action}
      </div>
      {children}
    </label>
  );
}

export function ConfigLink({ href, children }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-black text-blue-800 transition hover:bg-blue-100"
    >
      {children}
    </a>
  );
}

export function ConfigSaveBar({ saving, label, savingLabel }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <button
        type="submit"
        disabled={saving}
        className="inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-black text-white shadow-sm shadow-blue-600/20 transition-all hover:-translate-y-0.5 hover:bg-blue-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 sm:ml-auto"
      >
        {saving && <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />}
        {saving ? savingLabel : label}
      </button>
    </div>
  );
}
