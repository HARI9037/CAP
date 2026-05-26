import { useState } from "react";

import { confirmAction } from "../services/api";

export default function useConfirmation() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const submitConfirmation = async (actionId, actionType, approved) => {
    setIsSubmitting(true);
    const response = await confirmAction(actionId, actionType, approved);
    setIsSubmitting(false);
    return response;
  };

  return {
    isSubmitting,
    submitConfirmation,
  };
}
