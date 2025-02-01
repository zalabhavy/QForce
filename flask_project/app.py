from flask import Flask, request, send_file, render_template
import pandas as pd
import networkx as nx
import folium
from geopy.distance import geodesic
import os

app = Flask(__name__)

# Load Data
file_path = "SmartRoute Optimizer.xlsx"

def process_trips():
    # Read Excel Sheets
    shipment_data = pd.read_excel(file_path, sheet_name="Shipments_Data")
    vehicle_data = pd.read_excel(file_path, sheet_name="Vehicle_Information")
    store_location = pd.read_excel(file_path, sheet_name="Store Location")

    # Extract store location
    store_lat, store_lon = store_location.iloc[0]['Latitute'], store_location.iloc[0]['Longitude']

    def calculate_distance(loc1, loc2):
        return geodesic(loc1, loc2).km

    # Create MST (Minimum Spanning Tree)
    def create_mst(shipment_points):
        G = nx.Graph()
        points = [(store_lat, store_lon)] + shipment_points
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = calculate_distance(points[i], points[j])
                G.add_edge(i, j, weight=dist)
        return nx.minimum_spanning_tree(G, weight='weight')

    # Handle "Any" in Vehicle Data
    vehicle_data['Shipments_Capacity'] = pd.to_numeric(vehicle_data['Shipments_Capacity'].replace("Any", float('inf')))
    vehicle_data['Max Trip Radius (in KM)'] = pd.to_numeric(vehicle_data['Max Trip Radius (in KM)'].replace("Any", float('inf')))
    vehicle_data['Number'] = pd.to_numeric(vehicle_data['Number'].replace("Any", float('inf')))

    # Define Vehicle Priority Order
    vehicle_priority = ["3W", "4W-EV", "4W"]
    vehicle_data = vehicle_data.set_index("Vehicle Type").loc[vehicle_priority].reset_index()
    vehicle_availability = vehicle_data.set_index("Vehicle Type")['Number'].to_dict()

    trips = []
    available_shipments = shipment_data.copy()

    while not available_shipments.empty:
        for vehicle_type in vehicle_priority:
            if vehicle_availability[vehicle_type] <= 0:
                continue

            vehicle = vehicle_data[vehicle_data['Vehicle Type'] == vehicle_type].iloc[0]
            max_capacity = vehicle['Shipments_Capacity']
            max_distance = vehicle['Max Trip Radius (in KM)']
            
            selected_shipments = []
            total_capacity = 0
            shipment_points = []

            for _, shipment in available_shipments.iterrows():
                shipment_distance = calculate_distance((store_lat, store_lon), (shipment['Latitude'], shipment['Longitude']))
                if total_capacity + 1 <= max_capacity:
                    total_capacity += 1
                    shipment_points.append((shipment['Latitude'], shipment['Longitude']))
                    selected_shipments.append((shipment['Shipment ID'], round(shipment_distance, 2), shipment['Delivery Timeslot']))
                if total_capacity >= max_capacity * 0.5:
                    break

            if selected_shipments:
                mst = create_mst(shipment_points)
                mst_distance = sum(nx.get_edge_attributes(mst, 'weight').values())
                trip_time = (mst_distance * 5) + (len(selected_shipments) * 10)

                if mst_distance <= max_distance:
                    trips.append({
                        'Trip_ID': len(trips) + 1,
                        'Shipments': [s[0] for s in selected_shipments],
                        'Vehicle_Type': vehicle_type,
                        'MST_Distance': round(mst_distance, 2),
                        'Trip_Time': round(trip_time, 2),
                        'Capacity_Utilization': round((total_capacity / max_capacity) * 100, 2) if max_capacity != float('inf') else "N/A",
                    })
                    available_shipments = available_shipments[~available_shipments['Shipment ID'].isin([s[0] for s in selected_shipments])]
                    vehicle_availability[vehicle_type] -= 1

    trips_df = pd.DataFrame(trips)
    trips_df.to_excel("Trip_Output.xlsx", index=False)
    return trips_df

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_excel")
def generate_excel():
    process_trips()
    return send_file("Trip_Output.xlsx", as_attachment=True)

@app.route("/visualize_trips")
def visualize_trips():
    shipment_data = pd.read_excel(file_path, sheet_name="Shipments_Data")
    store_location = pd.read_excel(file_path, sheet_name="Store Location")
    store_lat, store_lon = store_location.iloc[0]['Latitute'], store_location.iloc[0]['Longitude']

    trips_df = pd.read_excel("Trip_Output.xlsx")
    map_center = [store_lat, store_lon]
    trip_map = folium.Map(location=map_center, zoom_start=12)

    folium.Marker(location=map_center, popup="Store", icon=folium.Icon(color='red')).add_to(trip_map)
    color_map = {"3W": "green", "4W-EV": "orange", "4W": "blue"}

    for _, trip in trips_df.iterrows():
        vehicle_color = color_map.get(trip['Vehicle_Type'], 'blue')
        points = [(store_lat, store_lon)]

        for shipment_id in str(trip['Shipments']).split(", "):
            shipment_id = str(shipment_id).strip("[]")  
            shipment_id = int(shipment_id) 
            shipment = shipment_data[shipment_data['Shipment ID'] == shipment_id].iloc[0]
            points.append((shipment['Latitude'], shipment['Longitude']))
            folium.Marker(
                location=(shipment['Latitude'], shipment['Longitude']),
                popup=f"Shipment {shipment_id}",
                icon=folium.Icon(color=vehicle_color)
            ).add_to(trip_map)

        points.append((store_lat, store_lon))
        folium.PolyLine(points, color=vehicle_color, weight=2.5, opacity=1).add_to(trip_map)

    trip_map.save("templates/trip_visualization.html")
    return render_template("trip_visualization.html")

if __name__ == "__main__":
    app.run(debug=True)
