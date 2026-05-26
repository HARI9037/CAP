function WarmupScreen({ errorMessage }) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
      <section className="w-full max-w-lg rounded-md border border-slate-800 bg-slate-900 p-8 text-center">
        <h1 className="m-0 text-2xl font-semibold text-slate-100">Warming up CAP...</h1>
        <p className="mt-3 text-sm text-slate-300">
          We are waiting for the backend to become available.
        </p>
        {errorMessage ? <p className="mt-3 text-xs text-amber-300">{errorMessage}</p> : null}
      </section>
    </main>
  );
}

export default WarmupScreen;
