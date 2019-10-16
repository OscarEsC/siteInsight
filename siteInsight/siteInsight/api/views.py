from django.shortcuts import render
from django.http import HttpResponse
#from django.template import loader
from django.shortcuts import render_to_response

# Create your views here.
def index(request):
    #template = loader.get_template("siteInsight/api/index.html")
    #return HttpResponse(template.render())
    return render_to_response('index.html')
