import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import os, uuid
import re
import warnings

warnings.filterwarnings("ignore")

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest, OrderBy, Filter, FilterExpression
from google.oauth2 import service_account


import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

from django.conf import settings
from website.models import Resource, Submission, Category, NewsItem, Subscription, InLitResource


###
# Users represent individuals that visit your site. If that same User leaves your site and comes back later, Google Analytics will remember them, and their second visit won’t increase the number of Users (since they have already been accounted for in the past).
# Sessions represent a single visit to your website. Whether a User lands on one of your web pages and leaves a few seconds later, or spends an hour reading every blog post on your site, it still counts as a single Session. If that User leaves and then comes back later, it wouldn’t count as a new User (see above), but it would count as a new Session.
# Pageviews represent each individual time a page on your website is loaded by a User. A single Session can include many Pageviews, if a User navigates to any other web pages on your website without leaving.
###

# If analytics save directory does not exist, create it.
ANALYTICS_PLOT_DIR = os.path.join(settings.STATIC_ROOT, 'analytics_plots')
if not os.path.exists(ANALYTICS_PLOT_DIR):
   os.makedirs(ANALYTICS_PLOT_DIR)

class Analytics():
    def __init__(self):
        self.KEY_FILE = settings.ANALYTICS_KEY_FILE
        self.SCOPES = settings.ANALYTICS_SCOPES
        self.VIEW_ID = settings.ANALYTICS_VIEW_ID

        # self.KEY_FILE = settings.ANALYTICS_GA4_KEY_FILE
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'website/analytics/google_analytics_api_access_keys.json'
        self.property_id = settings.PROPERTY_ID

        self.dirname = os.path.dirname(__file__)

        self.analytics = self.initialize_analyticsreporting()
        self.internal_segment = [{"segmentId": "REDACTED # JPR Redacted Oct. 2024"}]

        # credentials = ServiceAccountCredentials.from_json_keyfile_dict(self.KEY_FILE)
        credentials = service_account.Credentials.from_service_account_file('website/analytics/google_analytics_api_access_keys.json')
        self.client = BetaAnalyticsDataClient(credentials=credentials)

        self.resources = pd.DataFrame(list(Resource.objects.values("id","name","subtitle","version","creation_date","last_modification_date","credits","description","code_languages","categories","logo_image","logo_link","about_link","ads_abstract_link","jupyter_link","download_link", "download_data_link","launch_link","demo_link","discuss_link","citation_count","related_tool_string","is_hosted","is_published","subdomain","path","status_notes","submission","related_resources","SEEC_tool").distinct()))
        self.categories = pd.DataFrame(list(Category.objects.values("id","index","name","abbreviation","theme_color","text_color","description","children").distinct()))
        self.news = pd.DataFrame(list(NewsItem.objects.values().distinct()))
        self.subscriptions = pd.DataFrame(list(Subscription.objects.values().distinct()))


    def initialize_analyticsreporting(self):
        """Initializes an Analytics Reporting API V4 service object.

        Returns:
        An authorized Analytics Reporting API V4 service object.
        """
        # credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, SCOPES)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(self.KEY_FILE, self.SCOPES)

        # Build the service object.
        analytics = build('analyticsreporting', 'v4', credentials=credentials)

        return analytics

    def get_report(self, metrics, dimensions, segments=None, dateRanges=[{'startDate': '2021-01-19', 'endDate': 'yesterday'}]):
        if segments != None:
            dimensions.append({"name": "ga:segment"})

        bdy = {
            'reportRequests': [
                {
                    'viewId': self.VIEW_ID,
                    'dateRanges': dateRanges,
                    'metrics': metrics,
                    'dimensions': dimensions,
                    "segments": segments
                }]
        }
        return self.analytics.reports().batchGet(body=bdy).execute()
    
    def format_report(self, metrics, dimensions, segments=None, dateRanges=[{'startDate': '2023-07-01', 'endDate': 'yesterday'}], dimension_filter=None):
        request = RunReportRequest(
            property='properties/'+self.property_id,
            dimensions=[Dimension(name=dimensions[i]) for i in range(len(dimensions))],
            metrics=[Metric(name=metrics[i]) for i in range(len(metrics))],
            # order_bys = [OrderBy(dimension = {'dimension_name': 'month'}),
            #             OrderBy(dimension = {'dimension_name': 'sessionMedium'})],
            date_ranges=[DateRange(start_date=dateRanges[0]['startDate'], end_date=dateRanges[0]['endDate'])],
            dimension_filter=dimension_filter 
            )

        response = self.client.run_report(request)
        
        # Row index
        row_index_names = [header.name for header in response.dimension_headers]
        row_header = []
        for i in range(len(row_index_names)):
            row_header.append([row.dimension_values[i].value for row in response.rows])

        row_index_named = pd.MultiIndex.from_arrays(np.array(row_header), names = np.array(row_index_names))
        # Row flat data
        metric_names = [header.name for header in response.metric_headers]
        data_values = []
        for i in range(len(metric_names)):
            data_values.append([row.metric_values[i].value for row in response.rows])

        output = pd.DataFrame(data = np.transpose(np.array(data_values, dtype = 'f')), 
                            index = row_index_named, columns = metric_names)
        return output

    def compile_response(self, response):
        data_dict = {}
        for report in response.get('reports', []):
            for row in report.get('data', {}).get('rows', []):
                dimensions = row.get('dimensions', [])
                dateRangeValues = row.get('metrics', [])

                data_dict[dimensions[0]] = int(dateRangeValues[0]["values"][0])
        return data_dict

    def make_clicks_per_tool(self):

        metrics = ['eventCount']
        dimensions = ['linkId']
        # Start collecting these on the day after the backup so we don't double count
        response = self.format_report(metrics, dimensions, dateRanges=[{'startDate': '2024-08-12', 'endDate': 'yesterday'}])
        # Skipping index 0 because it contains totals
        counts = response['eventCount'].to_numpy()[1:].astype(np.int64)
        linkIds = [e[0] for e in response.index.to_numpy()[1:]]
        resource_ids = [linkId[:linkId.index('_')]for linkId in linkIds]

        # Getting resource names from the resource using the ids
        resource_names = []
        # in_lit_resource_names = []
        for res_id in resource_ids:
            name = ''
            try:
                name = Resource.objects.get(id=res_id).name
            except Resource.DoesNotExist:
                name = ''
            resource_names.append(name)
        
        link_types = [linkId[linkId.index('_')+1:]for linkId in linkIds]
        # Include in-lit links
        # link_types = [link_type[:-7] if link_type[-6:] == 'in_lit' else link_type for link_type in link_types]
        # Do not include in-lit links
        link_types = [link_type for link_type in link_types if not(link_type[-6:] in ['in_lit','inlit'])]
        # Making names match with old button names
        link_types = ['ads_abstract_link' if link_type == 'abstract_link' else link_type for link_type in link_types]
        
        columns = ['name']
        columns += list(set(link_types))

        # Organizing clicks into dictionary
        clicks = dict((col,[]) for col in columns)

        for res, button, count in zip(resource_names, link_types, counts):
            # Get index
            try:
                i_res = clicks['name'].index(res)
            except ValueError:
                i_res = -1
            # Add in values
            if i_res == -1:
                for k in clicks:
                    clicks[k].append(0)
                clicks['name'][-1] = res
                clicks[button][-1] = count
            else:
                clicks[button][i_res] = count

        clicks_GA4 = pd.DataFrame.from_dict(clicks)

        # Get the number of direct visits to this resource's page on EMAC (https://emac.gsfc.nasa.gov?cid={cid})
        # metrics = ['screenPageViews']
        # dimensions = ['pageTitle']
        # response = self.format_report(metrics, dimensions)
        # print(response)
        # all_clicks = response['screenPageViews'].to_numpy()
        # all_pageTitles = response.index.to_numpy()
        # n = len(all_clicks)
        # visits = np.array([])
        # toolNames = np.array([])
        # for i in range(n):
        #     if 'Exoplanet Modeling and Analysis Center: ' in all_pageTitles[i][0]:
        #         toolName = all_pageTitles[i][0][40:]
        #         toolNames = np.append(toolNames, toolName)
        #         click_i = all_clicks[i]
        #         visits = np.append(visits, click_i)

        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/click_count_df_UA.csv')):
            metrics = [{'expression': 'ga:uniqueEvents'}]
            dimensions = [{'name': 'ga:eventLabel'}]

            all_response = self.get_report(metrics, dimensions)
            all_dict = self.compile_response(all_response)
            all_links = np.array([i for i in all_dict])
            all_clicks = np.array([all_dict[i] for i in all_dict])
            all_exits_df = pd.DataFrame({"All Links": all_links, "All Unique Events": all_clicks})

            internal_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_dict = self.compile_response(internal_response)
            internal_links = np.array([i for i in internal_dict])
            internal_clicks = np.array([internal_dict[i] for i in internal_dict])
            internal_exits_df = pd.DataFrame({"Internal Links": internal_links, "Internal Unique Events": internal_clicks})

            external_exits_df = all_exits_df.merge(internal_exits_df, left_on="All Links", right_on="Internal Links", how="left").drop("Internal Links", axis=1)

            external_exits_df["Internal Unique Events"] = external_exits_df["Internal Unique Events"].fillna(0)
            external_exits_df["External Unique Events"] = external_exits_df["All Unique Events"] - external_exits_df["Internal Unique Events"]
            exits_df = external_exits_df[["All Links", "External Unique Events"]].rename(columns={"All Links": "Link"})

            # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            #     print(exits_df)

            resource_df = self.resources
            resource_df = resource_df.drop_duplicates(subset=["name"])

            link_cols = [i for i in resource_df.columns if ("link" in i) and ("logo" not in i)]
            link_cols.insert(0, "name")
            link_df = resource_df[link_cols].fillna("None")

            # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            #     print(link_df)

            click_count_df = pd.DataFrame({"name":link_df["name"]})

            for col in link_df.columns:
                if "link" in col:
                    df = link_df[["name",col]].merge(exits_df, how="left", left_on=col, right_on="Link").drop([col,"Link"], axis=1).rename(columns={"External Unique Events": col}).fillna(0)
                    click_count_df = click_count_df.merge(df, left_on="name", right_on="name", how="inner")
            #
            # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            #     print(click_count_df)
            #
            # exits_breakdown = pd.DataFrame(data={"Tool": link_df["name"], "About Count": np.zeros(len(link_df["name"])),
            #                                      "ADS Count": np.zeros(len(link_df["name"])),
            #                                      "Download Count": np.zeros(len(link_df["name"])),
            #                                      "Launch Count": np.zeros(len(link_df["name"])),
            #                                      "Demo Count": np.zeros(len(link_df["name"])),
            #                                      "Discuss Count": np.zeros(len(link_df["name"]))})
            # accounted_for_links = []
            #
            # for name, about, ads, down, launch, demo, discuss in zip(link_df["name"], link_df["about_link"],
            #                                                          link_df["ads_abstract_link"], link_df["download_link"],
            #                                                          link_df["launch_link"], link_df["demo_link"],
            #                                                          link_df["discuss_link"]):
            #     for l in range(len(exits_df["Link"])):
            #         if (exits_df["Link"][l] == about):
            #             exits_breakdown.loc[exits_breakdown.Tool == name, "About Count"] = exits_df["External Unique Events"][l]
            #             accounted_for_links.append(exits_df["Link"][l])
            #         elif (exits_df["Link"][l] == ads):
            #             exits_breakdown.loc[exits_breakdown.Tool == name, "ADS Count"] = exits_df["External Unique Events"][l]
            #             accounted_for_links.append(exits_df["Link"][l])
            #         elif (exits_df["Link"][l] == down):
            #             exits_breakdown.loc[exits_breakdown.Tool == name, "Download Count"] = exits_df["External Unique Events"][l]
            #             accounted_for_links.append(exits_df["Link"][l])
            #         elif (exits_df["Link"][l] == launch):
            #             exits_breakdown.loc[exits_breakdown.Tool == name, "Launch Count"] = exits_df["External Unique Events"][l]
            #             accounted_for_links.append(exits_df["Link"][l])
            #         elif (exits_df["Link"][l] == demo):
            #             exits_breakdown.loc[exits_breakdown.Tool == name, "Demo Count"] = exits_df["External Unique Events"][l]
            #             accounted_for_links.append(exits_df["Link"][l])
            #         elif (exits_df["Link"][l] == discuss):
            #             exits_breakdown.loc[exits_breakdown.Tool == name, "Discuss Count"] = exits_df["External Unique Events"][l]
            #             accounted_for_links.append(exits_df["Link"][l])

            # exits_breakdown.loc[exits_breakdown.Tool == "HARDCORE", "Launch Count"] = exits_df.loc[exits_df.Link == "https://hardcore.emac.gsfc.nasa.gov", "External Unique Events"].values[0]
            # exits_breakdown.loc[exits_breakdown.Tool == "REPAST", "Launch Count"] = exits_df.loc[exits_df.Link == "https://tools.emac.gsfc.nasa.gov/repast", "External Unique Events"].values[0]
            # exits_breakdown.loc[exits_breakdown.Tool == "CGP", "Launch Count"] = exits_df.loc[exits_df.Link == "https://tools.emac.gsfc.nasa.gov/CGP", "External Unique Events"].values[0]
            # exits_breakdown.loc[exits_breakdown.Tool == "ECI", "Launch Count"] = exits_df.loc[exits_df.Link == "https://tools.emac.gsfc.nasa.gov/ECI", "External Unique Events"].values[0]

            # exits_breakdown2 = exits_breakdown.copy()
            # exits_breakdown2["Total"] = exits_breakdown.sum(axis=1)
            # exits_breakdown2 = exits_breakdown2.sort_values(by="Total", ascending=True).set_index("Tool")
            # exits_breakdown3 = exits_breakdown2[exits_breakdown2.Total > 0].drop("Total", axis=1)
            # exits_breakdown3 = (exits_breakdown3.reset_index().drop_duplicates(subset='Tool', keep='last').set_index('Tool'))

            # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            #     print(exits_breakdown3)

            click_count_df["totals"] = click_count_df.sum(axis=1, numeric_only=True)
            click_count_df = click_count_df.sort_values(by="totals", ascending=True)
            total = sum(click_count_df["totals"])
            click_count_df2 = click_count_df.nlargest(10, "totals")
            click_count_df2 = click_count_df2.sort_values(by="totals", ascending=True)
            click_count_df = click_count_df.drop("totals", axis=1)
            click_count_df2 = click_count_df2.drop("totals", axis=1)

            # with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            #     print(click_count_df)

            #Save the UA dataframes
            click_count_df.to_csv('website/analytics/UA_backup/click_count_df_UA.csv', index=False)
            click_count_df2.to_csv('website/analytics/UA_backup/click_count_df2_UA.csv', index=False)

        if not(os.path.exists('website/analytics/UA_backup/interim_clicks.csv')):
            metrics = ['eventCount']
            dimensions = ['eventName', 'customEvent:event_label']
            response = self.format_report(metrics, dimensions, dateRanges=[{'startDate': '2023-07-01', 'endDate': '2024-08-12'}])
            all_clicks = response.loc[['click'], :]
            links = np.array([e[1] for e in all_clicks.index])
            link_counts = all_clicks['eventCount']
            n = len(links)

            keys = ['about_link', 'ads_abstract_link', 'jupyter_link', 'download_link', 'download_data_link', 'launch_link', 'demo_link', 'discuss_link']
            resource_names = np.array([])
            link_types = np.array([])
            counts = np.array([])
            resources = Resource.objects.all()
            for i in range(n):
                link = links[i]
                count = link_counts[i]
                r = 0
                not_done = True
                while not_done and r < len(resources): 
                    resource = resources[r]
                    resource_links = [resource.__dict__[key] for key in keys]
                    if link in resource_links:
                        resource_names = np.append(resource_names,resource.name)
                        link_types = np.append(link_types,keys[resource_links.index(link)])
                        counts = np.append(counts,count)
                        not_done = False
                    r += 1
            
            # Organizing clicks into dictionary
            clicks = dict((col,[]) for col in columns)

            for res, button, count in zip(resource_names, link_types, counts):
                # Get index
                try:
                    i_res = clicks['name'].index(res)
                except ValueError:
                    i_res = -1
                # Add in values
                if i_res == -1:
                    for k in clicks:
                        clicks[k].append(0)
                    clicks['name'][-1] = res
                    clicks[button][-1] = count
                else:
                    clicks[button][i_res] = count

            clicks_interim = pd.DataFrame.from_dict(clicks)
            clicks_interim.to_csv('website/analytics/UA_backup/interim_clicks.csv', index=False)

        #Read the old dataframes from files
        if not(os.path.exists('website/analytics/UA_backup/clicks_old.csv')):
            clicks_UA = pd.read_csv('website/analytics/UA_backup/click_count_df_UA.csv')
            clicks_interim = pd.read_csv('website/analytics/UA_backup/interim_clicks.csv')
            clicks_old = clicks_UA.merge(clicks_interim, 'outer')
            clicks_old.to_csv('website/analytics/UA_backup/clicks_old.csv', index=False)

        # Merge new and old analytics and add between them
        clicks_old = pd.read_csv('website/analytics/UA_backup/clicks_old.csv')
        clicks_total = clicks_old.merge(clicks_GA4, 'outer')
        clicks_total = clicks_total.fillna(0.)
        clicks_total = clicks_total.groupby('name').sum()

        # Sort by total clicks
        clicks_total["totals"] = clicks_total.sum(axis=1, numeric_only=True)
        clicks_total = clicks_total.sort_values(by="totals", ascending=True)
        # clicks_total = clicks_total.nlargest(10, "totals")
        total = sum(clicks_total["totals"])
        width = max(clicks_total["totals"])
        clicks_total = clicks_total.drop("totals", axis=1)

        ax = clicks_total.plot.barh(stacked=True, figsize=(30, 500))
        fig = ax.get_figure()
        labels = [i[:40] for i in clicks_total.index]
        ax.set_yticklabels(tuple(labels))
        ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
        ax.xaxis.set_label_position('top')
        ax.set_xlim(0, width+60)
        ax.set_xlabel("Count", fontsize=30, labelpad=30)
        plt.xticks(fontsize=25)
        plt.yticks(fontsize=25)
        plt.title(f"External Unique Clicks per Tool, Jan. 19 2021 - Yesterday, Total: {total} \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}", fontsize=36, pad=36)
        plt.legend(prop={'size':25}, loc='upper right', framealpha=0.6)
        filename = os.path.join(ANALYTICS_PLOT_DIR, 'clicks_per_tool.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

        # ax = click_count_df2.plot.barh(stacked=True, figsize=(10, 15))
        # fig = ax.get_figure()
        # labels = [i for i in click_count_df2["name"]]
        # ax.set_yticklabels(tuple(labels))
        # ax.set_xlabel("Count")
        # ax.set_title(f"External Unique Clicks per Tool (Top 10), Jan. 19 2021 - Jun. 28 2023, Total: {total} \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        # filename = os.path.join(ANALYTICS_PLOT_DIR, 'top_10_clicks_per_tool.png')
        # plt.tight_layout()
        # fig.savefig(filename)
        # plt.close()

        totals = []
        names = []
        for col in clicks_total.columns:
            if col != "name":
                totals.append(sum(clicks_total[col]))
                names.append(col[:-5])

        fig, ax = plt.subplots()
        ax.bar(names, totals)

        ax.set_xlabel("Button Type")
        ax.set_ylabel("Clicks")
        ax.set_title(f"External Unique Clicks per Button Type, Jan. 19 2021 - Yesterday \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        ax.tick_params(axis='x', labelrotation=-45)

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'clicks_per_button.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_visits_over_time(self):
        metrics = ['sessions']
        dimensions = ['date']
        all_visits = self.format_report(metrics, dimensions)
        all_visits = all_visits.sort_values('date')
        num_visits_GA4 = all_visits['sessions'].to_numpy()
        dates_GA4 = all_visits.index.to_numpy()
        for i in range(len(dates_GA4)):
            date = dates_GA4[i][0]
            yr = int(date[:4])
            mo = int(date[4:6])
            da = int(date[6:8])
            dates_GA4[i] = datetime.datetime(yr, mo, da, 0, 0)

        # TODO:
        # internal_visits = self.format_report(metrics, dimensions, self.internal_segment)
        # internal_visits = internal_visits.sort_values('date')
        # clean_visits = all_visits.subtract(internal_visits, fill_value=0)
        # print(clean_visits)

        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/num_visits_df_UA.txt')):
            metrics = [{'expression': 'ga:sessions'}]
            dimensions = [{'name': 'ga:date'}]
            all_visits_response = self.get_report(metrics, dimensions)
            all_visits_dict = self.compile_response(all_visits_response)
            internal_visits_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_visits_dict = self.compile_response(internal_visits_response)

            for i in all_visits_dict.keys():
                if i not in internal_visits_dict:
                    internal_visits_dict[i] = 0
            internal_visits_dict = dict(sorted(internal_visits_dict.items()))
            dates = np.array([datetime.datetime.strptime(i, '%Y%m%d') for i in all_visits_dict])
            num_visits = np.array([all_visits_dict[i] - internal_visits_dict[i] for i in all_visits_dict])
            
            np.savetxt('website/analytics/UA_backup/num_visits_df_UA.txt', num_visits)

        #Read the UA dataframes from files
        num_visits_UA = np.loadtxt('website/analytics/UA_backup/num_visits_df_UA.txt')
        
        start = datetime.datetime.strptime("2021-01-19", '%Y-%m-%d')
        end = datetime.datetime.strptime("2023-06-28", '%Y-%m-%d')
        dates_UA = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days)]
        
        num_visits_df = np.append(num_visits_UA, num_visits_GA4)
        dates_df = np.append(dates_UA, dates_GA4)

        # dimensions = [Dimension(name="Date")]
        # metrics=[Metric(name="Sessions")]
        # all_visits_dict = self.format_report(metrics, dimensions)
        # dates = [datetime.datetime.strptime(i, '%Y%m%d') for i in all_visits_dict]
        # num_visits = all_visits_dict

        # for i in range(len(dates)):
        #     if dates[i] == datetime.datetime(2022, 7, 4, 0, 0):
        #         num_visits[i] = np.mean([num_visits[i-1], num_visits[i+1]]) # accounting for weird spike

        fig, ax = plt.subplots(1, 1)

        ax.plot_date(dates_df, num_visits_df, fmt=",-")

        plt.tick_params(axis='x', labelrotation=-45)
        plt.xlabel("Date")
        plt.ylabel("Sessions")
        fig.suptitle(f"External Sessions over Time, Jan. 19 2021 - Yesterday \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'visits_over_time.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_weekly_visits(self):
        metrics = ['sessions']
        dimensions = ['date']
        all_visits = self.format_report(metrics, dimensions)
        all_visits = all_visits.sort_values('date')
        num_visits_GA4 = all_visits['sessions'].to_numpy()
        weekly_num_visits_GA4 = np.array([])
        count = 0
        for i in range(len(num_visits_GA4)):
            if i % 7 == 0:
                weekly_num_visits_GA4 = np.append(weekly_num_visits_GA4, count)
                count = 0
            count += num_visits_GA4[i]
        weekly_num_visits_GA4 = weekly_num_visits_GA4[1:]
        
        # The weekly numbers have unexplainable spikes that do not agree with the daily counts

        # metrics = ['sessions']
        # dimensions = ['week']
        # all_weekly_visits = self.format_report(metrics, dimensions)
        # all_weekly_visits = all_weekly_visits.sort_values('week')

        start = datetime.datetime.strptime("2023-07-03", '%Y-%m-%d')
        end = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_dates_GA4 = [start + datetime.timedelta(days=7*x) for x in range(0, ((end-start+datetime.timedelta(days=6))//7).days)]

        while len(weekly_num_visits_GA4) > len(weekly_dates_GA4):
            weekly_num_visits_GA4 = np.delete(weekly_num_visits_GA4, -1)

        while len(weekly_dates_GA4) > len(weekly_num_visits_GA4):
            weekly_dates_GA4 = np.delete(weekly_dates_GA4, -1)

        # TODO: Filter out internal traffic

        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/weekly_num_visits_df_UA.txt')):
            metrics = [{'expression': 'ga:sessions'}]
            dimensions = [{'name': 'ga:yearWeek'}]
            all_weekly_visits_response = self.get_report(metrics, dimensions)
            all_weekly_visits_dict = self.compile_response(all_weekly_visits_response)
            internal_weekly_visits_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_weekly_visits_dict = self.compile_response(internal_weekly_visits_response)

            for i in all_weekly_visits_dict.keys():
                if i not in internal_weekly_visits_dict:
                    internal_weekly_visits_dict[i] = 0
            internal_weekly_visits_dict = dict(sorted(internal_weekly_visits_dict.items()))
            weekly_dates = [datetime.datetime.strptime(i + '-1', "%Y%W-%w") for i in all_weekly_visits_dict]
            weekly_num_visits = np.array([all_weekly_visits_dict[i] - internal_weekly_visits_dict[i] for i in all_weekly_visits_dict])

            for i in range(len(weekly_dates)):
                if weekly_dates[i] == datetime.datetime(2022, 7, 4, 0, 0):
                    weekly_num_visits[i+1] = np.mean([weekly_num_visits[i], weekly_num_visits[i+2]]) # accounting for weird spike

            np.savetxt('website/analytics/UA_backup/weekly_num_visits_df_UA.txt', weekly_num_visits)
        
        fig, ax = plt.subplots()

        #Read the UA dataframes from files
        weekly_num_visits_UA = np.loadtxt('website/analytics/UA_backup/weekly_num_visits_df_UA.txt')

        start = datetime.datetime.strptime("2021-01-25", '%Y-%m-%d')
        end = datetime.datetime.strptime("2023-07-11", '%Y-%m-%d')
        weekly_dates_UA = [start + datetime.timedelta(days=7*x) for x in range(0, ((end-start)//7).days)]
        weekly_dates_UA = np.insert(weekly_dates_UA, 49, weekly_dates_UA[49])
        weekly_dates_UA = np.insert(weekly_dates_UA, 102, weekly_dates_UA[102])

        weekly_num_visits_df = np.append(weekly_num_visits_UA, weekly_num_visits_GA4)
        weekly_dates_df = np.append(weekly_dates_UA, weekly_dates_GA4)

        spikes = np.array([])
        spike_dates = np.array([])
        for spike, date in zip(weekly_num_visits_df, weekly_dates_df):
            if spike > 500:
                spikes = np.append(spikes, spike)
                spike_dates = np.append(spike_dates, date)

        fig, ax = plt.subplots(1, 1)

        ax.plot_date(weekly_dates_df, weekly_num_visits_df, fmt=",-")
        ax.set_ylim(0, 400)  # most of the data

        old_date = start
        for spike, date in zip(spikes, spike_dates):
            if date - old_date > datetime.timedelta(days=180):
                plt.annotate(
                    spike,
                    xy=(date, 400), xytext=(-10, -10),
                    textcoords='offset points', ha='right', va='top',
                    fontsize = 8,
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            else:
                plt.annotate(
                    spike,
                    xy=(date, 400), xytext=(10, -10),
                    textcoords='offset points', ha='left', va='top',
                    fontsize = 8,
                    bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
            old_date = date
        plt.tick_params(axis='x', labelrotation=-45)
        plt.xlabel("Date")
        plt.ylabel("Sum of Sessions")
        fig.suptitle(f"External Sessions by Week, Jan. 19 2021 - Yesterday \n  Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'weekly_visits.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_exit_clicks_by_category(self):

        # Get the subcategories
        cats = [cat for cat in Category.objects.all() if not(cat.has_parents())]
        cat_names = [cat.name for cat in cats]
        resources = Resource.objects.all()
        n_resources = len(resources)
        subcat_counts = dict((col, 0) for col in cats)
        for resource in resources:
            res_cats = resource.categories.all()
            for res_cat in res_cats:
                if res_cat in subcat_counts:
                    subcat_counts[res_cat] += 1
        subcategory_counts = {}
        for key in subcat_counts:
            subcategory_counts[key.name] = subcat_counts[key]
        subcategory_counts = {'name': list(subcategory_counts.keys()), 'Total Resources (this category)': list(subcategory_counts.values())}
        subcategory_counts = pd.DataFrame.from_dict(subcategory_counts)
        subcategory_counts.set_index('name', inplace=True)
        
        metrics = ['eventCount']
        dimensions = ['linkId']
        # Start collecting these on the day after the backup so we don't double count
        response = self.format_report(metrics, dimensions, dateRanges=[{'startDate': '2024-08-12', 'endDate': 'yesterday'}])
        # Skipping index 0 because it contains totals
        counts = response['eventCount'].to_numpy()[1:].astype(np.int64)
        linkIds = [e[0] for e in response.index.to_numpy()[1:]]
        resource_ids = [linkId[:linkId.index('_')]for linkId in linkIds]

        # Getting resource names from the resource using the ids
        resource_cats = []
        # in_lit_resource_names = []
        for res_id in resource_ids:
            cat = []
            try:
                cat = [c.name for c in Resource.objects.get(id=res_id).categories.all()]
            except Resource.DoesNotExist:
                cat = []
            resource_cats.append(cat)
        
        columns = cat_names

        # Organizing clicks into dictionary
        clicks = dict((col,0) for col in columns)

        for res_cats, count in zip(resource_cats, counts):
            for cat in res_cats:
                if cat in clicks:
                    clicks[cat] += count

        cats_GA4 = {'name': list(clicks.keys()), 'Total Clicks (this category)': list(clicks.values())}
        cats_GA4 = pd.DataFrame.from_dict(cats_GA4)
        cats_GA4.set_index('name', inplace=True)

        if not(os.path.exists('website/analytics/UA_backup/interim_cats.csv')):
            metrics = ['eventCount']
            dimensions = ['eventName', 'customEvent:event_label']
            response = self.format_report(metrics, dimensions, dateRanges=[{'startDate': '2023-07-01', 'endDate': '2024-08-12'}])
            all_clicks = response.loc[['click'], :]
            links = np.array([e[1] for e in all_clicks.index])
            counts = [all_clicks['eventCount'][i] for i in range(len(links))]
            n = len(links)
            category_clicks = dict([(category.name, 0) for category in cats])
            keys = ['about_link', 'ads_abstract_link', 'jupyter_link', 'download_link', 'download_data_link', 'launch_link', 'demo_link', 'discuss_link']
            for i in range(n):
                link = links[i]
                count = counts[i]
                r = 0
                not_done = True
                while not_done and r < len(resources): 
                    resource = resources[r]
                    resource_links = [resource.__dict__[key] for key in keys]
                    if link in resource_links:
                        for category in cats:
                            if category in resource.categories.all():
                                category_clicks[category.name] += count
                                not_done = False
                    r += 1
            cat_clicks ={'name':np.array(list(category_clicks.keys())),
                        'Total Clicks (this category)':np.array(list(category_clicks.values())),
                        }
            cat_clicks = pd.DataFrame.from_dict(cat_clicks)
            cat_clicks.set_index('name', inplace=True)
            cat_clicks.to_csv('website/analytics/UA_backup/interim_cats.csv')


        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/exit_cats_UA.csv')):
            metrics = [{'expression': 'ga:uniqueEvents'}]
            dimensions = [{'name': 'ga:eventLabel'}]

            all_response = self.get_report(metrics, dimensions)
            all_dict = self.compile_response(all_response)
            all_links = np.array([i for i in all_dict])
            all_clicks = np.array([all_dict[i] for i in all_dict])
            all_exits_df = pd.DataFrame({"All Links": all_links, "All Unique Events": all_clicks})

            internal_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_dict = self.compile_response(internal_response)
            internal_links = np.array([i for i in internal_dict])
            internal_clicks = np.array([internal_dict[i] for i in internal_dict])
            internal_exits_df = pd.DataFrame({"Internal Links": internal_links, "Internal Unique Events": internal_clicks})

            external_exits_df = all_exits_df.merge(internal_exits_df, left_on="All Links", right_on="Internal Links", how="left").drop("Internal Links", axis=1)

            external_exits_df["Internal Unique Events"] = external_exits_df["Internal Unique Events"].fillna(0)
            external_exits_df["External Unique Events"] = external_exits_df["All Unique Events"] - external_exits_df["Internal Unique Events"]
            exits_df = external_exits_df[["All Links", "External Unique Events"]].rename(columns={"All Links": "Link"})

            resource_df = self.resources
            resource_df_unique = resource_df.drop_duplicates(subset=["name"])

            link_cols = [i for i in resource_df.columns if ("link" in i) and ("logo" not in i)]
            link_cols.insert(0, "name")
            link_df = resource_df_unique[link_cols].fillna("None")

            click_count_df = pd.DataFrame({"name":link_df["name"]})

            for col in link_df.columns:
                if "link" in col:
                    df = link_df[["name",col]].merge(exits_df, how="left", left_on=col, right_on="Link").drop([col,"Link"], axis=1).rename(columns={"External Unique Events": col}).fillna(0)
                    click_count_df = click_count_df.merge(df, left_on="name", right_on="name", how="inner")

            click_count_df["totals"] = click_count_df.sum(axis=1, numeric_only=True)
            total_exits = click_count_df[["name", "totals"]]

            resource_cats = resource_df[["name", "categories"]]
            cats = self.categories
            cats = cats.dropna(subset=['children']).drop_duplicates(subset = "id")
            cats2 = cats[["id", "name"]]

            resource_cats = pd.merge(resource_cats, cats2, left_on="categories", right_on="id", how="left")
            resource_cats = resource_cats.dropna(subset=['categories'])
            cat_counts = resource_cats.groupby("name_y").count().reset_index()
            exit_cats = pd.merge(resource_cats, total_exits, left_on="name_x", right_on="name").groupby("categories").sum()

            exit_cats = exit_cats.merge(cats2, left_index=True, right_on="id")
            exit_cats = exit_cats.merge(cat_counts, left_on="name", right_on="name_y")

            exit_cats = exit_cats[["name", "totals", "categories"]]
            exit_cats["norm"] = exit_cats["totals"]/exit_cats["categories"]
            exit_cats = exit_cats[["name", "totals", "norm"]].rename(columns={"totals":"Total Clicks (this category)", "norm":"Total Clicks (this category) / Number of tools (this category)"})

            exit_cats = exit_cats.sort_values(by="Total Clicks (this category)", ascending=False)
            exit_cats = exit_cats.set_index("name")

            exit_cats.to_csv('website/analytics/UA_backup/exit_cats_UA.csv', index=True)

        #Read the UA dataframes from files
        if not(os.path.exists('website/analytics/UA_backup/old_cats.csv')):
            cats_UA = pd.read_csv('website/analytics/UA_backup/exit_cats_UA.csv')
            cats_UA = cats_UA.drop(columns='Total Clicks (this category) / Number of tools (this category)')
            cats_interim = pd.read_csv('website/analytics/UA_backup/interim_cats.csv')
            cats_old = cats_UA.merge(cats_interim, 'outer')
            cats_old = cats_old.fillna(0.)
            cats_old = cats_old.groupby('name').sum()
            cats_old.to_csv('website/analytics/UA_backup/old_cats.csv', index=True)

        cats_old = pd.read_csv('website/analytics/UA_backup/old_cats.csv')
        cats = cats_old.merge(cats_GA4, 'outer')
        cats = cats.fillna(0.)
        cats = cats.groupby('name').sum()
        cats = cats.drop(index=0.)
        cats = cats.join(subcategory_counts)
        cats = cats.fillna(0.)
        cats = cats.sort_values(by="Total Clicks (this category)", ascending=False)
        cats["Clicks per resource (this category)"] = cats["Total Clicks (this category)"] / cats["Total Resources (this category)"]
        cats = cats.drop(columns="Total Resources (this category)")
        
        
        # ax = cats.plot.barh(stacked=False, figsize=(15, 10))
        ax = cats.plot(kind='bar', secondary_y="Clicks per resource (this category)", rot= -45, figsize=(15, 10))
        fig = ax.get_figure()
        ax1, ax2 = plt.gcf().get_axes() # gets the current figure and then the axes
        ax1.set_ylabel('Click Count', fontsize=20)
        ax2.set_ylabel('Clicks per resource', fontsize=20)
        ax.set_xlabel('Categories', fontsize=20)
        ax.set_title(f"External Unique Clicks per Category \n Jan. 19 2021 - Yesterday, Generated {datetime.datetime.now().replace(second=0, microsecond=0)}", fontsize=25)
        for label in ax.get_xticklabels():
            label.set_horizontalalignment('left')
        filename = os.path.join(ANALYTICS_PLOT_DIR, 'exit_clicks_by_category.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_twitter_analytics(self):
        TWITTER_KEY_FILE = settings.TWITTER_SHEETS_KEY_FILE
        # TWITTER_SCOPES = settings.TWITTER_SCOPES
        gc = gspread.service_account_from_dict(TWITTER_KEY_FILE)
        gsheet = gc.open_by_url("REDACTED URL") # JPR Redacted Oct. 2024

        data = gsheet.sheet1.get_all_records()
        all_tweets = pd.DataFrame(data)
        all_tweets["time"] = all_tweets["time"].str[:10]

        all_tweets["time"] = pd.to_datetime(all_tweets["time"], format='%Y-%m-%d').dt.date
        all_tweets = all_tweets.sort_values(by=['time'], ascending=False)

        fig, ax = plt.subplots()
        ax.xaxis_date()
        ax.plot_date(all_tweets["time"], all_tweets["engagements"], fmt=".-")
        ax.set_xlabel("Date")
        ax.set_ylabel("Engagements")
        ax.set_title(f"Tweet Engagements")
        ax.tick_params(axis='x', labelrotation=-45)
        filename = os.path.join(ANALYTICS_PLOT_DIR, 'tweet_engagements.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

        fig, ax = plt.subplots()
        ax.xaxis_date()
        ax.plot_date(all_tweets["time"], all_tweets["impressions"], fmt=".-")
        ax.set_xlabel("Date")
        ax.set_ylabel("Impressions")
        ax.set_title(f"Tweet Impressions")
        ax.tick_params(axis='x', labelrotation=-45)
        filename = os.path.join(ANALYTICS_PLOT_DIR, 'tweet_impressions.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

        top_engagement_tweets = all_tweets.sort_values(by=['engagements'], ascending=False)[["Tweet text", "time", "engagements"]][all_tweets["time"]>=datetime.date(year=2021,month=1,day=19)].head(3)
        top_engagement_text = []
        top_engagement_time = []
        top_engagement_engagements = []
        # c = 1
        for tweet, time, engagements in zip(top_engagement_tweets["Tweet text"], top_engagement_tweets["time"], top_engagement_tweets["engagements"]):
            # top_engagement_dict[c] = [tweet, time, engagements]
            top_engagement_text.append(tweet)
            top_engagement_time.append(time)
            top_engagement_engagements.append(engagements)
            # c += 1

        bot_engagement_tweets = all_tweets.sort_values(by=['engagements'], ascending=True)[["Tweet text", "time", "engagements"]][all_tweets["time"]>=datetime.date(year=2021,month=1,day=19)].head(3)
        bot_engagement_text = []
        bot_engagement_time = []
        bot_engagement_engagements = []
        for tweet, time, engagements in zip(bot_engagement_tweets["Tweet text"], bot_engagement_tweets["time"], bot_engagement_tweets["engagements"]):
            bot_engagement_text.append(tweet)
            bot_engagement_time.append(time)
            bot_engagement_engagements.append(engagements)

        # top_impression_tweets = all_tweets.sort_values(by=['impressions'], ascending=False)[["Tweet text", "time", "impressions"]].head(3)
        # top_impression_dict = {}
        # c = 1
        # for tweet, time, impressions in zip(top_impression_tweets["Tweet text"], top_impression_tweets["time"],top_impression_tweets["impressions"]):
        #     top_impression_dict[c] = [tweet, time, impressions]
        #     c += 1

        # data = {"Date":external_dates[external_sources=="Twitter"].T, "Sessions":external_sessions[external_sources=="Twitter"].T}
        # tweet_referrals_df = pd.DataFrame(data)
        # indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=2)
        # tweet_referrals_df["Rolling Sessions"] = tweet_referrals_df.rolling(window=indexer, min_periods=1).sum()
        # # # tweet_visits_df = pd.DataFrame({"Date":tweet_dates, "Following Sessions":social_referrals[external_sources=="Twitter"]}).drop_duplicates("Date")
        # sorted_all_tweets = all_tweets.sort_values(by=['time'], ascending=True).groupby("time").sum().reset_index()
        #
        # tweet_impact_df = tweet_referrals_df.merge(right=sorted_all_tweets[["time","engagements"]][sorted_all_tweets["time"]>=datetime.date(year=2021,month=1,day=19)], how="right", left_on="Date", right_on="time").dropna()
        # daily_combined_tweet_text = all_tweets[["time", "Tweet text"]].groupby("time")["Tweet text"].apply(','.join).reset_index().sort_values(by=['time'], ascending=True)
        # tweet_impact_df = tweet_impact_df.merge(daily_combined_tweet_text, how="left", left_on="Date", right_on="time")[["Date", "engagements", "Rolling Sessions", "Tweet text"]]
        #
        # fig, ax = plt.subplots()
        # ax.scatter(tweet_impact_df["engagements"], tweet_impact_df["Rolling Sessions"])
        # ax.set_xlabel("Engagements")
        # ax.set_ylabel("Following Sessions")
        # ax.set_title(f"Tweet Impact on Site Visits (last updated 10/14)")
        # ax.tick_params(axis='x', labelrotation=-45)
        #
        # filename = os.path.join(ANALYTICS_PLOT_DIR, 'tweet_impact.png')
        # plt.tight_layout()
        # fig.savefig(filename)
        # plt.close()
        #
        # top_following_sessions = tweet_impact_df.sort_values(by=['Rolling Sessions'], ascending=False)[["Rolling Sessions", "Tweet text", "Date"]].head(3)
        # top_following_sessions_dict = {}
        # c = 1
        # for tweet, time, sessions in zip(top_following_sessions["Tweet text"], top_following_sessions["Date"], top_following_sessions["Rolling Sessions"]):
        #     top_following_sessions_dict[c] = [tweet, time, sessions]
        #     c += 1
        #
        # bot_following_sessions = tweet_impact_df.sort_values(by=['Rolling Sessions'], ascending=True)[["Rolling Sessions", "Tweet text", "Date"]].head(3)
        # bot_following_sessions_dict = {}
        # c = 1
        # for tweet, time, sessions in zip(bot_following_sessions["Tweet text"], bot_following_sessions["Date"], bot_following_sessions["Rolling Sessions"]):
        #     bot_following_sessions_dict[c] = [tweet, time, sessions]
        #     c += 1

        return top_engagement_text, top_engagement_time, top_engagement_engagements, bot_engagement_text, bot_engagement_time, bot_engagement_engagements

    def make_social_traffic(self):
        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/external_twitter_sessions_df_UA.txt') and os.path.exists('website/analytics/UA_backup/external_youtube_sessions_df_UA.txt')):
            metrics = [{'expression': 'ga:sessions'}]
            dimensions = [{'name': 'ga:date'}, {'name':'ga:source'}]

            all_response = self.get_report(metrics, dimensions)
            all_dates = []
            all_sources = []
            all_sessions = []
            for report in all_response.get('reports', []):
                for row in report.get('data', {}).get('rows', []):
                    dimensions = row.get('dimensions', [])
                    if 't.co' in dimensions[1]:
                        source = "Twitter"
                    elif 'facebook' in dimensions[1]:
                        source = "Facebook"
                    elif 'youtube' in dimensions[1]:
                        source = 'Youtube'
                    elif 'reddit' in dimensions[1]:
                        source = 'Reddit'
                    else:
                        continue
                    all_sources.append(source)
                    all_dates.append(datetime.datetime.strptime(dimensions[0], '%Y%m%d').date())
                    metrics = row.get('metrics', [])
                    all_sessions.append(int(metrics[0]["values"][0]))

            metrics = [{'expression': 'ga:sessions'}]
            dimensions = [{'name': 'ga:date'}, {'name':'ga:source'}]
            internal_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_dates = []
            internal_sources = []
            internal_sessions = []
            for report in internal_response.get('reports', []):
                for row in report.get('data', {}).get('rows', []):
                    dimensions = row.get('dimensions', [])
                    if 't.co' in dimensions[1]:
                        source = "Twitter"
                    elif 'facebook' in dimensions[1]:
                        source = "Facebook"
                    elif 'youtube' in dimensions[1]:
                        source = 'Youtube'
                    elif 'reddit' in dimensions[1]:
                        source = 'Reddit'
                    else:
                        continue
                    internal_sources.append(source)
                    internal_dates.append(datetime.datetime.strptime(dimensions[0], '%Y%m%d').date())
                    metrics = row.get('metrics', [])
                    internal_sessions.append(int(metrics[0]["values"][0]))

            external_dates = []
            external_sources = []
            external_sessions = []
            for i, j, k in zip(all_dates, all_sources, all_sessions):
                date = i
                source = j
                session = k
                for a, b, c in zip(internal_dates, internal_sources, internal_sessions):
                    if date == a and source == b:
                        session = session - c
                        if session < 0: # internal traffic but no external traffic
                            session = 0
                    else:
                        continue
                external_dates.append(date)
                external_sources.append(source)
                external_sessions.append(session)
            external_dates = np.array(external_dates)
            external_sources = np.array(external_sources)
            external_sessions = np.array(external_sessions)

            external_twitter_dates = external_dates[external_sources=="Twitter"]
            external_twitter_sessions = external_sessions[external_sources=="Twitter"]
            external_youtube_dates = external_dates[external_sources=="Youtube"]
            external_youtube_sessions = external_sessions[external_sources=="Youtube"]

            np.savetxt('website/analytics/UA_backup/external_twitter_sessions_df_UA.txt', external_twitter_sessions)
            np.savetxt('website/analytics/UA_backup/external_youtube_sessions_df_UA.txt', external_youtube_sessions)

        external_youtube_dates_df = np.array([datetime.date(2021, 1, 19),datetime.date(2021, 1, 20),datetime.date(2021, 1, 24),datetime.date(2021, 1, 26),datetime.date(2021, 1, 27),datetime.date(2021, 1, 28),datetime.date(2021, 2, 2),datetime.date(2021, 2, 3),datetime.date(2021, 2, 8),datetime.date(2021, 2, 9),datetime.date(2021, 2, 12),datetime.date(2021, 2, 16),datetime.date(2021, 2, 23),datetime.date(2021, 2, 24),datetime.date(2021, 2, 25),datetime.date(2021, 2, 26),datetime.date(2021, 3, 2),datetime.date(2021, 3, 4),datetime.date(2021, 3, 5),datetime.date(2021, 3, 6),datetime.date(2021, 3, 8),datetime.date(2021, 3, 9),datetime.date(2021, 3, 16),datetime.date(2021, 3, 17),datetime.date(2021, 3, 18),datetime.date(2021, 3, 22),datetime.date(2021, 3, 23),datetime.date(2021, 3, 25),datetime.date(2021, 3, 26),datetime.date(2021, 4, 3),datetime.date(2021, 4, 6),datetime.date(2021, 4, 7),datetime.date(2021, 4, 8),datetime.date(2021, 4, 10),datetime.date(2021, 4, 11),datetime.date(2021, 4, 12),datetime.date(2021, 4, 13),datetime.date(2021, 4, 14),datetime.date(2021, 4, 15),datetime.date(2021, 4, 20),datetime.date(2021, 4, 21),datetime.date(2021, 4, 22),datetime.date(2021, 4, 26),datetime.date(2021, 4, 27),datetime.date(2021, 4, 28),datetime.date(2021, 4, 29),datetime.date(2021, 4, 30),datetime.date(2021, 5, 2),datetime.date(2021, 5, 4),datetime.date(2021, 5, 5),datetime.date(2021, 5, 6),datetime.date(2021, 5, 8),datetime.date(2021, 5, 9),datetime.date(2021, 5, 11),datetime.date(2021, 5, 12),datetime.date(2021, 5, 13),datetime.date(2021, 5, 14),datetime.date(2021, 5, 18),datetime.date(2021, 5, 24),datetime.date(2021, 5, 25),datetime.date(2021, 5, 26),datetime.date(2021, 6, 1),datetime.date(2021, 6, 2),datetime.date(2021, 6, 3),datetime.date(2021, 6, 4),datetime.date(2021, 6, 7),datetime.date(2021, 6, 8),datetime.date(2021, 6, 9),datetime.date(2021, 6, 10),datetime.date(2021, 6, 15),datetime.date(2021, 6, 16),datetime.date(2021, 6, 17),datetime.date(2021, 6, 18),datetime.date(2021, 6, 19),datetime.date(2021, 6, 20),datetime.date(2021, 6, 21),datetime.date(2021, 6, 22),datetime.date(2021, 6, 24),datetime.date(2021, 6, 28),datetime.date(2021, 7, 1),datetime.date(2021, 7, 9),datetime.date(2021, 7, 10),datetime.date(2021, 7, 11),datetime.date(2021, 7, 13),datetime.date(2021, 7, 22),datetime.date(2021, 7, 28),datetime.date(2021, 8, 2),datetime.date(2021, 8, 5),datetime.date(2021, 8, 9),datetime.date(2021, 8, 13),datetime.date(2021, 8, 14),datetime.date(2021, 8, 17),datetime.date(2021, 8, 25),datetime.date(2021, 8, 28),datetime.date(2021, 8, 30),datetime.date(2021, 9, 1),datetime.date(2021, 9, 5),datetime.date(2021, 9, 9),datetime.date(2021, 9, 10),datetime.date(2021, 9, 13)])
        external_twitter_dates_df = np.array([datetime.date(2021, 1, 19),datetime.date(2021, 1, 20),datetime.date(2021, 1, 21),datetime.date(2021, 1, 22),datetime.date(2021, 1, 23),datetime.date(2021, 1, 25),datetime.date(2021, 1, 26),datetime.date(2021, 1, 27),datetime.date(2021, 1, 28),datetime.date(2021, 1, 29),datetime.date(2021, 2, 1),datetime.date(2021, 2, 2),datetime.date(2021, 2, 3),datetime.date(2021, 2, 4),datetime.date(2021, 2, 8),datetime.date(2021, 2, 9),datetime.date(2021, 2, 10),datetime.date(2021, 2, 11),datetime.date(2021, 2, 12),datetime.date(2021, 2, 14),datetime.date(2021, 2, 16),datetime.date(2021, 2, 19),datetime.date(2021, 2, 20),datetime.date(2021, 2, 21),datetime.date(2021, 3, 2),datetime.date(2021, 3, 16),datetime.date(2021, 3, 25),datetime.date(2021, 3, 30),datetime.date(2021, 4, 2),datetime.date(2021, 4, 4),datetime.date(2021, 4, 8),datetime.date(2021, 4, 21),datetime.date(2021, 4, 22),datetime.date(2021, 4, 28),datetime.date(2021, 4, 29),datetime.date(2021, 5, 1),datetime.date(2021, 5, 3),datetime.date(2021, 5, 4),datetime.date(2021, 5, 5),datetime.date(2021, 5, 8),datetime.date(2021, 5, 14),datetime.date(2021, 5, 15),datetime.date(2021, 5, 16),datetime.date(2021, 5, 18),datetime.date(2021, 5, 21),datetime.date(2021, 5, 23),datetime.date(2021, 5, 25),datetime.date(2021, 6, 5),datetime.date(2021, 6, 8),datetime.date(2021, 6, 9),datetime.date(2021, 6, 11),datetime.date(2021, 6, 12),datetime.date(2021, 6, 14),datetime.date(2021, 6, 18),datetime.date(2021, 6, 26),datetime.date(2021, 6, 29),datetime.date(2021, 6, 29),datetime.date(2021, 6, 30),datetime.date(2021, 6, 30),datetime.date(2021, 7, 1),datetime.date(2021, 7, 2),datetime.date(2021, 7, 3),datetime.date(2021, 7, 4),datetime.date(2021, 7, 5),datetime.date(2021, 7, 6),datetime.date(2021, 7, 7),datetime.date(2021, 7, 9),datetime.date(2021, 7, 13),datetime.date(2021, 7, 13),datetime.date(2021, 7, 15),datetime.date(2021, 7, 15),datetime.date(2021, 7, 17),datetime.date(2021, 7, 19),datetime.date(2021, 7, 20),datetime.date(2021, 7, 21),datetime.date(2021, 7, 25),datetime.date(2021, 7, 27),datetime.date(2021, 7, 28),datetime.date(2021, 7, 30),datetime.date(2021, 8, 3),datetime.date(2021, 8, 4),datetime.date(2021, 8, 6),datetime.date(2021, 8, 10),datetime.date(2021, 8, 12),datetime.date(2021, 8, 13),datetime.date(2021, 8, 14),datetime.date(2021, 8, 17),datetime.date(2021, 8, 19),datetime.date(2021, 8, 23),datetime.date(2021, 8, 24),datetime.date(2021, 8, 25),datetime.date(2021, 8, 26),datetime.date(2021, 8, 27),datetime.date(2021, 8, 28),datetime.date(2021, 8, 31),datetime.date(2021, 9, 1),datetime.date(2021, 9, 2),datetime.date(2021, 9, 3),datetime.date(2021, 9, 7),datetime.date(2021, 9, 9),datetime.date(2021, 9, 10),datetime.date(2021, 9, 10),datetime.date(2021, 9, 11),datetime.date(2021, 9, 12),datetime.date(2021, 9, 12),datetime.date(2021, 9, 13),datetime.date(2021, 9, 14),datetime.date(2021, 9, 15),datetime.date(2021, 9, 15),datetime.date(2021, 9, 18),datetime.date(2021, 9, 20),datetime.date(2021, 9, 22),datetime.date(2021, 9, 22),datetime.date(2021, 9, 22),datetime.date(2021, 9, 23),datetime.date(2021, 9, 24)])

        #Read the UA dataframes from files
        external_twitter_sessions_df = np.loadtxt('website/analytics/UA_backup/external_twitter_sessions_df_UA.txt')
        external_youtube_sessions_df = np.loadtxt('website/analytics/UA_backup/external_youtube_sessions_df_UA.txt')


        fig, ax = plt.subplots()
        ax.plot(external_twitter_dates_df, external_twitter_sessions_df, label="Twitter")
        ax.plot(external_youtube_dates_df, external_youtube_sessions_df, label="Youtube")
        ax.legend()
        ax.set_xlabel("Date")
        ax.set_ylabel("External Sessions")
        ax.set_title(f"Social Media Traffic \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        ax.tick_params(axis='x', labelrotation=-45)

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'social_traffic.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_RSS_report(self):
        
        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/news_df_UA.csv')):
            metrics = [{'expression': 'ga:pageviews'}]
            dimensions = [{'name': 'ga:pagePathLevel2'}]

            all_drilldown = self.get_report(metrics, dimensions)
            all_drilldown = self.compile_response(all_drilldown)
            all_rss_pages = dict()
            for i in all_drilldown:
                if re.search("^\/\d?\d\/$", i) != None:
                    all_rss_pages[i] = all_drilldown[i]
            internal_drilldown = self.get_report(metrics, dimensions, self.internal_segment)
            internal_drilldown = self.compile_response(internal_drilldown)
            internal_rss_pages = dict()
            for i in internal_drilldown:
                if re.search("^\/\d?\d\/$", i) != None:
                    internal_rss_pages[i] = internal_drilldown[i]

            all_rss_ids = np.array([int(i[1:-1]) for i in all_rss_pages.keys()])
            all_rss_vals = np.array([i for i in all_rss_pages.values()])
            all_rss_df = pd.DataFrame({"ids":all_rss_ids, "all_vals":all_rss_vals})
            internal_rss_ids = np.array([int(i[1:-1]) for i in internal_rss_pages.keys()])
            internal_rss_vals = np.array([i for i in internal_rss_pages.values()])
            internal_rss_df = pd.DataFrame({"ids": internal_rss_ids, "internal_vals": internal_rss_vals})
            rss_df = all_rss_df.merge(internal_rss_df, on="ids", how="left")
            rss_df["internal_vals"] = rss_df["internal_vals"].fillna(0)
            rss_df["external_vals"] = rss_df["all_vals"] - rss_df["internal_vals"]

            news_df = self.news
            news_df = news_df.merge(rss_df[["ids", "external_vals"]], how="right", left_on="id", right_on="ids").sort_values(by="id")

            news_df.to_csv('website/analytics/UA_backup/news_df_UA.csv', index=False)

        #Read the UA dataframes from files
        news_df = pd.read_csv('website/analytics/UA_backup/news_df_UA.csv')

        vals = news_df["external_vals"][5:]
        keys = news_df["title"][5:]

        fig, ax = plt.subplots()
        ax.bar(range(len(keys)), vals, align="center")
        ax.set_xlabel("RSS Post")
        ax.set_ylabel("External Pageviews")
        ax.set_title(f"RSS Viewership \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        ax.set_xticks([i for i in range(len(vals))])
        ax.set_xticklabels(keys, ha="left")
        ax.tick_params(axis='x', labelrotation=-25)
        # for i in range(len(keys)):
        #     ax.annotate(keys[i], xy=(i, vals[i]+0.5), horizontalalignment='center')

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'RSS_report.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    # JPR 2023-04-24 - Disabling YouTube analytics due to error in `analytix` package.
    # def make_youtube_analytics(self):
    #     from analytix import Analytics as yt_analytix
    #     CLIENT_SECRETS_FILE = os.path.join(self.dirname, 'secrets.json')
    #     client = yt_analytix.with_secrets(CLIENT_SECRETS_FILE)
    #     CLIENT_TOKENS_FILE = os.path.join(self.dirname, 'tokens.json')
    #     client.authorise(token_path=CLIENT_TOKENS_FILE)

    #     report = client.retrieve(dimensions=("day",), metrics=("views","subscribersGained","subscribersLost"), start_date=datetime.date(2020,9,29), end_date=datetime.date.today())
    #     channel_stats_df = report.to_dataframe()

    #     # channel_stats_df["net_subs"] = channel_stats_df["subscribersGained"] - channel_stats_df["subscribersLost"]
    #     # cumulative_subs = [sum(channel_stats_df["net_subs"][:i + 1]) for i in range(len(channel_stats_df["net_subs"]))]
    #     # channel_stats_df["cumulative_subs"] = cumulative_subs

    #     date_range = pd.period_range(start=datetime.date(2020,9,29), end=datetime.date.today(), freq='W-SUN')
    #     date_range = date_range.map(str)
    #     date_range = date_range.str.split('/').str[0]
    #     date_range = [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in date_range]
    #     w = 0
    #     weeks = []
    #     for d in channel_stats_df["day"]:
    #         if d <= date_range[w]:
    #             weeks.append(date_range[w])
    #         elif d > date_range[w]:
    #             w += 1
    #             weeks.append(date_range[w])
    #     channel_stats_df["week"] = weeks
    #     weekly_channel_stats_df = channel_stats_df.groupby("week").sum().reset_index()

    #     weekly_channel_stats_df["net_subs"] = weekly_channel_stats_df["subscribersGained"] - weekly_channel_stats_df["subscribersLost"]
    #     cumulative_subs = [sum(weekly_channel_stats_df["net_subs"][:i + 1]) for i in range(len(weekly_channel_stats_df["net_subs"]))]
    #     weekly_channel_stats_df["cumulative_subs"] = cumulative_subs

    #     fig, ax1 = plt.subplots()

    #     ax1.plot_date(weekly_channel_stats_df["week"], weekly_channel_stats_df["cumulative_subs"], color="blue", fmt=",-", alpha=0.5, linewidth=5)
    #     ax1.set_ylabel("Cumulative Subscribers", color="blue")
    #     ax1.tick_params(axis='y', labelcolor="blue")

    #     ax2 = ax1.twinx()
    #     ax2.plot_date(weekly_channel_stats_df["week"], weekly_channel_stats_df["views"], color="red", fmt=",-", alpha=0.5)
    #     ax2.set_ylabel('Views/Week', color="red")
    #     ax2.tick_params(axis='y', labelcolor="red")

    #     ax1.set_title(f"Weekly YouTube Channel Stats \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
    #     ax1.set_xlabel("Date")
    #     ax1.tick_params(axis='x', labelrotation=-45)

    #     filename = os.path.join(ANALYTICS_PLOT_DIR, 'yt_channel_stats.png')
    #     plt.tight_layout()
    #     fig.savefig(filename)
    #     plt.close()

    #     report = client.retrieve(dimensions=("video",), metrics=("views","subscribersGained","subscribersLost"), start_date=datetime.date(2020,9,29), end_date=datetime.date.today(), max_results=100, sort_options=["-views"])
    #     vid_stats_df = report.to_dataframe()

    #     key = settings.YT_KEY
    #     client = Client(key)

    #     video_titles = []
    #     for video_id in vid_stats_df["video"]:
    #         title = client.get_video(video_id).title
    #         if len(title)>10:
    #             title = title[:10]+"..."
    #         video_titles.append(title)
    #     vid_stats_df["title"] = video_titles

    #     vid_stats_df["sub_net"] = vid_stats_df["subscribersGained"] - vid_stats_df["subscribersLost"]

    #     fig, ax1 = plt.subplots(figsize=(15, 5))

    #     # normmin = min(vid_stats_df["sub_net"])
    #     # normmax = max(vid_stats_df["sub_net"])
    #     # data_color = [(x - normmin) / (normmax - normmin) for x in vid_stats_df["sub_net"]]  # see the difference here
    #     # my_cmap = plt.cm.get_cmap('RdYlGn')
    #     # colors = my_cmap(data_color)

    #     ax1.bar(vid_stats_df["title"], vid_stats_df["views"])
    #     # ax1.bar(vid_stats_df["title"], vid_stats_df["views"], color=colors)

    #     # sm = ScalarMappable(cmap=my_cmap, norm=plt.Normalize(normmin, normmax))
    #     # sm.set_array([])
    #     # cax = fig.add_axes([1.2, 0.25, 0.02, 0.6])
    #     # cbar = fig.colorbar(sm, cax=cax)
    #     # cbar.set_label('Net Subscribers', rotation=0, labelpad=25)

    #     ax1.tick_params(axis='x', labelrotation=-90)
    #     ax1.set_ylabel("Views")
    #     ax1.set_title(f"YouTube Video Stats \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
    #     plt.tight_layout()
    #     filename = os.path.join(ANALYTICS_PLOT_DIR, 'yt_video_stats.png')
    #     fig.savefig(filename)
    #     plt.close()

    #     return None

    def make_tools_per_category(self):
        resource_df = self.resources
        resource_df = resource_df.drop_duplicates(subset=["name"])
        resource_cats = resource_df[["name", "categories"]]

        cats = self.categories
        cats = cats.dropna(subset=['children']).drop_duplicates(subset = "id")
        cats2 = cats[["id", "name"]].set_index("id")

        cat_names = []
        for i in resource_cats["categories"]:
            try:
                cat_names.append(cats2.loc[i]["name"])
            except KeyError:
                cat_names.append(np.nan)

        resource_cats["categories"] = cat_names
        resource_cats = resource_cats.dropna(subset=['categories'])

        cat_counts = resource_cats.groupby("categories").count().reset_index()

        # cat_order = ["Stellar Models and Catalogs", "Planetary Atmosphere Models", "Planetary Interior Models", "Radiative Transfer Tools", "Observatory/Instrument Models", "Model-Fitting Tools", "Data Reduction Tools", "Planet Form. and Dynamics Tools", "Planet Populations", "Data Visualization Tools", "Hardware Control & Optimization"]
        # try:
        #     cat_counts = cat_counts.reindex(cat_order).reset_index()
        # except:
        #     cat_counts = cat_counts.reset_index()

        fig, ax = plt.subplots()
        ax.barh(cat_counts["categories"], cat_counts["name"], align='center')
        # ax.set_yticks(range(len(cat_counts["categories"])))
        # ax.set_yticklabels(cat_counts["categories"])
        ax.set_xlabel("Count")
        ax.set_title(f'Number of Tools per Category \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}')
        ax.invert_yaxis()

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'tools_per_category.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_tools_per_coding_language(self):
        resource_df = self.resources
        resource_df = resource_df.drop_duplicates(subset=["name"])

        code_languages = resource_df['code_languages']
        split_code_languages = code_languages.str.split(", ")
        exploded_code_laguages = split_code_languages.explode()
        df = pd.DataFrame({"code_languages": exploded_code_laguages})
        df = df.groupby("code_languages").size().reset_index()
        df.columns = ["code_languages", "count"]
        df = df.sort_values(by="count")

        fig, ax = plt.subplots()
        ax.barh(df["code_languages"], df["count"], align='center')
        ax.set_xlabel('Count')
        ax.set_title(f"Number of Tools per Coding Language \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'tools_per_coding_language.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_new_visitors_over_time(self):
        
        metrics = ['newUsers']
        dimensions = ['date']
        all_new_visitors = self.format_report(metrics, dimensions)
        all_new_visitors = all_new_visitors.sort_values('date')
        all_new_visitors = all_new_visitors['newUsers'].to_numpy()
        all_new_visitors_GA4 = np.array([])
        count = 0
        for i in range(len(all_new_visitors)):
            if i % 7 == 0:
                all_new_visitors_GA4 = np.append(all_new_visitors_GA4, count)
                count = 0
            count += all_new_visitors[i]
        all_new_visitors_GA4 = all_new_visitors_GA4[1:]

        start = datetime.datetime.strptime("2023-07-03", '%Y-%m-%d')
        end = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_dates_GA4 = [start + datetime.timedelta(days=7*x) for x in range(0, ((end-start+datetime.timedelta(days=6))//7).days)]

        while len(all_new_visitors_GA4) > len(weekly_dates_GA4):
            all_new_visitors_GA4 = np.delete(all_new_visitors_GA4, -1)

        while len(weekly_dates_GA4) > len(all_new_visitors_GA4):
            weekly_dates_GA4 = np.delete(weekly_dates_GA4, -1)

        cumulative_num_visitors_GA4 = [sum(all_new_visitors_GA4[:i+1]) for i in range(len(all_new_visitors_GA4))]

        # TODO: Filter out internal traffic

        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/cumulative_num_visitors_df_UA.txt') and os.path.exists('website/analytics/UA_backup/num_new_users_df_UA.txt')):
            metrics = [{'expression': 'ga:newUsers'}]
            dimensions = [{'name': 'ga:yearWeek'}, {'name': 'ga:userType'}]
            all_new_visitors_response = self.get_report(metrics, dimensions)
            all_new_visitors_dict = self.compile_response(all_new_visitors_response)
            internal_new_visitors_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_new_visitors_dict = self.compile_response(internal_new_visitors_response)

            for i in all_new_visitors_dict.keys():
                if i not in internal_new_visitors_dict:
                    internal_new_visitors_dict[i] = 0
            internal_new_visitors_dict = dict(sorted(internal_new_visitors_dict.items()))
            dates = [datetime.datetime.strptime(i + '-1', "%Y%W-%w") for i in all_new_visitors_dict]

            # metrics = [{'expression': 'ga:sessions'}]
            # dimensions = [{'name': 'ga:yearWeek'}]
            # all_weekly_visits_response = self.get_report(metrics, dimensions)
            # all_weekly_visits_dict = self.compile_response(all_weekly_visits_response)
            # dates = [datetime.datetime.strptime(i + '-1', "%Y%W-%w") for i in all_weekly_visits_dict]

            num_new_users = [all_new_visitors_dict[i] - internal_new_visitors_dict[i] for i in all_new_visitors_dict]
            for i in range(len(dates)):
                if dates[i] == datetime.datetime(2022, 7, 4, 0, 0):
                    num_new_users[i + 1] = np.mean([num_new_users[i], num_new_users[i + 2]])  # accounting for weird spike

            cumulative_num_visitors = [sum(num_new_users[:i+1]) for i in range(len(num_new_users))]

            np.savetxt('website/analytics/UA_backup/cumulative_num_visitors_df_UA.txt', cumulative_num_visitors)
            np.savetxt('website/analytics/UA_backup/num_new_users_df_UA.txt', num_new_users)

        #Read the UA dataframes from files
        cumulative_num_visitors_UA = np.loadtxt('website/analytics/UA_backup/cumulative_num_visitors_df_UA.txt')
        num_new_users_UA = np.loadtxt('website/analytics/UA_backup/num_new_users_df_UA.txt')

        start = datetime.datetime.strptime("2021-01-25", '%Y-%m-%d')
        end = datetime.datetime.strptime("2023-07-11", '%Y-%m-%d')
        weekly_dates_UA = [start + datetime.timedelta(days=7*x) for x in range(0, ((end-start)//7).days)]
        weekly_dates_UA = np.insert(weekly_dates_UA, 49, weekly_dates_UA[49])
        weekly_dates_UA = np.insert(weekly_dates_UA, 102, weekly_dates_UA[102])
        
        weekly_dates_df = np.append(weekly_dates_UA, weekly_dates_GA4)
        cumulative_num_visitors_df = np.append(cumulative_num_visitors_UA, cumulative_num_visitors_GA4+cumulative_num_visitors_UA[-1])
        num_new_users_df = np.append(num_new_users_UA, all_new_visitors_GA4)
        
        #Read the UA dataframes from files
        # dates_df = pd.read_csv('website/analytics/UA_backup/dates_df.csv')
        # num_new_users_df = pd.read_csv('website/analytics/UA_backup/num_new_users_df_UA.csv')
        # cumulative_num_visitors_df = pd.read_csv('website/analytics/UA_backup/cumulative_num_visitors_df_UA.csv')
        
        fig, ax1 = plt.subplots()

        ax1.plot_date(weekly_dates_df, cumulative_num_visitors_df, color="blue", fmt=",-", alpha=0.5, linewidth=5)
        ax1.set_ylabel("Cumulative New Visitors", color="blue")
        ax1.tick_params(axis='y', labelcolor="blue")

        ax2 = ax1.twinx()
        ax2.plot_date(weekly_dates_df, num_new_users_df, color="red", fmt=",-", alpha=0.5)
        ax2.set_ylabel('Weekly New Visitors', color="red")
        ax2.tick_params(axis='y', labelcolor="red")

        ax1.set_title(f"New Visitors to EMAC, Jan. 19 2021 - Yesterday \n Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        ax1.set_xlabel("Date")
        ax1.tick_params(axis='x', labelrotation=-45)

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'new_visitors_over_time.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_new_visitors_fraction_over_time(self):
        
        metrics = ['newUsers']
        dimensions = ['date']
        all_new_visitors = self.format_report(metrics, dimensions)
        all_new_visitors = all_new_visitors.sort_values('date')
        all_new_visitors = all_new_visitors['newUsers'].to_numpy()
        all_new_visitors_GA4 = np.array([])
        count = 0
        for i in range(len(all_new_visitors)):
            if i % 7 == 0:
                all_new_visitors_GA4 = np.append(all_new_visitors_GA4, count)
                count = 0
            count += all_new_visitors[i]
        all_new_visitors_GA4 = all_new_visitors_GA4[1:]

        start = datetime.datetime.strptime("2023-07-03", '%Y-%m-%d')
        end = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_dates_GA4 = [start + datetime.timedelta(days=7*x) for x in range(0, ((end-start+datetime.timedelta(days=6))//7).days)]

        while len(all_new_visitors_GA4) > len(weekly_dates_GA4):
            all_new_visitors_GA4 = np.delete(all_new_visitors_GA4, -1)

        while len(weekly_dates_GA4) > len(all_new_visitors_GA4):
            weekly_dates_GA4 = np.delete(weekly_dates_GA4, -1)

        metrics = ['totalUsers']
        dimensions = ['date']
        all_visitors = self.format_report(metrics, dimensions)
        all_visitors = all_visitors.sort_values('date')
        all_visitors = all_visitors['totalUsers'].to_numpy()
        all_visitors_GA4 = np.array([])
        count = 0
        for i in range(len(all_new_visitors)):
            if i % 7 == 0:
                all_visitors_GA4 = np.append(all_visitors_GA4, count)
                count = 0
            count += all_visitors[i]
        all_visitors_GA4 = all_visitors_GA4[1:]

        while len(all_visitors_GA4) > len(weekly_dates_GA4):
            all_visitors_GA4 = np.delete(all_visitors_GA4, -1)

        # TODO: Filter out internal traffic

        frac_GA4 = all_new_visitors_GA4/all_visitors_GA4
        
        #If the UA files are not backed up, do the backup. This does not work past June 2024.
        if not(os.path.exists('website/analytics/UA_backup/frac_df_UA.txt')):
            metrics = [{'expression': 'ga:newUsers'}]
            dimensions = [{'name': 'ga:yearWeek'}, {'name': 'ga:userType'}]
            all_new_visitors_response = self.get_report(metrics, dimensions)
            all_new_visitors_dict = self.compile_response(all_new_visitors_response)
            internal_new_visitors_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_new_visitors_dict = self.compile_response(internal_new_visitors_response)
            for i in all_new_visitors_dict.keys():
                if i not in internal_new_visitors_dict:
                    internal_new_visitors_dict[i] = 0
            internal_new_visitors_dict = dict(sorted(internal_new_visitors_dict.items()))
            num_new_users = [all_new_visitors_dict[i] - internal_new_visitors_dict[i] for i in all_new_visitors_dict]

            dates1 = [datetime.datetime.strptime(i + '-1', "%Y%W-%w") for i in all_new_visitors_dict]

            metrics = [{'expression': 'ga:sessions'}]
            dimensions = [{'name': 'ga:yearWeek'}]
            all_weekly_visits_response = self.get_report(metrics, dimensions)
            all_weekly_visits_dict = self.compile_response(all_weekly_visits_response)
            internal_weekly_visits_response = self.get_report(metrics, dimensions, self.internal_segment)
            internal_weekly_visits_dict = self.compile_response(internal_weekly_visits_response)

            for i in all_weekly_visits_dict.keys():
                if i not in internal_weekly_visits_dict:
                    internal_weekly_visits_dict[i] = 0
            internal_weekly_visits_dict = dict(sorted(internal_weekly_visits_dict.items()))
            weekly_num_visits = [all_weekly_visits_dict[i] - internal_weekly_visits_dict[i] for i in all_weekly_visits_dict]

            dates2 = [datetime.datetime.strptime(i + '-1', "%Y%W-%w") for i in all_weekly_visits_dict]

            frac = np.array(num_new_users)/np.array(weekly_num_visits)

            for i in range(len(dates2)):
                if dates2[i] == datetime.datetime(2022, 7, 4, 0, 0):
                    frac[i + 1] = np.mean([frac[i], frac[i + 2]])  # accounting for weird spike

            np.savetxt('website/analytics/UA_backup/frac_df_UA.txt', frac)

        #Read the UA dataframes from files
        frac_UA = np.loadtxt('website/analytics/UA_backup/frac_df_UA.txt')

        start = datetime.datetime.strptime("2021-01-25", '%Y-%m-%d')
        end = datetime.datetime.strptime("2023-07-11", '%Y-%m-%d')
        dates2_UA = [start + datetime.timedelta(days=7*x) for x in range(0, ((end-start)//7).days)]
        dates2_UA = np.insert(dates2_UA, 49, dates2_UA[49])
        dates2_UA = np.insert(dates2_UA, 102, dates2_UA[102])

        frac_df = np.append(frac_UA, frac_GA4)
        dates_df = np.append(dates2_UA, weekly_dates_GA4)

        fig, ax = plt.subplots()
        ax.plot_date(dates_df, frac_df, fmt=",-")
        ax.set_xlabel("Date")
        ax.set_ylabel("Fraction of New Users")
        ax.set_title(f"External Fraction of Sessions from New Users, Jan. 19 2021 - Yesterday \n  Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        ax.tick_params(axis='x', labelrotation=-45)

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'weekly_new_user_fraction.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def make_n_tools(self):
        resource_df = self.resources
        resource_df = resource_df.drop_duplicates(subset = ["name"])

        resource_df["creation_date"] = resource_df["creation_date"].dt.date
        resources2 = resource_df.groupby("creation_date").count().reset_index()[["creation_date", "id"]].sort_values("creation_date")
        cumulative_n = [sum(resources2["id"].iloc[:i + 1]) for i in range(len(resources2["id"]))]

        fig, ax = plt.subplots()
        ax.plot_date(resources2["creation_date"], cumulative_n, fmt=",-", linewidth=5)
        ax.set_title(f"Cumulative Number of Tools on EMAC, Total={sum(resources2['id'])} \n  Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        ax.set_xlabel("Date")
        ax.set_ylabel("N")
        ax.tick_params(axis='x', labelrotation=-45)

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'n_tools.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()

    def subs_over_time(self):
        subs_df = self.subscriptions
        subs_df["creation_date"] = subs_df["creation_date"].dt.date

        subs2 = subs_df.groupby("creation_date").count().reset_index()[["creation_date", "id"]].sort_values("creation_date")
        cumulative_n = [sum(subs2["id"].iloc[:i + 1]) for i in range(len(subs2["id"]))]

        fig, ax = plt.subplots()
        ax.plot_date(subs2["creation_date"], cumulative_n, fmt=",-", linewidth=5)
        ax.set_title(f"Cumulative Number of Subscribers to EMAC, Total={sum(subs2['id'])} \n  Generated {datetime.datetime.now().replace(second=0, microsecond=0)}")
        ax.set_xlabel("Date")
        ax.set_ylabel("N")
        ax.tick_params(axis='x', labelrotation=-45)

        filename = os.path.join(ANALYTICS_PLOT_DIR, 'n_subs.png')
        plt.tight_layout()
        fig.savefig(filename)
        plt.close()
