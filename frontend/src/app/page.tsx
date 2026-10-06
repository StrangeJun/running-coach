export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
      <p className="mb-3 text-sm font-medium uppercase tracking-widest text-emerald-700">
        Personal running companion
      </p>
      <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
        Running Coach
      </h1>
      <p className="mt-6 max-w-xl text-lg leading-8 text-slate-600">
        Understand your runs and plan your next training session.
      </p>
      <section aria-labelledby="getting-started" className="mt-10 rounded-2xl border border-slate-200 bg-white p-6">
        <h2 id="getting-started" className="text-lg font-semibold text-slate-900">
          Your running journey starts here
        </h2>
        <p className="mt-2 leading-7 text-slate-600">
          Run import, analysis, and coaching are coming in a future update.
        </p>
      </section>
    </main>
  );
}
