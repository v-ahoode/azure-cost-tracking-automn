import logging

import azure.functions as func
from datetime import datetime, timezone, timedelta
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.costmanagement.models import (QueryDefinition, ExportType, TimeframeType, QueryTimePeriod, GranularityType, QueryDataset, QueryAggregation, QueryGrouping)
import json
import time

def get_cost(scope_with_rg , from_datetime, to_datetime, cost_mgmt_client):

    try:
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

        query_result = cost_mgmt_client.query.usage(scope=scope_with_rg, parameters=query_def)
        query_result_dict = query_result.as_dict()
        rows_of_cost = query_result_dict["rows"]

        return rows_of_cost
    except Exception as e:
        logging.exception("[ERROR]: Something went wrong while getting the cost")
        logging.exception(e)
        return []

def get_rgs_cost(resource_groups, scope, from_datetime, to_datetime, cost_mgmt_client):

    logging.info("-----------------Yesterday, Daily, Weekly & Monthly Cost-----------------")

    yesterday_cost_dict = {}
    yesterday_cost_dict["resourceGroupCost"] = list()
    yesterday_cost_dict["smfTotalCost"] = float(0)
    yesterday_cost_dict["lmfTotalCost"] = float(0)
    yesterday_cost_dict["aifTotalCost"] = float(0)
    yesterday_cost_dict["amTotalCost"] = float(0)
    yesterday_cost_dict["autmTotalCost"] = float(0) 
    yesterday_cost_dict["avdmTotalCost"] = float(0)
    yesterday_cost_dict["cmTotalCost"] = float(0)
    yesterday_cost_dict["dbmTotalCost"] = float(0)
    yesterday_cost_dict["infraTotalCost"] = float(0)
    yesterday_cost_dict["nwTotalCost"] = float(0)
    yesterday_cost_dict["totalCost"] = float(0)

    daily_cost_dict = {}
    daily_cost_dict["resourceGroupCost"] = list()
    daily_cost_dict["smfTotalCost"] = float(0)
    daily_cost_dict["lmfTotalCost"] = float(0)
    daily_cost_dict["aifTotalCost"] = float(0)
    daily_cost_dict["amTotalCost"] = float(0)
    daily_cost_dict["autmTotalCost"] = float(0) 
    daily_cost_dict["avdmTotalCost"] = float(0)
    daily_cost_dict["cmTotalCost"] = float(0)
    daily_cost_dict["dbmTotalCost"] = float(0)
    daily_cost_dict["infraTotalCost"] = float(0)
    daily_cost_dict["nwTotalCost"] = float(0)
    daily_cost_dict["totalCost"] = float(0)

    weekly_cost_dict = {}
    weekly_cost_dict["resourceGroupCost"] = list()
    weekly_cost_dict["smfTotalCost"] = float(0)
    weekly_cost_dict["lmfTotalCost"] = float(0)
    weekly_cost_dict["aifTotalCost"] = float(0)
    weekly_cost_dict["amTotalCost"] = float(0)
    weekly_cost_dict["autmTotalCost"] = float(0) 
    weekly_cost_dict["avdmTotalCost"] = float(0)
    weekly_cost_dict["cmTotalCost"] = float(0)
    weekly_cost_dict["dbmTotalCost"] = float(0)
    weekly_cost_dict["infraTotalCost"] = float(0)
    weekly_cost_dict["nwTotalCost"] = float(0)
    weekly_cost_dict["totalCost"] = float(0)

    monthly_cost_dict = {}
    monthly_cost_dict["resourceGroupCost"] = list()
    monthly_cost_dict["smfTotalCost"] = float(0)
    monthly_cost_dict["lmfTotalCost"] = float(0)
    monthly_cost_dict["aifTotalCost"] = float(0)
    monthly_cost_dict["amTotalCost"] = float(0)
    monthly_cost_dict["autmTotalCost"] = float(0) 
    monthly_cost_dict["avdmTotalCost"] = float(0)
    monthly_cost_dict["cmTotalCost"] = float(0)
    monthly_cost_dict["dbmTotalCost"] = float(0)
    monthly_cost_dict["infraTotalCost"] = float(0)
    monthly_cost_dict["nwTotalCost"] = float(0)
    monthly_cost_dict["totalCost"] = float(0)

    try:
        for x,rg in enumerate(resource_groups, start=1):
            logging.info(f"--------------------------------------{str(x)}--------------------------------------")
                        
            if rg.managed_by is None:
                scope_with_rg = '' + scope + str(rg.name)

                rows_of_cost = get_cost(scope_with_rg, from_datetime, to_datetime, cost_mgmt_client)

                logging.info(len(rows_of_cost))

                yesterday_row_of_cost = list()
                daily_weekly_rows_of_cost = list()
                monthly_rows_of_cost = list()

                if (len(rows_of_cost) <= 31 and len(rows_of_cost) > 0):
                    logging.info("[INFO]: Yesterday cost present")
                    yesterday_row_of_cost = [rows_of_cost[-1]]
                if (len(rows_of_cost) >= 8):
                    logging.info("[INFO]: Daily & Weekly cost present")
                    daily_weekly_rows_of_cost = rows_of_cost[len(rows_of_cost)-8: len(rows_of_cost)-1]
                if (len(rows_of_cost) == 31):
                    logging.info("[INFO]: Monthly cost present")
                    monthly_rows_of_cost = rows_of_cost[0: len(rows_of_cost)-1]

                if(len(yesterday_row_of_cost) == 1): 
                    past_numDays_cost = list()
                    for row in yesterday_row_of_cost: 
                        past_numDays_cost.append(row[0])
                    total_cost = float(sum(past_numDays_cost))

                    logging.info("[INFO]: Yesterdays' Total Cost: $ {0}".format(round(total_cost,2)))

                    if rg.tags is not None and "Team" in rg.tags.keys():
                        yesterday_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": rg.tags.get("Team"),
                            "rgcost": round(total_cost,2)
                        })
                    else:
                        yesterday_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": "NA",
                            "rgcost": round(total_cost,2)
                        })

                    if rg.tags is not None and "Team" in rg.tags.keys():
                        if rg.tags['Team'].strip().lower() == "SQL Migration".strip().lower():
                            yesterday_cost_dict["smfTotalCost"] = yesterday_cost_dict["smfTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Lakehouse Migration".strip().lower():
                            yesterday_cost_dict["lmfTotalCost"] = yesterday_cost_dict["lmfTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "AI".strip().lower():
                            yesterday_cost_dict["aifTotalCost"] = yesterday_cost_dict["aifTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "App Migration".strip().lower():
                            yesterday_cost_dict["amTotalCost"] = yesterday_cost_dict["amTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Automation".strip().lower():
                            yesterday_cost_dict["autmTotalCost"] = yesterday_cost_dict["autmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "AVD Migration".strip().lower():
                            yesterday_cost_dict["avdmTotalCost"] = yesterday_cost_dict["avdmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Cassandra Migration".strip().lower():
                            yesterday_cost_dict["cmTotalCost"] = yesterday_cost_dict["cmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "DB Migration".strip().lower():
                            yesterday_cost_dict["dbmTotalCost"] = yesterday_cost_dict["dbmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Infra".strip().lower():
                            yesterday_cost_dict["infraTotalCost"] = yesterday_cost_dict["infraTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Network".strip().lower():
                            yesterday_cost_dict["nwTotalCost"] = yesterday_cost_dict["nwTotalCost"] + total_cost
                else:
                    logging.info(f"[INFO]: Yesterdays' cost data not available from {from_datetime.date()} to {to_datetime.date()} for RG - {rg.name}")
                
                if(len(daily_weekly_rows_of_cost) == 7): 
                    past_numDays_cost = list()
                    for row in daily_weekly_rows_of_cost: 
                        past_numDays_cost.append(row[0])
                    avg_cost = float(sum(past_numDays_cost)/7) 
                    total_cost = float(sum(past_numDays_cost))

                    logging.info("[INFO]: Daily Avg Cost: $ {0}".format(round(avg_cost,2)))
                    logging.info("[INFO]: Weekly Total Cost: $ {0}".format(round(total_cost,2)))

                    if rg.tags is not None and "Team" in rg.tags.keys():
                        daily_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": rg.tags.get("Team"),
                            "rgcost": round(avg_cost,2)
                        })
                        weekly_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": rg.tags.get("Team"),
                            "rgcost": round(total_cost,2)
                        })
                    else:
                        daily_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": "NA",
                            "rgcost": round(avg_cost,2)
                        })
                        weekly_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": "NA",
                            "rgcost": round(total_cost,2)
                        })

                    if rg.tags is not None and "Team" in rg.tags.keys():
                        if rg.tags['Team'].strip().lower() == "SQL Migration".strip().lower():
                            daily_cost_dict["smfTotalCost"] = daily_cost_dict["smfTotalCost"] + avg_cost
                            weekly_cost_dict["smfTotalCost"] = weekly_cost_dict["smfTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Lakehouse Migration".strip().lower():
                            daily_cost_dict["lmfTotalCost"] = daily_cost_dict["lmfTotalCost"] + avg_cost
                            weekly_cost_dict["lmfTotalCost"] = weekly_cost_dict["lmfTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "AI".strip().lower():
                            daily_cost_dict["aifTotalCost"] = daily_cost_dict["aifTotalCost"] + avg_cost
                            weekly_cost_dict["aifTotalCost"] = weekly_cost_dict["aifTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "App Migration".strip().lower():
                            daily_cost_dict["amTotalCost"] = daily_cost_dict["amTotalCost"] + avg_cost
                            weekly_cost_dict["amTotalCost"] = weekly_cost_dict["amTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Automation".strip().lower():
                            daily_cost_dict["autmTotalCost"] = daily_cost_dict["autmTotalCost"] + avg_cost
                            weekly_cost_dict["autmTotalCost"] = weekly_cost_dict["autmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "AVD Migration".strip().lower():
                            daily_cost_dict["avdmTotalCost"] = daily_cost_dict["avdmTotalCost"] + avg_cost
                            weekly_cost_dict["avdmTotalCost"] = weekly_cost_dict["avdmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Cassandra Migration".strip().lower():
                            daily_cost_dict["cmTotalCost"] = daily_cost_dict["cmTotalCost"] + avg_cost
                            weekly_cost_dict["cmTotalCost"] = weekly_cost_dict["cmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "DB Migration".strip().lower():
                            daily_cost_dict["dbmTotalCost"] = daily_cost_dict["dbmTotalCost"] + avg_cost
                            weekly_cost_dict["dbmTotalCost"] = weekly_cost_dict["dbmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Infra".strip().lower():
                            daily_cost_dict["infraTotalCost"] = daily_cost_dict["infraTotalCost"] + avg_cost
                            weekly_cost_dict["infraTotalCost"] = weekly_cost_dict["infraTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Network".strip().lower():
                            daily_cost_dict["nwTotalCost"] = daily_cost_dict["nwTotalCost"] + avg_cost
                            weekly_cost_dict["nwTotalCost"] = weekly_cost_dict["nwTotalCost"] + total_cost
                else:
                    logging.info(f"[INFO]: Daily and Weekly cost data not available from {from_datetime.date()} to {to_datetime.date()} for RG - {rg.name}")

                if(len(monthly_rows_of_cost) == 30): 
                    past_numDays_cost = list()
                    for row in monthly_rows_of_cost: 
                        past_numDays_cost.append(row[0])
                    total_cost = float(sum(past_numDays_cost))

                    logging.info("[INFO]: Monthly Total Cost: $ {0}".format(round(total_cost,2)))

                    if rg.tags is not None and "Team" in rg.tags.keys():
                        monthly_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": rg.tags.get("Team"),
                            "rgcost": round(total_cost,2)
                        })
                    else:
                        monthly_cost_dict["resourceGroupCost"].append({
                            "rgname": rg.name,
                            "rgteam": "NA",
                            "rgcost": round(total_cost,2)
                        })

                    if rg.tags is not None and "Team" in rg.tags.keys():
                        if rg.tags['Team'].strip().lower() == "SQL Migration".strip().lower():
                            monthly_cost_dict["smfTotalCost"] = monthly_cost_dict["smfTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Lakehouse Migration".strip().lower():
                            monthly_cost_dict["lmfTotalCost"] = monthly_cost_dict["lmfTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "AI".strip().lower():
                            monthly_cost_dict["aifTotalCost"] = monthly_cost_dict["aifTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "App Migration".strip().lower():
                            monthly_cost_dict["amTotalCost"] = monthly_cost_dict["amTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Automation".strip().lower():
                            monthly_cost_dict["autmTotalCost"] = monthly_cost_dict["autmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "AVD Migration".strip().lower():
                            monthly_cost_dict["avdmTotalCost"] = monthly_cost_dict["avdmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Cassandra Migration".strip().lower():
                            monthly_cost_dict["cmTotalCost"] = monthly_cost_dict["cmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "DB Migration".strip().lower():
                            monthly_cost_dict["dbmTotalCost"] = monthly_cost_dict["dbmTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Infra".strip().lower():
                            monthly_cost_dict["infraTotalCost"] = monthly_cost_dict["infraTotalCost"] + total_cost
                        elif rg.tags['Team'].strip().lower() == "Network".strip().lower():
                            monthly_cost_dict["nwTotalCost"] = monthly_cost_dict["nwTotalCost"] + total_cost
                else:
                    logging.info(f"[INFO]: Monthly cost data not available from {from_datetime.date()} to {to_datetime.date()} for RG - {rg.name}")

            logging.info(f"--------------------------------------{str(x)}--------------------------------------")

            if x in range(1,100,5):
                time_to_wait = 10
                logging.info("++++++++++ Request throttled, waiting for 10 secs ++++++++++")
                time.sleep(time_to_wait)
                logging.info("++++++++++ Continuing ++++++++++")
    except Exception as e:
        logging.exception("[ERROR]: Something went wrong while calculating the cost")
        logging.exception(e)

    yesterday_cost_dict["smfTotalCost"] = round(yesterday_cost_dict["smfTotalCost"],2)            
    yesterday_cost_dict["lmfTotalCost"] = round(yesterday_cost_dict["lmfTotalCost"],2)      
    yesterday_cost_dict["aifTotalCost"] = round(yesterday_cost_dict["aifTotalCost"],2)
    yesterday_cost_dict["amTotalCost"] = round(yesterday_cost_dict["amTotalCost"],2)
    yesterday_cost_dict["autmTotalCost"] = round(yesterday_cost_dict["autmTotalCost"],2) 
    yesterday_cost_dict["avdmTotalCost"] = round(yesterday_cost_dict["avdmTotalCost"],2)
    yesterday_cost_dict["cmTotalCost"] = round(yesterday_cost_dict["cmTotalCost"],2)
    yesterday_cost_dict["dbmTotalCost"] = round(yesterday_cost_dict["dbmTotalCost"],2)
    yesterday_cost_dict["infraTotalCost"] = round(yesterday_cost_dict["infraTotalCost"],2)
    yesterday_cost_dict["nwTotalCost"] = round(yesterday_cost_dict["nwTotalCost"],2)    
    yesterday_cost_dict["totalCost"] = round(yesterday_cost_dict["smfTotalCost"]
                                             + yesterday_cost_dict["lmfTotalCost"]
                                             + yesterday_cost_dict["aifTotalCost"]
                                             + yesterday_cost_dict["amTotalCost"]
                                             + yesterday_cost_dict["autmTotalCost"]
                                             + yesterday_cost_dict["avdmTotalCost"]
                                             + yesterday_cost_dict["cmTotalCost"]
                                             + yesterday_cost_dict["dbmTotalCost"]
                                             + yesterday_cost_dict["infraTotalCost"]
                                             + yesterday_cost_dict["nwTotalCost"], 2)
    yesterday_cost_dict["fromDate"] = str(to_datetime.date())
    yesterday_cost_dict["toDate"] = str(to_datetime.date())

    daily_cost_dict["smfTotalCost"] = round(daily_cost_dict["smfTotalCost"],2)            
    daily_cost_dict["lmfTotalCost"] = round(daily_cost_dict["lmfTotalCost"],2)      
    daily_cost_dict["aifTotalCost"] = round(daily_cost_dict["aifTotalCost"],2) 
    daily_cost_dict["amTotalCost"] = round(daily_cost_dict["amTotalCost"],2)
    daily_cost_dict["autmTotalCost"] = round(daily_cost_dict["autmTotalCost"],2) 
    daily_cost_dict["avdmTotalCost"] = round(daily_cost_dict["avdmTotalCost"],2)
    daily_cost_dict["cmTotalCost"] = round(daily_cost_dict["cmTotalCost"],2)
    daily_cost_dict["dbmTotalCost"] = round(daily_cost_dict["dbmTotalCost"],2)
    daily_cost_dict["infraTotalCost"] = round(daily_cost_dict["infraTotalCost"],2)
    daily_cost_dict["nwTotalCost"] = round(daily_cost_dict["nwTotalCost"],2)     
    daily_cost_dict["totalCost"] = round(daily_cost_dict["smfTotalCost"]
                                             + daily_cost_dict["lmfTotalCost"]
                                             + daily_cost_dict["aifTotalCost"]
                                             + daily_cost_dict["amTotalCost"]
                                             + daily_cost_dict["autmTotalCost"]
                                             + daily_cost_dict["avdmTotalCost"]
                                             + daily_cost_dict["cmTotalCost"]
                                             + daily_cost_dict["dbmTotalCost"]
                                             + daily_cost_dict["infraTotalCost"]
                                             + daily_cost_dict["nwTotalCost"], 2)
    daily_cost_dict["fromDate"] = str((to_datetime - timedelta(days=7)).date())
    daily_cost_dict["toDate"] = str((to_datetime - timedelta(days=1)).date())

    weekly_cost_dict["smfTotalCost"] = round(weekly_cost_dict["smfTotalCost"],2)            
    weekly_cost_dict["lmfTotalCost"] = round(weekly_cost_dict["lmfTotalCost"],2)      
    weekly_cost_dict["aifTotalCost"] = round(weekly_cost_dict["aifTotalCost"],2)
    weekly_cost_dict["amTotalCost"] = round(weekly_cost_dict["amTotalCost"],2)
    weekly_cost_dict["autmTotalCost"] = round(weekly_cost_dict["autmTotalCost"],2) 
    weekly_cost_dict["avdmTotalCost"] = round(weekly_cost_dict["avdmTotalCost"],2)
    weekly_cost_dict["cmTotalCost"] = round(weekly_cost_dict["cmTotalCost"],2)
    weekly_cost_dict["dbmTotalCost"] = round(weekly_cost_dict["dbmTotalCost"],2)
    weekly_cost_dict["infraTotalCost"] = round(weekly_cost_dict["infraTotalCost"],2)
    weekly_cost_dict["nwTotalCost"] = round(weekly_cost_dict["nwTotalCost"],2)      
    weekly_cost_dict["totalCost"] = round(weekly_cost_dict["smfTotalCost"]
                                             + weekly_cost_dict["lmfTotalCost"]
                                             + weekly_cost_dict["aifTotalCost"]
                                             + weekly_cost_dict["amTotalCost"]
                                             + weekly_cost_dict["autmTotalCost"]
                                             + weekly_cost_dict["avdmTotalCost"]
                                             + weekly_cost_dict["cmTotalCost"]
                                             + weekly_cost_dict["dbmTotalCost"]
                                             + weekly_cost_dict["infraTotalCost"]
                                             + weekly_cost_dict["nwTotalCost"], 2)
    weekly_cost_dict["fromDate"] = str((to_datetime - timedelta(days=7)).date())
    weekly_cost_dict["toDate"] = str((to_datetime - timedelta(days=1)).date())

    monthly_cost_dict["smfTotalCost"] = round(monthly_cost_dict["smfTotalCost"],2)            
    monthly_cost_dict["lmfTotalCost"] = round(monthly_cost_dict["lmfTotalCost"],2)      
    monthly_cost_dict["aifTotalCost"] = round(monthly_cost_dict["aifTotalCost"],2)
    monthly_cost_dict["amTotalCost"] = round(monthly_cost_dict["amTotalCost"],2)
    monthly_cost_dict["autmTotalCost"] = round(monthly_cost_dict["autmTotalCost"],2) 
    monthly_cost_dict["avdmTotalCost"] = round(monthly_cost_dict["avdmTotalCost"],2)
    monthly_cost_dict["cmTotalCost"] = round(monthly_cost_dict["cmTotalCost"],2)
    monthly_cost_dict["dbmTotalCost"] = round(monthly_cost_dict["dbmTotalCost"],2)
    monthly_cost_dict["infraTotalCost"] = round(monthly_cost_dict["infraTotalCost"],2)
    monthly_cost_dict["nwTotalCost"] = round(monthly_cost_dict["nwTotalCost"],2)  
    monthly_cost_dict["totalCost"] = round(monthly_cost_dict["smfTotalCost"]
                                             + monthly_cost_dict["lmfTotalCost"]
                                             + monthly_cost_dict["aifTotalCost"]
                                             + monthly_cost_dict["amTotalCost"]
                                             + monthly_cost_dict["autmTotalCost"]
                                             + monthly_cost_dict["avdmTotalCost"]
                                             + monthly_cost_dict["cmTotalCost"]
                                             + monthly_cost_dict["dbmTotalCost"]
                                             + monthly_cost_dict["infraTotalCost"]
                                             + monthly_cost_dict["nwTotalCost"], 2)
    monthly_cost_dict["fromDate"] = str((to_datetime - timedelta(days=30)).date())
    monthly_cost_dict["toDate"] = str((to_datetime - timedelta(days=1)).date())

    return yesterday_cost_dict, daily_cost_dict, weekly_cost_dict, monthly_cost_dict

def get_estimation(monthly_cost_dict):

    estimation_cost_dict = {}

    estimation_cost_dict["resourceGroupCost"] = list()
    estimation_cost_dict["smfTotalCost"] = float(0)
    estimation_cost_dict["lmfTotalCost"] = float(0)
    estimation_cost_dict["aifTotalCost"] = float(0)
    estimation_cost_dict["amTotalCost"] = float(0)
    estimation_cost_dict["autmTotalCost"] = float(0) 
    estimation_cost_dict["avdmTotalCost"] = float(0)
    estimation_cost_dict["cmTotalCost"] = float(0)
    estimation_cost_dict["dbmTotalCost"] = float(0)
    estimation_cost_dict["infraTotalCost"] = float(0)
    estimation_cost_dict["nwTotalCost"] = float(0)
    estimation_cost_dict["totalCost"] = float(0)

    estimation_cost_dict["smfTotalCost"] = round(monthly_cost_dict["smfTotalCost"] * 12, 2)
    estimation_cost_dict["lmfTotalCost"] = round(monthly_cost_dict["lmfTotalCost"] * 12, 2)
    estimation_cost_dict["aifTotalCost"] = round(monthly_cost_dict["aifTotalCost"] * 12, 2)
    estimation_cost_dict["amTotalCost"] = round(monthly_cost_dict["amTotalCost"] * 12, 2)
    estimation_cost_dict["autmTotalCost"] = round(monthly_cost_dict["autmTotalCost"] * 12, 2) 
    estimation_cost_dict["avdmTotalCost"] = round(monthly_cost_dict["avdmTotalCost"] * 12, 2)
    estimation_cost_dict["cmTotalCost"] = round(monthly_cost_dict["cmTotalCost"] * 12, 2)
    estimation_cost_dict["dbmTotalCost"] = round(monthly_cost_dict["dbmTotalCost"] * 12, 2)
    estimation_cost_dict["infraTotalCost"] = round(monthly_cost_dict["infraTotalCost"] * 12, 2)
    estimation_cost_dict["nwTotalCost"] = round(monthly_cost_dict["nwTotalCost"] * 12, 2)
    estimation_cost_dict["totalCost"] = round(monthly_cost_dict["totalCost"] * 12, 2)

    return estimation_cost_dict

def main(name: str) -> dict:
    logging.info('Executing durable activity function')

    try:

        scope = "/subscriptions/edf6dd9d-7c4a-4bca-a997-945f3d60cf4e/resourceGroups/"
        
        toDate = datetime.strptime(datetime.utcnow().strftime("%Y-%m-%d 0:0"), "%Y-%m-%d 0:0").replace(tzinfo = timezone.utc)

        from_datetime =  (toDate - timedelta(days = 30 + 1)) 
        to_datetime = (toDate - timedelta(minutes=1))

        cred = DefaultAzureCredential( 
            exclude_environment_credential = True,
            exclude_powershell_credential = True,
            exclude_visual_studio_code_credential = True,
            exclude_shared_token_cache_credential = True,
            exclude_interactive_browser_credential = True,
        )  

        subscription_id = scope.split("/")[2]

        cost_mgmt_client = CostManagementClient(cred, 'https://management.azure.com')

        resource_mgmt_client = ResourceManagementClient(cred, subscription_id)

        resource_groups = resource_mgmt_client.resource_groups.list()
        resource_groups_list = list(resource_groups)

        rgs_cost_dict = {}

        rgs_cost_dict["yesterday"] = {}
        rgs_cost_dict["daily"] = {}
        rgs_cost_dict["weekly"] = {}
        rgs_cost_dict["monthly"] = {}
        rgs_cost_dict["estimation"] = {}
        
        rgs_cost_dict["yesterday"], rgs_cost_dict["daily"], rgs_cost_dict["weekly"], rgs_cost_dict["monthly"] = get_rgs_cost(resource_groups_list, scope, from_datetime, to_datetime, cost_mgmt_client)

        rgs_cost_dict["estimation"] = get_estimation(rgs_cost_dict["monthly"])

        rgs_cost_json = json.dumps(rgs_cost_dict)

        return rgs_cost_json

    except Exception as e:
        logging.exception("[ERROR]: Something went wrong in the activity function")
        return e