function NotFoundPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6 text-slate-100">
      <section className="rounded-md border border-slate-800 bg-slate-900 p-8 text-center">
        <h1 className="m-0 text-xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-slate-300">Return to the root URL to open CAP.</p>
      </section>
    </main>
  );
}

export default NotFoundPage;
