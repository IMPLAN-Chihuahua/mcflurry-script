import arcpy
import arcpy.da
import arcpy.management
import sys
import time
import timeit
import json

tbx_path = r"O:\Miguel Valdez\UsosDeSuelo\CrazyPollo.atbx"

def get_stats_fields(server_layer):
    geom_type = arcpy.Describe(server_layer).shapeType.lower()
    statistics_fields = []
    if geom_type == "polygon" or geom_type == "multipolygon":
        statistics_fields = [["Shape_Area", "SUM"]]
    if geom_type == "line" or geom_type == "polyline":
        statistics_fields = [["Shape_Length", "SUM"]]
    if geom_type == "point" or geom_type == "multipoint":
        statistics_fields = [["OID", "COUNT"]]

    return statistics_fields

def parse_params(equipamiento):
    try: 
        feature_layer = equipamiento.get("feature_layer").encode("latin_1").decode("utf_8")
        case_fields = equipamiento.get("case_fields")
        stat_fields = equipamiento.get("stat_fields")
        return (feature_layer, case_fields, stat_fields)
    except IndexError as e:
        raise Exception(f"No se recibieron los parametros necesarios: {str(e)}")

def prepare_area_estudio(geom, radio):
    epsg6368 = arcpy.SpatialReference(6368)
    shp = arcpy.CopyFeatures_management(
        geom, rf"{arcpy.env.workspace}\geom_{int(time.time())}"
    )
    arcpy.DefineProjection_management(shp, epsg6368)
    shp = arcpy.analysis.Buffer(
        in_features=shp,
        out_feature_class=rf"{arcpy.env.workspace}\buffer_{int(time.time())}",
        buffer_distance_or_field=f'{radio} Meters',
        method="GEODESIC",
    )
    return shp

start = timeit.default_timer()
gdb_name = f"mcflurry_{int(time.time())}.gdb"
workspace_folder = r"C:/mcflurry/"
analisis_gdb = f"{workspace_folder}{gdb_name}"
arcpy.management.CreateFileGDB(workspace_folder, gdb_name)
arcpy.env.workspace = analisis_gdb
arcpy.env.overwriteOutput = True
arcpy.env.transferDomains = True


equipamientos = r'./equipamineto_urbano/a_comercio_y_servicios.json'
f_eqp = open(equipamientos)
equipamientos = json.loads(f_eqp.read())
f_eqp.close()

analysis_features = r'./toAnalyze.json'
f_analysis = open(analysis_features)
analysis_features = json.loads(f_analysis.read())
f_analysis.close()

tbx = arcpy.AddToolbox(tbx_path)
# TODO: case_fields.append('BUFF_DIST')

for equipamiento in equipamientos:
    eqp_layer = equipamiento.get('feature_layer')
    buffer_distance = equipamiento.get('buffer_distance')
    for item in analysis_features:
        feature_layer, case_fields, stat_fields = parse_params(item)
        eqp_stat_fields = get_stats_fields(feature_layer)
        # call model that merges prepare area and summary intersect
        # res = tbx.IntersectAnalisis(
        #     Capa_server=feature_layer,
        #     Geojson=area_estudio,
        #     Case_Field=case_fields,
        #     Statistics_Fields=eqp_stat_fields.extend(stat_fields),
        # )
        pass
    pass

stop = timeit.default_timer()

print("Time: ", stop - start)

