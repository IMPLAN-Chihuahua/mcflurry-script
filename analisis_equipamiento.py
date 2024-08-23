import arcpy
import arcpy.da
import arcpy.management
import time
import json
import os

tbx_path = rf"{os.environ['TOOLBOX_PATH']}"
equipamiento_gdb = rf"{os.environ['EQUIPAMIENTO_GDB']}"
insumos_gdb = rf"{os.environ['INSUMEOS_GDB']}"
tbx = arcpy.AddToolbox(tbx_path)

def get_stat_fields(server_layer):
    geom_type = arcpy.Describe(server_layer).shapeType.lower()
    statistics_fields = []
    if geom_type == "polygon" or geom_type == "multipolygon":
        statistics_fields = [["Shape_Area", "SUM"]]
    if geom_type == "line" or geom_type == "polyline":
        statistics_fields = [["Shape_Length", "SUM"]]
    if geom_type == "point" or geom_type == "multipoint":
        statistics_fields = [["IDPS", "COUNT"]]

    return statistics_fields


def parse_equipamiento(eqp):
    try: 
        feature_layer = eqp.get("feature_layer").encode("latin_1").decode("utf_8")
        case_fields = eqp.get("case_fields")
        stat_fields = eqp.get("stat_fields")
        name = eqp.get("name")
        return (feature_layer, case_fields, stat_fields, name)
    except IndexError as e:
        raise Exception(f"No se recibieron los parametros necesarios: {str(e)}")

 
def get_json_content(path):
    f = open(path)
    content = json.loads(f.read())
    f.close()
    return content


def get_poblacion_buffers(distance, eqp_layer):
    out_single_buffer = fr"in_memory\buffer_{int(time.time())}"
    out_dissolve_buffer = fr"in_memory\disolve_buffer_{int(time.time())}"
    tbx.BufferPoblacion(
            elemento=rf"{equipamiento_gdb}\{eqp_layer}",
            distance=f'{distance} Meters',
            single_buffer=out_single_buffer,
            disolve_buffer=out_dissolve_buffer
    )
    return (out_single_buffer, out_dissolve_buffer)


def analyze_poblacion(buffer, dissolved_buffer, poblacion, eqp_layer):
    feature_layer, case_fields, stat_fields, name = parse_equipamiento(poblacion)
    prefix = rf"{eqp_layer}_{name}"
    input_feature_layer =rf'{insumos_gdb}\{feature_layer}'
    eqp_stat_fields = get_stat_fields(input_feature_layer)
    out_summary_buffer = rf"{arcpy.env.workspace}\{prefix}_summary_single_buffer_{int(time.time())}"
    out_summary_dissolved_buffer = rf"{arcpy.env.workspace}\{prefix}_summary_dissolve_buffer_{int(time.time())}"
    tbx.SummaryIntersect(
        layer=input_feature_layer,
        area_estudio=buffer,
        stat_fields=eqp_stat_fields + stat_fields,
        case_fields=case_fields,
        out_summary=out_summary_buffer
    )
    tbx.SummaryIntersect(
        layer=input_feature_layer,
        area_estudio=dissolved_buffer,
        stat_fields=eqp_stat_fields + stat_fields,
        case_fields=case_fields,
        out_summary=out_summary_dissolved_buffer
    )


def get_infraestructura_buffer(eqp_layer):
    out_buffer = rf"in_memory\buffer_{int(time.time())}"
    tbx.BufferInfraestructura(
        elemento=rf"{equipamiento_gdb}\{eqp_layer}",
        out_buffer=out_buffer
    )
    return out_buffer


def analyze_infraestructura(infraestructura, area_estudio, eqp_layer):
    feature_layer, case_fields, stat_fields, name = parse_equipamiento(infraestructura)
    input_feature_layer =fr'{insumos_gdb}\{feature_layer}'
    prefix = fr"{eqp_layer}_infraestructura_{name}_{int(time.time())}"
    eqp_stat_fields = get_stat_fields(input_feature_layer)
    out_summary = rf"{arcpy.env.workspace}\{prefix}_summary_buffer"
    tbx.SummaryIntersect(
        layer=input_feature_layer,
        area_estudio=area_estudio,
        stat_fields=eqp_stat_fields + stat_fields,
        case_fields=case_fields + ['IDPS'],
        out_summary=out_summary
    )
    

def analyze(equipamiento_group):
    gdb_name = rf"{equipamiento_group}_{int(time.time())}.gdb"
    workspace_folder = rf"{os.environ['WORKSPACE']}"
    analisis_gdb = os.path.join(workspace_folder, gdb_name)
    arcpy.management.CreateFileGDB(workspace_folder, gdb_name)
    
    arcpy.env.overwriteOutput = True
    arcpy.env.transferDomains = True
    arcpy.env.workspace = analisis_gdb
    
    equipamientos = get_json_content(rf'.\equipamiento_urbano\{equipamiento_group}.json')
    poblacion = get_json_content(r'.\poblacion.json')
    infraestructuras = get_json_content( r'.\infraestructura.json')
    
    for equipamiento in equipamientos:
        eqp_layer = equipamiento.get('feature_layer')
        radio_servicio = equipamiento.get('radio_servicio')
        (buffer, dissolved_buffer) = get_poblacion_buffers(radio_servicio, eqp_layer)
        analyze_poblacion(buffer, dissolved_buffer, poblacion, eqp_layer)
        
        area_estudio = get_infraestructura_buffer(eqp_layer)
        for item in infraestructuras:
            analyze_infraestructura(item, area_estudio, eqp_layer)
