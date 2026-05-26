import { parseConfirmationPayload } from "../utils/formatters";

function ConfirmationCard({ actions, onResolve, isSubmitting }) {
  const parsedActions = parseConfirmationPayload(actions);
  if (parsedActions.length === 0) {
    return null;
  }

  return (
    <section className="rounded-md border border-amber-700 bg-amber-950/40 p-4">
      <h2 className="m-0 text-sm font-semibold text-amber-200">Pending Confirmation</h2>
      <div className="mt-3 space-y-3">
        {parsedActions.map((action) => (
          <article key={action.actionId} className="rounded-md border border-amber-800 bg-amber-950 p-3">
            <p className="m-0 text-sm font-medium text-amber-100">{action.title}</p>
            <p className="mt-1 text-xs text-amber-300">{action.description}</p>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => onResolve(action.actionId, action.actionType, true)}
                className="rounded-md bg-emerald-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-slate-700"
              >
                Approve
              </button>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={() => onResolve(action.actionId, action.actionType, false)}
                className="rounded-md bg-rose-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:bg-slate-700"
              >
                Reject
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default ConfirmationCard;
