from rest_framework.views import APIView
from rest_framework.response import Response
from issue_template_metric.models import IssueTemplates
from issue_template_metric.serializers import IssueTemplatesSerializer
from datetime import date
import requests


class IssueTemplatesView(APIView):

    def get(self, request, owner, repo):
        issue_templates = IssueTemplates.objects.all().filter(
            owner=owner,
            repo=repo
        )
        
        if(not issue_templates):

            url1 = 'https://api.github.com/repos/'
            url2 = '/contents/.github/ISSUE_TEMPLATE'
            result = url1 + owner + '/' + repo + url2
            github_request = requests.get(result)
            if(github_request.status_code == 200):
                IssueTemplates.objects.create(
                    owner=owner,
                    repo=repo,
                    issue_templates=True,
                    date=date.today()
                )
            else:
                IssueTemplates.objects.create(
                    owner=owner,
                    repo=repo,
                    issue_templates=False,
                    date=date.today()
                )

        issue_templates = IssueTemplates.objects.all().filter(
            owner=owner,
            repo=repo
        )
        issue_serialized = IssueTemplatesSerializer(issue_templates, many=True)
        return Response(issue_serialized.data[0])
