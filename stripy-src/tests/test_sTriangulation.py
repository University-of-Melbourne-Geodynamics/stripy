import numpy as np
import stripy

from scipy import spatial
from time import time

try: range = xrange
except: pass


mesh = stripy.spherical_meshes.octahedral_mesh(include_face_points=True, refinement_levels=3)


def test_area():

    def compute_area(v1, v2, v3):
        """ manually compute area on unit sphere """
        u1 = np.cross(v1, v2)
        u2 = np.cross(v2, v3)
        u3 = np.cross(v3, v1)

        s1 = np.sqrt(u1.dot(u1))
        s2 = np.sqrt(u2.dot(u2))
        s3 = np.sqrt(u3.dot(u3))

        u1 /= s1
        u2 /= s2
        u3 /= s3

        ca1 = -u1.dot(u3)
        ca2 = -u2.dot(u1)
        ca3 = -u3.dot(u2)

        a1 = np.arccos(ca1)
        a2 = np.arccos(ca2)
        a3 = np.arccos(ca3)

        areas = a1 + a2 + a3 - np.arccos(-1.0)
        return areas

    n  = mesh.npoints
    nt = mesh.simplices.shape[0]

    area1 = np.empty(nt)

    t = time()
    for i in range(0,nt):
        tr = mesh.simplices[i]
        xi = mesh.x[tr]
        yi = mesh.y[tr]
        zi = mesh.z[tr]

        area1[i] = compute_area(xi, yi, zi)
    t1 = time() - t
    t = time()
    area2 = mesh.areas()
    t2 = time() - t

    res = ((area1 - area2)**2).max()
    assert res < 1.0e-5

    return


def test_derivative():
    from scipy import interpolate

    def analytic(lons, lats, k1, k2):
        return np.cos(k1*lons) * np.sin(k2*lats)

    def analytic_ddlon(lons, lats, k1, k2):
        return -k1 * np.sin(k1*lons) * np.sin(k2*lats) / np.cos(lats)

    def analytic_ddlat(lons, lats, k1, k2):
        return k2 * np.cos(k1*lons) * np.cos(k2*lats)

    # Create a field to test derivatives
    lons, lats = mesh.lons, mesh.lats + np.pi/2

    Z     = analytic(lons, lats, 5.0, 2.0)
    Zlons = analytic_ddlon(lons, lats, 5.0, 2.0)
    Zlats = analytic_ddlat(lons, lats, 5.0, 2.0)
    gradZ = np.hypot(Zlons, Zlats)

    # Stripy
    t = time()
    Zlons1, Zlats1 = mesh.gradient_lonlat(Z, nit=10, tol=1e-10)
    t1 = time() - t
    gradZ1 = np.hypot(Zlons1, Zlats1)

    # Spline
    spl = interpolate.SmoothSphereBivariateSpline(lats, lons, Z, s=1)
    t = time()
    Zlons2 = spl.ev(lats, lons, dtheta=1)
    Zlats2 = spl.ev(lats, lons, dphi=1)
    t2 = time() - t
    gradZ2 = np.hypot(Zlons2, Zlats2)

    res1 = ((gradZ1 - gradZ)**2).max()
    res2 = ((gradZ2 - gradZ)**2).max()

    return

def test_interpolation():
    from scipy import interpolate

    lons, lats = mesh.lons, mesh.lats
    Z = np.exp(-lons**2 - lats**2)
    lon = 2.*np.pi*np.random.random(10)
    lat = np.arccos(2.*np.random.random(10) - 1.) - np.pi/2

    # Stripy
    zn1 = mesh.interpolate_nearest(lon, lat, Z)
    zl1 = mesh.interpolate_linear(lon, lat, Z)
    zc1 = mesh.interpolate_cubic(lon, lat, Z)

    # cKDTree
    tree = interpolate.NearestNDInterpolator((lons,lats), Z)
    zn2 = tree(lon, lat)

    # Least-squares spline
    tri = interpolate.LinearNDInterpolator((lons,lats), Z)
    zl2 = tri((lon, lat))


    # Cubic spline
    spl = interpolate.SmoothSphereBivariateSpline(lats+np.pi/2, lons, Z, s=1)
    zc2 = spl.ev(lat+np.pi/2,lon)

    print("squared residual in interpolation\n  \
     - nearest neighbour = {}\n  \
     - linear = {}\n  \
     - cubic  = {}".format(((zn1 - zn2)**2).max(), \
                           ((zl1 - zl2)**2).max(), \
                           ((zc1 - zc2)**2).max()))

def test_smoothing():
    pass
