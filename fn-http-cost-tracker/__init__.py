import logging

import azure.functions as func
from datetime import datetime, timezone, timedelta
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.costmanagement.models import (QueryDefinition, ExportType, TimeframeType, QueryTimePeriod, GranularityType, QueryDataset, QueryAggregation, QueryGrouping)
import json
import time

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json() 
        
        if req_body.get('numDays') is None:
            numDays = 7
        else:
            numDays = int(req_body.get('numDays'))

        if req_body.get('toDate') is None:
            toDate = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M").replace(tzinfo = timezone.utc)
        else:
            toDate = datetime.strptime(req_body.get('toDate'), "%Y-%m-%d %H:%M").replace(tzinfo = timezone.utc)
            
        scope = req_body.get('scope')

        from_datetime =  (toDate - timedelta(days = numDays)) 
        to_datetime = (toDate - timedelta(days = 1))
        
        cred = DefaultAzureCredential( 
            exclude_cli_credential = False,
            exclude_environment_credential = True,
            exclude_managed_identity_credential = False,
            exclude_powershell_credential = True,
            exclude_visual_studio_code_credential = True,
            exclude_shared_token_cache_credential = True,
            exclude_interactive_browser_credential = True,
        )  

        subscription_id = scope.split("/")[2]

        cost_mgmt_client = CostManagementClient(cred, 'https://management.azure.com')

        resource_mgmt_client = ResourceManagementClient(cred, subscription_id)

        query_dataset = QueryDataset(
            granularity=GranularityType("Daily"),                
            # configuration=QueryDatasetConfiguration(), 
            aggregation={"totalCost" : QueryAggregation(name="PreTaxCost", function ="Sum")}, 
            grouping=[QueryGrouping(type="Dimension", name="ResourceGroup")], 
            # filter = QueryFilter()
        )
        
        query_def = QueryDefinition(
            type=ExportType("Usage"),
            timeframe=TimeframeType("Custom"),            
            time_period=QueryTimePeriod(from_property=from_datetime, to=to_datetime),
            dataset=query_dataset
        )

        resourceGroups = resource_mgmt_client.resource_groups.list()

        rgs_cost_dict = {}
        rgs_cost_dict["resourceGroupCost"] = list()
        rgs_cost_dict["vcsaTotalCost"] = float(0)
        rgs_cost_dict["smfpTotalCost"] = float(0)

        for x,rg in enumerate(list(resourceGroups), start=1):
            logging.info(f"--------------------------------------{str(x)}----------------------------------------")
                        
            if rg.managed_by is None:
                scope_with_rg = '' + scope + str(rg.name)
                query_result = cost_mgmt_client.query.usage(scope=scope_with_rg, parameters=query_def)
                query_result_dict = query_result.as_dict()
                rows_of_cost = query_result_dict["rows"]
                
                if(len(rows_of_cost) == numDays): 
                    past_numDays_cost = list()
                    for row in rows_of_cost: 
                        past_numDays_cost.append(row[0])
                    avg_cost = float(sum(past_numDays_cost)/numDays) 

                    logging.info("Avg Cost: $ {0}".format(round(avg_cost,2)))

                    rgs_cost_dict["resourceGroupCost"].append({
                        "rgname": rg.name,
                        "rgteam": "NA",
                        "rgcost": round(avg_cost,2)
                    })
                    if rg.tags is not None and "Offering" in rg.tags.keys():
                        if rg.tags['Offering'] == "SQL Server Migration" or rg.tags['Offering'] == "SQL Migration":
                            rgs_cost_dict["resourceGroupCost"][-1]["rgteam"] = "SMFP"
                            rgs_cost_dict["smfpTotalCost"] = rgs_cost_dict["smfpTotalCost"] + avg_cost
                        else:
                            rgs_cost_dict["resourceGroupCost"][-1]["rgteam"] = "v-CSA"
                            rgs_cost_dict["vcsaTotalCost"] = rgs_cost_dict["vcsaTotalCost"] + avg_cost
                else:
                    logging.info(f"Cost data not available for the past {numDays} days for RG - {rg.name}")

            if x in range(1,40,5):
                logging.info("Request throttled, waiting for 10 secs")
                time.sleep(10)
                logging.info("Continuing")


        rgs_cost_dict["vcsaTotalCost"] = round(rgs_cost_dict["vcsaTotalCost"],2)            
        rgs_cost_dict["smfpTotalCost"] = round(rgs_cost_dict["smfpTotalCost"],2)      

        rgs_cost_json = json.dumps(rgs_cost_dict)

        return func.HttpResponse(rgs_cost_json,status_code=200)         

    except Exception as e:
        logging.exception(e)
        return func.HttpResponse(e,status_code=e.status_code)