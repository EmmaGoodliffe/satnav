import gpxpy
import gpxpy.gpx  # does this do anything?

with open("stav_to_trin.gpx", "r") as f:
    gpx = gpxpy.parse(f)
    print(gpx.tracks, gpx.waypoints, gpx.routes)
