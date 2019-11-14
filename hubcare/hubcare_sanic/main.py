#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

from indicators import active_indicator
from indicators import welcoming_indicator
from indicators import support_indicator
from services import issue_metric
from services import community_metric
from services import commit_metric
from services import pull_request_metric
from constants import URL_REPOSITORY, TOTAL_WEEKS
import requests

import os

import json

from datetime import datetime, timezone

from sanic import Sanic
from sanic.response import json as sanic_json
import asyncio

app = Sanic()

'''
This is the main class view of the project, it gets data from a repo
Input: owner, repo, token_auth
Output: indicators
'''
@app.route("/hubcare_indicators/<owner:string>/<repo:string>/<token_auth:string>/", methods=["GET"])
async def get_indicators(request, owner, repo, token_auth):
    '''
    Getting data from a repo and indicate parameters
    Input: owner, repo, token_auth
    Output: indicators
    '''
    # username = os.environ['NAME']
    # token = os.environ['TOKEN']

    repo_request = requests.get(
        URL_REPOSITORY + owner + '/' + repo + '/' + token_auth + '/').json()
    response = []
    metrics = {}

    print('-------------------')
    print(repo_request['status'])
    print('-------------------')

    if repo_request['status'] == 0:
        return sanic_json([response])
    elif repo_request['status'] == 1:
        print('###########INITIAL TIME POST############')
        now = datetime.now()
        print(now)
        print('###################################')

        metrics = await get_metric(owner, repo, token_auth, 'post')
        hubcare_indicators = get_hubcare_indicators(owner, repo,
                                                    token_auth, metrics)
        response = create_response(
            metrics,
            hubcare_indicators,
            get_commit_graph(metrics),
            get_pull_request_graph(metrics)
        )

        repo_request = requests.post(
            URL_REPOSITORY + owner + '/' + repo + '/' + token_auth + '/'
        )

        print('############FINAL TIME#############')
        after = datetime.now()
        print(after)
        print('TOTAL = ', (after-now))
        print('###################################')
        return sanic_json([response])
    elif repo_request['status'] == 2:
        print('###########INITIAL TIME PUT############')
        now = datetime.now()
        print(now)
        print('#######################################')

        metrics = await get_metric(owner, repo, token_auth, 'put')
        hubcare_indicators = get_hubcare_indicators(owner, repo,
                                                    token_auth, metrics)
        response = create_response(
            metrics,
            hubcare_indicators,
            get_commit_graph(metrics),
            get_pull_request_graph(metrics)
        )

        repo_request = requests.put(
            URL_REPOSITORY + owner + '/' + repo + '/' + token_auth + '/'
        )

        print('############FINAL TIME#############')
        after = datetime.now()
        print(after)
        print('TOTAL = ', (after-now))
        print('###################################')
    elif repo_request['status'] == 3:
        print('###########INITIAL TIME GET############')
        now = datetime.now()
        print(now)
        print('###################################')

        metrics = await get_metric(owner, repo, token_auth, 'get')
        hubcare_indicators = get_hubcare_indicators(owner, repo,
                                                    token_auth, metrics)

        response = create_response(
            metrics,
            hubcare_indicators,
            get_commit_graph(metrics),
            get_pull_request_graph(metrics)
        )

        print('############FINAL TIME#############')
        after = datetime.now()
        print(after)
        print('TOTAL = ', (after-now))
        print('###################################')

    return sanic_json([metrics])


def create_response(metrics, indicators, commit_graph, pull_request_graph):
    graphs = {
        'commit_graph': commit_graph,
        'pull_request_graph': pull_request_graph
    }

    response = metrics
    response.update(indicators)
    response.update(graphs)
    return response


async def get_metric(owner, repo, token_auth, request_type):

    metrics_types = [issue_metric, community_metric, commit_metric,
                     pull_request_metric]

    tasks = []
    for metric in metrics_types:
        tasks.append(asyncio.create_task(metric.get_metric(
            owner, repo, token_auth, request_type)))

    metrics = {}

    res = await asyncio.gather(*tasks)
    for metric in res:
        metrics.update(metric)

    return metrics


def get_hubcare_indicators(owner, repo, token_auth, metrics):
    active_data = active_indicator.get_active_indicator(owner, repo,
                                                        metrics)
    welcoming_data = welcoming_indicator.get_welcoming_indicator(
        owner,
        repo,
        metrics
    )
    support_data = support_indicator.get_support_indicator(owner, repo,
                                                           metrics)
    hubcare_indicators = {
        'active_indicator': float(
            '{0:.2f}'.format(active_data*100)),
        'welcoming_indicator': float(
            '{0:.2f}'.format(welcoming_data*100)),
        'support_indicator': float(
            '{0:.2f}'.format(support_data*100)),
    }

    hubcare_indicators = {
        'indicators': hubcare_indicators
    }

    return hubcare_indicators


def get_pull_request_graph(metrics):
    metrics = metrics['pull_request_metric']
    categories = metrics['categories']
    x_axis = [
        'merged_yes',
        'merged_no',
        'open_yes_new',
        'closed_yes',
        'open_yes_old',
        'closed_no',
        'open_no_old'
    ]
    y_axis = []
    for i in x_axis:
        y_axis.append(categories[i])

    pull_request_graph_axis = {
        'x_axis': x_axis,
        'y_axis': y_axis
    }
    return pull_request_graph_axis


def get_commit_graph(metrics):
    metrics = metrics['commit_metric']
    commits_week = metrics['commits_week']
    commits_week = json.loads(commits_week)
    WEEKS = len(commits_week)
    if WEEKS == 0:
        x_axis = [str(TOTAL_WEEKS-i) + ' weeks ago'
                  for i in range(TOTAL_WEEKS-1)]
        x_axis.append('this week')
        y_axis = [0] * TOTAL_WEEKS
    else:
        x_axis = []
        y_axis = []

    for i in range(WEEKS-1):
        x_axis.append(str(WEEKS-i) + ' weeks ago')
        y_axis.append(commits_week[i])

    if WEEKS > 0:
        x_axis.append('this week')
        y_axis.append(commits_week[-1])
    commit_graph_axis = {
        'x_axis': x_axis,
        'y_axis': y_axis
    }
    return commit_graph_axis


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8010)
