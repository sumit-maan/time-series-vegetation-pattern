import errno

from osgeo import gdal
import os


def raster_to_array(raster_file, data_type):
    ds = gdal.Open(raster_file)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()
    arr = arr.astype(data_type)
    return arr


def merge_clip_raster(raster_file_list, output_file=None, shp_file=None, bbox=None, out_width=None, out_height=None):
    ds_lst = list()
    for raster in raster_file_list:
        ds = gdal.Warp('', raster, format='vrt', dstNodata=0,
                       dstSRS="+proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0",
                       cutlineDSName=shp_file, cropToCutline=True, width=out_width, height=out_height)
        ds_lst.append(ds)
    del ds
    if shp_file:
        ds = gdal.BuildVRT('', ds_lst, VRTNodata=0, srcNodata=0)
        gdal.Warp(output_file, ds, format='GTiff', dstNodata=0,
                  dstSRS="+proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0",
                  cutlineDSName=shp_file, cropToCutline=True, width=out_width, height=out_height)
    else:
        ds = gdal.BuildVRT('', ds_lst, VRTNodata=0, srcNodata=0)
        gdal.Warp(output_file, ds, format='GTiff', dstNodata=0,
                  dstSRS="+proj=longlat +datum=WGS84 +no_defs +ellps=WGS84 +towgs84=0,0,0",
                  outputBounds=tuple(bbox), cropToCutline=True, width=out_width, height=out_height)
    return output_file


def write_raster(ref_raster, array, dst_filename, gdal_GDT_datatype):
    driver = gdal.GetDriverByName('GTiff')
    cols = array.shape[1]
    rows = array.shape[0]
    out_ds = driver.Create(dst_filename, cols, rows, 1, gdal_GDT_datatype)
    out_ds.GetRasterBand(1).WriteArray(array)

    # adding GeoTransform and Projection
    data0 = gdal.Open(ref_raster)
    geo_trans = data0.GetGeoTransform()
    proj = data0.GetProjection()
    del data0
    out_ds.SetGeoTransform(geo_trans)
    out_ds.SetProjection(proj)
    out_ds.FlushCache()
    del out_ds
    return dst_filename


def raster_shape(raster_file_path):
    ds = gdal.Open(raster_file_path)
    height = ds.RasterXSize
    width = ds.RasterYSize
    return height, width


def raster_sampling(bands_raster_list, raster2, shapefile):
    raster_path = 'data/temp'
    try:
        os.makedirs(raster_path)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        pass
    output_file1 = f'{raster_path}/raster1.tif'
    output_file2 = f'{raster_path}/raster2.tif'
    merge_clip_raster(bands_raster_list, output_file=output_file1, shp_file=shapefile, bbox=None,
                      out_width=None, out_height=None)
    merge_clip_raster([raster2], output_file=output_file2, shp_file=shapefile, bbox=None,
                      out_width=None, out_height=None)
    h1, w1 = raster_shape(output_file1)
    h2, w2 = raster_shape(output_file2)
    h = min(h1, h2)
    w = min(w1, w2)
    agrimask_file = f'{raster_path}/agrimask.tif'
    merge_clip_raster(raster_file_list=[output_file2], output_file=agrimask_file,shp_file=shapefile,
                      out_width=w, out_height=h)
    return h, w
