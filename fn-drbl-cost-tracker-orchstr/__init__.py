import logging
import json

import azure.functions as func
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    try:
        rgs_cost = yield context.call_activity('fn-drbl-cost-tracker-activity', None)
        return rgs_cost
    except Exception as e:
        logging.exception(e)
        return "Error"

main = df.Orchestrator.create(orchestrator_function)