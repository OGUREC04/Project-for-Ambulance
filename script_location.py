import geopandas as gpd
import os
import time
from selenium import webdriver
import geopandas
import osmnx as ox
import folium
import io
# import imgkit
from PIL import Image

# prov_shp=geopandas.read_file(fichier_dist )
# prov_shp.set_crs(epsg=4326, inplace=True)
lon = (55.147047, 61.366533)#
end_latlng = (55.147188, 61.382787)#
location_point = (55.147047, 61.366533)# НЕ ДЕЛАТЬ НАОБОРОТ ТОЧКИ55.155149, 61.394063
print(type(lon), lon)

place = "Chelyabinsk, Russia"
tooltip = "Click me!"
G = ox.graph_from_point(location_point, dist=1000, network_type="walk", simplify=True )
orig_node = ox.distance.nearest_nodes(G, lon[1],lon[0]) # тут мы зачем то переворачиваем координаты, осбо не заебываемся еад этим
dest_nodes = ox.distance.nearest_nodes(G, end_latlng[1], end_latlng[0])# тут мы зачем то переворачиваем координаты, осбо не заебываемся еад этим
route = ox.shortest_path(G, orig_node, dest_nodes)
map = ox.plot_route_folium(G, route, tiles='openstreetmap')
second_marker = (G.nodes[route[-1]]['y'], G.nodes[route[-1]]['x']) # беру из списка узлов кротчайшего пути последнюю точку и узнаю ее координаты, чтобы поставить маркер без погрещности
first_marker = (G.nodes[route[0]]['y'], G.nodes[route[0]]['x'])# беру из списка узлов кротчайшего пути первую точку и узнаю ее координаты, чтобы поставить маркер без погрещности
folium.Marker([first_marker[0],first_marker[1]], popup="<i>Mt. Hood Meadows</i>", tooltip=tooltip).add_to(map) # добавление маркера на карту
folium.Marker([second_marker[0], second_marker[1]], popup="<i>Mt. Hood Meadows</i>", tooltip=tooltip).add_to(map)
# img_data = map.to_png(5)
# img = Image.open(io.BytesIO(img_data))
# img.save('mappp.png')

# delay=5
# fn='mapp.html'
# tmpurl='file://{path}/{mapfile}'.format(path=os.getcwd(),mapfile=fn)
# map.save(fn)
#
# browser = webdriver.Firefox()
# browser.get(tmpurl)
# #Give the map tiles some time to load
# time.sleep(delay)
# browser.save_screenshot('fffffffffff.png')
# browser.quit()

img_data = map._to_png(5)
img = Image.open(io.BytesIO(img_data))
img.save('1.png')
# 1533304329:AAHVhvmtXETWT4eDJrjzmbMn7Ac1XScSbwM