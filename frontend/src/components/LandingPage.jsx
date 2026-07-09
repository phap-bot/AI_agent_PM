const workflowSteps = [
  { name: 'Input', detail: 'Capture the raw stakeholder request.' },
  { name: 'Researcher', detail: 'Retrieve project context and assumptions.' },
  { name: 'Planner', detail: 'Draft stories, AC, points, and tasks.' },
  { name: 'Evaluator', detail: 'Validate guardrails before handoff.' },
  { name: 'Approval', detail: 'Keep a human in the release loop.' },
  { name: 'Jira/Slack', detail: 'Notify the team only after approval.' },
];

const features = [
  {
    title: 'Context-aware research',
    description: 'Ground every story in your uploaded project docs, prior decisions, and sprint constraints.',
  },
  {
    title: 'Planner with guardrails',
    description: 'Generate user stories, acceptance criteria, Fibonacci points, and BE/FE/QA tasks in one pass.',
  },
  {
    title: 'Evaluation before Jira',
    description: 'Block ambiguous, oversized, or incomplete output before it can become team noise.',
  },
  {
    title: 'Team handoff',
    description: 'Preview Jira, Slack, and GitHub actions so your delivery workflow stays intentional.',
  },
];

const planCards = [
  {
    name: 'Free',
    price: '$0',
    description: 'For teams getting started with AI-assisted planning.',
    items: ['Local AI with default models', 'Up to 3 active projects', 'Jira & Slack integration', 'Community support'],
  },
  {
    name: 'Team',
    price: '$29',
    description: 'For growing teams that need more power and control.',
    items: ['All Free features', 'Unlimited projects', 'Custom models & prompts', 'Advanced guardrails & evals'],
    highlighted: true,
  },
];

function ArrowIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true" className="h-5 w-5">
      <path
        d="M4.2 10h11.1m0 0-4.1-4.1m4.1 4.1-4.1 4.1"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function ProductPreview() {
  return (
    <div className="relative mx-auto w-full max-w-[710px] rounded-[28px] border border-slate-200 bg-white p-3 shadow-[0_34px_90px_rgba(79,70,229,0.22)]">
      <div className="absolute -right-8 -top-8 h-28 w-28 rounded-full bg-violet-300/40 blur-3xl" />
      <div className="absolute -bottom-10 -left-8 h-32 w-32 rounded-full bg-blue-300/40 blur-3xl" />
      <div className="relative overflow-hidden rounded-[22px] border border-slate-200 bg-white text-slate-950">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-blue-50 text-[10px] font-black text-blue-600">PM</span>
            <p className="text-sm font-extrabold">PM Agent</p>
          </div>
          <div className="flex items-center gap-3 text-slate-400">
            <span className="material-symbols-outlined text-base">notifications</span>
            <span className="grid h-7 w-7 place-items-center rounded-full bg-slate-950 text-[10px] font-bold text-white">TM</span>
          </div>
        </div>
        <div className="grid min-h-[430px] sm:grid-cols-[150px_1fr]">
          <aside className="hidden border-r border-slate-200 bg-slate-50/80 p-4 text-xs font-semibold text-slate-600 sm:block">
            {['New request', 'Inbox', 'Requests', 'Projects', 'Pipeline', 'Templates', 'Settings'].map((item) => (
              <div key={item} className={`mb-2 rounded-xl px-3 py-2 ${item === 'Pipeline' ? 'bg-blue-50 text-blue-700' : ''}`}>
                {item}
              </div>
            ))}
            <div className="mt-20 rounded-2xl border border-blue-100 bg-white p-3 text-[11px] text-slate-500">
              <p className="font-bold text-slate-800">Local AI</p>
              <p className="mt-1">Data stays local</p>
            </div>
          </aside>
          <div className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xl font-black tracking-normal">Pipeline</p>
                <p className="text-xs text-slate-500">From request to Jira-ready stories.</p>
              </div>
              <button className="text-xs font-bold text-blue-600">View details →</button>
            </div>
            <div className="mt-7 grid grid-cols-3 gap-3 md:grid-cols-6">
              {workflowSteps.map((step, index) => (
                <div key={step.name} className="text-center">
                  <div className={`mx-auto grid h-14 w-14 place-items-center rounded-2xl border text-xl ${index === 2 ? 'border-violet-200 bg-violet-50 text-violet-600' : 'border-blue-100 bg-blue-50 text-blue-600'}`}>
                    {['▣', '⌕', '▤', '◇', '✓', '↗'][index]}
                  </div>
                  <p className="mt-2 text-[11px] font-black">{step.name}</p>
                </div>
              ))}
            </div>
            <div className="mt-7 grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-bold text-violet-600">Current step · Planner</p>
                <div className="mt-4 space-y-2 text-xs text-slate-600">
                  {['Context loaded', 'Requirements analyzed', 'Options compared', 'Drafting stories & tasks'].map((item) => (
                    <p key={item} className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-emerald-400" />
                      {item}
                    </p>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-bold text-slate-500">Planner output preview</p>
                <p className="mt-3 text-sm font-black">Story</p>
                <p className="mt-1 text-xs leading-5 text-slate-600">
                  As a user, I want to reset my password so that I can regain access securely.
                </p>
                <p className="mt-3 text-sm font-black">Acceptance criteria</p>
                <ul className="mt-1 list-disc space-y-1 pl-4 text-xs leading-5 text-slate-600">
                  <li>Reset request is sent via email</li>
                  <li>Token expires in 15 minutes</li>
                  <li>Confirmation appears on success</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LandingPage({ onEnterApp }) {
  const reloadLandingPage = () => {
    localStorage.removeItem('skipLanding');
    window.location.reload();
  };

  const scrollToPricing = () => {
    document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="min-h-screen overflow-hidden bg-[#f8fbff] text-slate-950">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_15%_10%,rgba(99,102,241,0.16),transparent_28%),radial-gradient(circle_at_86%_8%,rgba(14,165,233,0.16),transparent_25%),linear-gradient(rgba(15,23,42,0.045)_1px,transparent_1px),linear-gradient(90deg,rgba(15,23,42,0.045)_1px,transparent_1px)] bg-[size:auto,auto,72px_72px,72px_72px]" />

      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <button
          type="button"
          onClick={reloadLandingPage}
          className="flex items-center gap-3 rounded-2xl text-left transition hover:bg-white/60 focus:outline-none focus:ring-2 focus:ring-blue-200 focus:ring-offset-2 focus:ring-offset-transparent"
          aria-label="Reload PM Agent landing page"
        >
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-slate-950 text-white shadow-lg shadow-slate-900/15">
            <span className="text-sm font-black">PM</span>
          </span>
          <span className="text-lg font-extrabold tracking-normal">PM Agent</span>
        </button>
        <nav className="hidden items-center gap-8 text-sm font-semibold text-slate-600 md:flex">
          <a href="#product" className="hover:text-slate-950">Product</a>
          <a href="#workflow" className="hover:text-slate-950">Workflow</a>
          <a href="#pricing" className="hover:text-slate-950">Pricing</a>
          <a href="#docs" className="hover:text-slate-950">Docs</a>
        </nav>
        <div className="flex items-center gap-3">
          <button
            onClick={scrollToPricing}
            className="hidden rounded-xl border border-blue-200 bg-white/70 px-5 py-3 text-sm font-bold text-blue-700 shadow-sm transition hover:-translate-y-0.5 sm:inline-flex"
          >
            View demo
          </button>
          <button
            onClick={onEnterApp}
            className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-blue-700/20 transition hover:-translate-y-0.5 hover:bg-blue-700"
          >
            Start free
          </button>
        </div>
      </header>

      <main className="relative z-10">
        <section id="product" className="mx-auto grid max-w-7xl items-center gap-14 px-6 pb-24 pt-14 lg:grid-cols-[0.95fr_1.05fr] lg:px-8 lg:pb-32 lg:pt-20">
          <div>
            <h1 className="max-w-4xl text-5xl font-black tracking-normal text-slate-950 sm:text-6xl">
              Turn raw requests into sprint-ready work
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-600">
              Research, plan, evaluate, and ship Jira-ready stories with local AI guardrails.
            </p>
            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={onEnterApp}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-blue-600 px-7 py-4 text-base font-extrabold text-white shadow-xl shadow-blue-600/25 transition hover:-translate-y-0.5 hover:bg-blue-700"
              >
                Start free <ArrowIcon />
              </button>
              <button
                onClick={scrollToPricing}
                className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white/80 px-7 py-4 text-base font-extrabold text-slate-950 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-300 hover:text-blue-700"
              >
                View demo
              </button>
            </div>
            <div className="mt-10 grid max-w-xl grid-cols-3 gap-4 border-t border-slate-200 pt-8 text-sm">
              <div>
                <p className="font-black text-slate-950">Local-first</p>
                <p className="mt-1 text-slate-500">Ollama-ready</p>
              </div>
              <div>
                <p className="font-black text-slate-950">3-step guardrail</p>
                <p className="mt-1 text-slate-500">Plan, evaluate, approve</p>
              </div>
              <div>
                <p className="font-black text-slate-950">Sprint format</p>
                <p className="mt-1 text-slate-500">BE / FE / QA</p>
              </div>
            </div>
          </div>
          <ProductPreview />
        </section>

        <section id="workflow" className="border-y border-slate-200/80 bg-white/72 py-20 backdrop-blur">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <h2 className="text-4xl font-black tracking-normal text-slate-950">A workflow built for agile teams</h2>
              <p className="mt-4 text-lg leading-8 text-slate-600">
                From stakeholder input to Jira or Slack—transparent, guided, and local-first.
              </p>
            </div>
            <div className="mt-12 grid gap-5 md:grid-cols-6">
              {workflowSteps.map((step, index) => (
                <div key={step.name} className="relative text-center">
                  {index < workflowSteps.length - 1 && (
                    <div className="absolute left-[58%] top-7 hidden h-px w-[84%] bg-slate-300 md:block" />
                  )}
                  <div className="relative mx-auto grid h-16 w-16 place-items-center rounded-2xl border border-blue-100 bg-blue-50 text-2xl text-blue-600 shadow-sm">
                    {['▣', '⌕', '▤', '◇', '✓', '↗'][index]}
                  </div>
                  <p className="mt-4 text-sm font-black text-slate-950">{step.name}</p>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{step.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-6 py-24 lg:px-8">
          <div className="mx-auto mb-12 max-w-3xl text-center">
            <h2 className="text-4xl font-black tracking-normal text-slate-950">Everything you need to deliver better sprints</h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <article key={feature.title} className="group rounded-[24px] border border-slate-200 bg-white/82 p-7 shadow-sm transition hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-900/10">
                <div className="mb-8 h-12 w-12 rounded-2xl bg-blue-600/10 text-blue-700">
                  <div className="grid h-full place-items-center">
                    <ArrowIcon />
                  </div>
                </div>
                <h3 className="text-lg font-black tracking-normal text-slate-950">{feature.title}</h3>
                <p className="mt-4 text-base leading-7 text-slate-600">{feature.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-6 pb-20 lg:px-8">
          <div className="grid items-center gap-10 rounded-[28px] border border-slate-200 bg-white/88 p-8 shadow-sm md:grid-cols-[0.8fr_1fr_0.9fr] md:p-10">
            <div className="grid h-36 w-36 place-items-center rounded-[32px] bg-gradient-to-br from-blue-100 to-violet-100 text-6xl text-blue-600">
              🔒
            </div>
            <div>
              <h2 className="text-3xl font-black tracking-normal text-slate-950">Local-first. Private by design.</h2>
              <p className="mt-4 text-base leading-7 text-slate-600">
                PM Agent runs locally in your environment. Your data never leaves your network. You stay in control.
              </p>
            </div>
            <div className="space-y-4 border-slate-200 md:border-l md:pl-8">
              {['Data stays local', 'Enterprise-ready', 'You’re in control'].map((item) => (
                <div key={item}>
                  <p className="font-black text-slate-950">{item}</p>
                  <p className="mt-1 text-sm text-slate-500">Set your models, roles, and audit rules.</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="pricing" className="mx-auto max-w-7xl px-6 pb-24 lg:px-8">
          <div className="mx-auto mb-10 max-w-3xl text-center">
            <h2 className="text-4xl font-black tracking-normal text-slate-950">Simple pricing. Start building today.</h2>
            <p className="mt-4 text-lg text-slate-600">Start free and upgrade when your team is ready.</p>
          </div>
          <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-2">
            {planCards.map((plan) => (
              <div key={plan.name} className={`rounded-[24px] border p-8 shadow-sm ${plan.highlighted ? 'border-transparent bg-gradient-to-br from-blue-600 to-violet-600 text-white' : 'border-slate-200 bg-white text-slate-950'}`}>
                <p className="text-xl font-black">{plan.name}</p>
                <p className={`mt-2 text-sm ${plan.highlighted ? 'text-blue-50' : 'text-slate-500'}`}>{plan.description}</p>
                <p className="mt-8 text-5xl font-black tracking-normal">{plan.price}</p>
                <p className={`mt-1 text-sm ${plan.highlighted ? 'text-blue-100' : 'text-slate-500'}`}>{plan.highlighted ? 'per user / month' : 'Forever'}</p>
                <div className="mt-8 space-y-3">
                  {plan.items.map((item) => (
                    <p key={item} className="flex items-center gap-3 text-sm font-semibold">
                      <span className={`grid h-5 w-5 place-items-center rounded-full ${plan.highlighted ? 'bg-white/15 text-white' : 'bg-emerald-50 text-emerald-600'}`}>✓</span>
                      {item}
                    </p>
                  ))}
                </div>
                <button
                  onClick={onEnterApp}
                  className={`mt-8 inline-flex w-full items-center justify-center rounded-xl px-5 py-3 text-sm font-extrabold transition hover:-translate-y-0.5 ${plan.highlighted ? 'bg-white text-blue-700' : 'border border-blue-200 text-blue-700 hover:bg-blue-50'}`}
                >
                  Start free
                </button>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer id="docs" className="relative z-10 bg-slate-950 text-white">
        <div className="mx-auto grid max-w-7xl gap-10 px-6 py-12 text-sm lg:grid-cols-[1.2fr_1fr_1fr_1fr] lg:px-8">
          <div>
            <p className="text-lg font-black">PM Agent</p>
            <p className="mt-4 max-w-xs leading-6 text-slate-400">Local-first AI for agile teams. Turn raw requests into sprint-ready Jira stories.</p>
          </div>
          {['Product', 'Workflow', 'Company'].map((group) => (
            <div key={group}>
              <p className="font-black">{group}</p>
              <div className="mt-4 space-y-3 text-slate-400">
                <p>Overview</p>
                <p>Docs</p>
                <p>Contact</p>
              </div>
            </div>
          ))}
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
