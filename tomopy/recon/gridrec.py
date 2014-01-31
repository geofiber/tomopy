# -*- coding: utf-8 -*-
import numpy as np
import ctypes
import os
import time
from tomopy.dataio.reader import Dataset

libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib/libgridrec.so'))
libgridrec = ctypes.CDLL(libpath)

class GridrecCStruct(ctypes.Structure):
    """
    The input structure for the C extension library.
    """
    _fields_ = [("numPixels", ctypes.c_int),
                ("numProjections", ctypes.c_int),
                ("numSlices", ctypes.c_int),
                ("sinoScale", ctypes.c_float),
                ("reconScale", ctypes.c_float),
                ("paddedSinogramWidth", ctypes.c_int),
                ("airPixels", ctypes.c_int),
                ("ringWidth", ctypes.c_int),
                ("fluorescence", ctypes.c_int),
                ("reconMethod", ctypes.c_int),
                ("reconMethodTomoRecon", ctypes.c_int),
                ("reconMethodGridrec", ctypes.c_int),
                ("reconMethodBackproject", ctypes.c_int),
                ("numThreads", ctypes.c_int),
                ("slicesPerChunk", ctypes.c_int),
                ("debug", ctypes.c_int),
                ("debugFileName", ctypes.c_byte*256),
                ("geom", ctypes.c_int),
                ("pswfParam", ctypes.c_float),
                ("sampl", ctypes.c_float),
                ("MaxPixSiz", ctypes.c_float),
                ("ROI", ctypes.c_float),
                ("X0", ctypes.c_float),
                ("Y0", ctypes.c_float),
                ("ltbl", ctypes.c_int),
                ("fname", ctypes.c_byte*16),
                ("BP_Method", ctypes.c_int),
                ("BP_MethodRiemann", ctypes.c_int),
                ("BP_MethodRadon", ctypes.c_int),
                ("BP_filterName", ctypes.c_byte*16),
                ("BP_filterSize", ctypes.c_int),
                ("RiemannInterpolation", ctypes.c_int),
                ("RiemannInterpolationNone", ctypes.c_int),
                ("RiemannInterpolationBilinear", ctypes.c_int),
                ("RiemannInterpolationCubic", ctypes.c_int),
                ("RadonInterpolation", ctypes.c_int),
                ("RadonInterpolationNone", ctypes.c_int),
                ("RadonInterpolationLinear", ctypes.c_int)]

def gridrec(TomoObj,
            slice_no=None,
            sinoScale=1e4,
            reconScale=1,
            paddedSinogramWidth=None,
            airPixels=10,
            ringWidth=9,
            fluorescence=0,
            reconMethod=0,
            reconMethodTomoRecon=0,
            numThreads=24,
            slicesPerChunk=32,
            debugFileName='',
            debug=0,
            geom=0,
            pswfParam=6,
            sampl=1,
            MaxPixSiz=1,
            ROI=1,
            X0=0,
            Y0=0,
            ltbl=512,
            fname='shepp',
            BP_Method=0,
            BP_filterName='shepp',
            BP_filterSize=100,
            RiemannInterpolation=0,
            RadonInterpolation=0):
    """
    Performs tomographic reconstruction using the TomoObj object.
    
    Gridrec uses the anonymous "gridrec" algorithm (there are
    rumors that it was written by written by Bob Marr and Graham
    Campbell at BNL in 1997). The basic algorithm is based on FFTs
    and interpolations.
    
    TODO: Make checks outside.
    
    Parameters
    ----------
    TomoObj : tomopy data object
        Tomopy data object generated by the Dataset() class.
    
    slice_no : int, optional
        If specified reconstructs only the slice defined by ``slice_no``.
    
    Returns
    -------
    out : ndarray
        Assigns reconstructed values in TomoRecon object as ``recon``.
        """
    
    # Initialization parameters.
    TomoObj.recon = GridrecCStruct()
    TomoObj.recon.numProjections = TomoObj.data.shape[0]
    TomoObj.recon.numSlices = TomoObj.data.shape[1]
    TomoObj.recon.numPixels = TomoObj.data.shape[2]
    TomoObj.recon.sinoScale = sinoScale
    TomoObj.recon.reconScale = reconScale
    if paddedSinogramWidth is None:
        paddedSinogramWidth = 0
        powerN = 1
        while (paddedSinogramWidth < TomoObj.data.shape[2]):
            paddedSinogramWidth = 2 ** powerN
            powerN += 1
    elif paddedSinogramWidth < TomoObj.data.shape[2]:
        raise ValueError('paddedSinogramWidth must be higher than the number of pixels.')
    TomoObj.recon.paddedSinogramWidth = paddedSinogramWidth
    TomoObj.recon.airPixels = airPixels
    TomoObj.recon.ringWidth = ringWidth
    TomoObj.recon.fluorescence = fluorescence
    TomoObj.recon.reconMethod = reconMethod
    TomoObj.recon.reconMethodTomoRecon = 0
    TomoObj.recon.reconMethodGridrec = 1
    TomoObj.recon.reconMethodBackproject = 2
    TomoObj.recon.numThreads = numThreads
    TomoObj.recon.slicesPerChunk = slicesPerChunk
    TomoObj.recon.debug = 0
    for m in range(len(map(ord, debugFileName))):
        TomoObj.recon.debugFileName[m] = map(ord, debugFileName)[m]
    TomoObj.recon.geom = geom
    TomoObj.recon.pswfParam = pswfParam
    TomoObj.recon.sampl = sampl
    TomoObj.recon.MaxPixSiz = MaxPixSiz
    TomoObj.recon.ROI = ROI
    TomoObj.recon.X0 = X0
    TomoObj.recon.Y0 = Y0
    TomoObj.recon.ltbl = ltbl
    for m in range(len(map(ord, fname))):
        TomoObj.recon.fname[m] = map(ord, fname)[m]
    TomoObj.recon.BP_Method = BP_Method
    TomoObj.recon.BP_MethodRiemann = 0
    TomoObj.recon.BP_MethodRadon = 1
    for m in range(len(map(ord, BP_filterName))):
        TomoObj.recon.BP_filterName[m] = map(ord, BP_filterName)[m]
    TomoObj.recon.BP_filterSize = BP_filterSize
    TomoObj.recon.RiemannInterpolation = RiemannInterpolation
    TomoObj.recon.RiemannInterpolationNone = 0
    TomoObj.recon.RiemannInterpolationBilinear = 1
    TomoObj.recon.RiemannInterpolationCubic = 2
    TomoObj.recon.RadonInterpolation = RadonInterpolation
    TomoObj.recon.RadonInterpolationNone = 0
    TomoObj.recon.RadonInterpolationLinear = 1
    
    # Assume 180 degrees rotation if theta is absent.
    if TomoObj.theta is None:
        theta = (np.linspace(0, TomoObj.recon.numProjections,
                             TomoObj.recon.numProjections)
                 * 180 / TomoObj.recon.numProjections).astype('float32')
    
    # Assign slice_no.
    num_slices = TomoObj.recon.numSlices
    if slice_no is not None:
        num_slices = 1
    
    # Construct the reconstruction object.
    libgridrec.reconCreate(ctypes.byref(TomoObj.recon),
                           theta.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
                           
    # Assume mid point as the rotation axis if center is absent.
    if TomoObj.center is None:
       center = np.ones(num_slices, dtype='float32') * TomoObj.recon.numPixels/2
    else:
       center = np.array(TomoObj.center, dtype='float32')
       if center.size is 1:
           center = np.ones(num_slices, dtype='float32') * center
       elif center.size is num_slices:
           center = np.array(center, dtype='float32')

    # Prepare input variables by converting them to C-types.
    _num_slices = ctypes.c_int(num_slices)
    datain = np.array(TomoObj.data[:, slice_no, :], dtype='float32')
    TomoObj.data = np.empty((num_slices,
                            TomoObj.recon.numPixels,
                            TomoObj.recon.numPixels), dtype='float32')

    # Go, go, go.
    libgridrec.reconRun(ctypes.byref(_num_slices),
                        center.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                        datain.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                        TomoObj.data.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
    
    # Relax and wait while the reconstruction is running.
    while True:
        recon_complete, slices_remaining = poll()
        if recon_complete.value is 1:
            break
        else:
            time.sleep(0.1)

    # Destruct the reconstruction object used by the wrapper.
    libgridrec.reconDelete()

def poll():
    """ 
    Read the reconstruction status and the number of slices remaining.
    
    Returns
    -------
    recon_complete: scalar
        1 if the reconstruction is complete,
        0 if it is not yet complete.
    
    slices_remaining : scalar
        slices_remaining is the number of slices
        remaining to be reconstructed.
        """
    # Get the shared library
    recon_complete = ctypes.c_int(0)
    slices_remaining = ctypes.c_int(0)
    libgridrec.reconPoll(ctypes.byref(recon_complete),
                         ctypes.byref(slices_remaining))
    return recon_complete, slices_remaining

setattr(Dataset, 'gridrec', gridrec)

    
    
    