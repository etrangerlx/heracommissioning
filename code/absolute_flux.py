from ephem import *
import numpy as np
import pylab as plt
import glob, os
import inittasks as it
import plotutilities as plutil
import sys, getopt
import pyfits

#FAINTER SOURCE (MEASURED WITH VIEWER)
PMN_J2101_2802_RA = "21:01:18.3"
PMN_J2101_2802_DEC = "-28:01:55"
PMN_J2101_2802_FLUX_189 = 23.1

#https://ned.ipac.caltech.edu/cgi-bin/objsearch?objname=PMN+J2101-2802&extend=no&hconst=73&omegam=0.27&omegav=0.73&corr_z=1&out_csys=Equatorial&out_equinox=J2000.0&obj_sort=RA+or+Longitude&of=pre_text&zv_breaker=30000.0&list_limit=5&img_stamp=YES


#BRIGHTER SOURCE (MEASURED WITH VIEWER)
PMN_J2107_2526_RA = "21:07:25.3"
PMN_J2107_2526_DEC = "-25:25:40"
PMN_J2107_2526_FLUX_189 = 47.7

#https://ned.ipac.caltech.edu/cgi-bin/objsearch?objname=PMN+J2107-2526&extend=no&hconst=73&omegam=0.27&omegav=0.73&corr_z=1&out_csys=Equatorial&out_equinox=J2000.0&obj_sort=RA+or+Longitude&of=pre_text&zv_breaker=30000.0&list_limit=5&img_stamp=YES


#OTHER OBSERVABLE SOURCE IDENTIFIED AS CENA
CENA_RA = "13:35:58"
CENA_DEC = "-34:04:19"

class absflux():

      def __init__(self):
          pass

      def getFieldCenter(self,direc,fits_file):

          if os.path.isfile(direc+fits_file):
             ff = pyfits.open(direc+fits_file)
             header_v = ff[0].header
             ra_0 = header_v["crval1"]#degrees
             dec_0 = header_v["crval2"]#degrees
             ff.close()
          else:
             ra_0 = np.NaN
             dec_0 = np.NaN
          return ra_0,dec_0

      # converting ra and dec to l and m coordiantes
      def radec2lm(self,direc,fits_file,ra_d,dec_d):
          # ra and dec in degrees
          rad2deg = lambda val: val * 180./np.pi
          deg2rad = lambda val: val * np.pi/180
          ra0,dec0 = self.getFieldCenter(direc,fits_file) # phase centre in degrees
          #print "ra0 = ",ra0
          #print "dec0 = ",dec0
          ra0,dec0 = deg2rad(ra0),deg2rad(dec0)
          ra_r, dec_r = deg2rad(ra_d), deg2rad(dec_d) # coordinates of the sources in radians
          l = np.cos(dec_r)* np.sin(ra_r - ra0)
          m = np.sin(dec_r)*np.cos(dec0) - np.cos(dec_r)*np.sin(dec0)*np.cos(ra_r-ra0)
          return rad2deg(l),rad2deg(m) #lm in degrees

      def convert_PMN_J2101_2802_to_lm(self,direc,fits_file):
          ra_d = (hours(PMN_J2101_2802_RA))*180./np.pi
          dec_d = (degrees(PMN_J2101_2802_DEC))*180./np.pi

          l,m = self.radec2lm(direc,fits_file,ra_d,dec_d)
          return l,m

      def convert_PMN_J2107_2526_to_lm(self,direc,fits_file):
          ra_d = (hours(PMN_J2107_2526_RA))*180./np.pi
          dec_d = (degrees(PMN_J2107_2526_DEC))*180./np.pi

          l,m = self.radec2lm(direc,fits_file,ra_d,dec_d)
          return l,m

      def test_lm_conversion(self,direc,fits_file,l,m):
          if os.path.isfile(direc+fits_file):
             ff = pyfits.open(direc+fits_file)
             header_v = ff[0].header
             cellsize = np.absolute(header_v['cdelt1']) #pixel width in degrees
             #print "cellsize = ",cellsize
             #print "cellsize2 = ",header_v['cdelt2']
             #print "cellsize3 = ",header_v['cdelt1']
             data = ff[0].data
             data = data[0,0,::-1,::-1]
             npix = data.shape[0] #number of pixels in fits file
             cpix = npix/2.0
             max_l = int(cpix*cellsize)
             plt.imshow(data,extent=[-max_l,max_l,-max_l,max_l])
             plt.hold('on')
             plt.plot(l,m,'x',ms = 10.0)
             plt.show()
          else:
             pass

      def flipTrimBox(self,box,npix):
          x = np.arange(npix,dtype=int)
          x_reverse = x[::-1]
          #print "x_reverse = ",x_reverse
          #print "box = ",box
          itemindex1 = np.where(x_reverse==box[0])[0][0]
          itemindex2 = np.where(x_reverse==box[1])[0][0]
          itemindex3 = np.where(x_reverse==box[2])[0][0]
          itemindex4 = np.where(x_reverse==box[3])[0][0]

          #print "itemindex1 = ",itemindex1
          #print "itemindex2 = ",itemindex2
          #print "itemindex3 = ",itemindex3
          #print "itemindex4 = ",itemindex4
          return np.array([itemindex2,itemindex1,itemindex4,itemindex3])

      def obtainTrimBox(self,direc,fits_file,mask,window=2,pix_deg="PIX",plot_selection=False):
          if not (os.path.isfile(direc+fits_file)):
             return np.array([np.NaN,np.NaN,np.NaN,np.NaN]),np.NaN

          ff = pyfits.open(direc+"/"+fits_file)
          header_v = ff[0].header
          cellsize = np.absolute(header_v['cdelt1']) #pixel width in degrees
          data = ff[0].data
          data = data[0,0,::-1,::-1]
          npix = data.shape[0] #number of pixels in fits file

          cpix = npix/2.0

          values = np.zeros((mask.shape[0],3))

          if pix_deg == "PIX":
             w = window
          else:
             w = int(window/cellsize)+1

          for s in xrange(mask.shape[0]):
              l = mask[s,0]
              m = mask[s,1]
              source = True
              pix_x = int(cpix + l/cellsize)
              pix_y = int(cpix - m/cellsize)

              if pix_x < 0 or pix_x > npix:
                 source = False
              if pix_y < 0 or pix_y > npix:
                 source = False

              if source:
                 if pix_x - w < 0:
                    x_1 = 0
                 else:
                    x_1 = pix_x - w
                 if pix_x + w + 1> npix-1:
                    x_2 = npix-1
                 else:
                    x_2 = pix_x + w + 1
                 if pix_y - w < 0:
                    y_1 = 0
                 else:
                    y_1 = pix_y - w
                 if pix_y + w + 1 > npix-1:
                    y_2 = npix-1
                 else:
                    y_2 = pix_y + w + 1

                #print "y_1 = ",y_1
                #print "y_2 = ",y_2

              if plot_selection:
                   data_temp = np.copy(data[y_1:y_2,x_1:x_2])
                   data[y_1:y_2,x_1:x_2] = 0
                   #data_temp = data[0:1000,:]

                   plt.imshow(data_temp)
                   plt.show()
                   plt.imshow(data)
                   plt.show()
              else:
                 x_1 = np.NaN
                 x_2 = np.NaN
                 y_1 = np.NaN
                 y_2 = Np.NaN

          ff.close()
          return np.array([x_1,x_2,y_1,y_2]),npix

if __name__ == "__main__":
   
   ab_object = absflux()
   
   mask = np.zeros((2,2),dtype=float)
   direc = plutil.FIGURE_PATH+"IMAGES/"
   
   x = ["59147","59842","61234", "61930", "62626"]

   for k in xrange(len(x)):
       fits_file = "zen.2457545."+x[k]+".xx.HH.uvcU.fits"    

       print "fits_file = ",fits_file
       print "direc = ",direc
       l,m = ab_object.convert_PMN_J2101_2802_to_lm(direc,fits_file)

       print "l = ",l
       print "m = ",m

       mask[0,0] = l
       mask[0,1] = m

       l,m = ab_object.convert_PMN_J2107_2526_to_lm(direc,fits_file)

       mask[1,0] = l
       mask[1,1] = m

       ab_object.obtainTrimBox(direc,fits_file,mask,window=8,pix_deg="PIX",plot_selection=True) 
