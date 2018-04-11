import logging

from flask import Flask, request
import requests
import matplotlib
matplotlib.use('agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import skfmm
import math
import io

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello! Wdy 290 Hw5, please provide data and n!'

@app.route('/query')
def query():
    mydate = request.args.get('date')
    n = request.args.get('n')
    mystr = "https://ce290-hw5-weather-report.appspot.com/?date=" + mydate
    res = requests.get(mystr)
    myres = res.json()
    Cx = myres['centroid_x']
    Cy = myres['centroid_y']
    R = myres['radius']
    L=20
    step = L/float(n)
    X, Y = np.meshgrid(np.linspace(0,L,n+1), np.linspace(0,L,n+1))
    phi, mask = np.ones_like(X), np.zeros_like(X)
    phi[0,0] = 0
    for i in range(n+1):
        for j in range(n+1):
            if (X[i,j]-Cx)**2+(Y[i,j]-Cy)**2<=R**2:
                mask[i,j] = 1
    phi = np.ma.MaskedArray(phi,mask)
    dis1= skfmm.distance(phi, dx=step)
    phi[0,0] = 1
    phi[n,n] = 0
    dis2= skfmm.distance(phi, dx=step)
    dis = dis1 + dis2
    
    def path_find(dis,st,ed,step):
        curx, cury = st, st
        px, py = [], []
        while curx<ed and cury<ed:
            px.append(curx*step)
            py.append(cury*step)
            mydis = list((dis[curx+1,cury],dis[curx,cury+1],dis[curx+1,cury+1]))
            mydir = list(((1,0),(0,1),(1,1)))
            myidx = mydis.index(min(mydis))
            curx = curx + mydir[myidx][0]
            cury = cury + mydir[myidx][1]
            #print(curx,cury)
        while curx<ed:
            px.append(curx*step)
            py.append(cury*step)
            curx = curx + 1
        while cury<ed:
            px.append(curx*step)
            py.append(cury*step)
            cury = cury + 1
        return px, py

    print(dis1[n,n])
    px,py = path_find(dis,0,n,step)
    fig = Figure()
    axis=fig.add_subplot(1,1,1)
    axis.pcolor(X,Y,phi)
    axis.plot(px,py)
    axis('equal')
    canvas=FigureCanvas(fig)
    output=io.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END app]
