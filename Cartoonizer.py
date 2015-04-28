import cv2
import scipy
from scipy import signal
import pylab
import math
import numpy as np
from dynamicThreshold import OtsuThresholdMethod


class CannyEdgeDetect:

    def _apply_filter(self, im, y, x):
        y = np.reshape(y, (3,3))
        x = np.reshape(x, (3,3))
        Gy = scipy.signal.convolve(im, y)
        Gx = scipy.signal.convolve(im, x)
        return Gy, Gx
    
    def scharr_filter(self, im):
        # this filter was really crappy
        y = [-3, -10, -3,
                0,  0,   0,
              +3, +10, +3]
        x = [-3, 0,  +3,
              -10, 0, +10,
               -3,  0,  +3]
        return self._apply_filter(im, y, x)
    
    # because of how gradients are calculated, a gradient in the x direction = a vertical line.
    def sobel_filter(self, im):
        y = [-1, -2, -1,
               0,  0,  0,
              +1, +2, +1]
        x = [-1, 0, +1,
               -2, 0, +2,
               -1, 0, +1]
        return self._apply_filter(im, y, x)

    def get_gradient_magnitude_and_angle(self, im):
        gy, gx = self.sobel_filter(im)
        mag = self.get_magnitude(gy, gx)
        phi = self.get_angle(gy, gx)
        return mag, phi

    def get_magnitude(self, gy, gx):
        """ calculate gradient magnitude from Gx and Gy, the gradients in x and y, respectively """
        return np.hypot(gy, gx)  # == np.sqrt(sobelX**2 + sobelY**2)

    def get_angle(self, gy, gx):
        """ calculate gradient angle. For each pixel determine direction of gradient in radians. 0 - 2pi """
        phi = np.arctan2(gy, gx)
        phi += 2 * math.pi  # because all of phi is negative for some reason
        phi %= (2 * math.pi)  # ensure that angle values are only between 0 and 2pi
        return phi

    def get_4_thinned_bidirectional_edges(self, mag, phi):
        """ only keep pixel if is strongest of nieghbors that point in the same direction.
        1 . compare to direction. There are 4 directions. Horizontal, Vertical, And DiagB \ and DiagF /
        2. compare to neighbors. Keep pixels that are stronger than both neighbors
        """
        shape = mag.shape
        higher, lower = np.zeros(shape), np.zeros(shape)
        toLeft, toRight = np.zeros(shape), np.zeros(shape)
        downLeft, upRight = np.zeros(shape), np.zeros(shape)
        upLeft, downRight = np.zeros(shape), np.zeros(shape)
        # ------ vertical ------- #
        higher[:-1, :] = mag[1:, :]  # shift rows up
        lower[1:, :] = mag[:-1, :]  # shift rows down
        # ------ horizontal ------- #
        toLeft[:, :-1] = mag[:, 1:]  # shift rows left
        toRight[:, 1:] = mag[:, :-1]  # shift rows right
        # ------ diagForward ------- #  /
        downLeft[1:, :-1] = mag[:-1, 1:]
        upRight[:-1, 1:] = mag[1:, :-1]
        # ------ diagBackward ------- #  \
        downRight[1:, 1:] = mag[:-1, :-1]
        upLeft[:-1, :-1] = mag[1:, 1:]
        # -------------------------------
        diagFphi, diagBphi, horizPhi, vertPhi = self.get_4_bidirectional_matrices(phi)
        thinVert = vertPhi & (mag > higher) & (mag >= lower)
        thinHoriz = horizPhi & (mag > toLeft) & (mag >= toRight)
        thinDiagF = diagFphi & (mag > downRight) & (mag >= upLeft)  # why is the diagonal logic switched?
        thinDiagB = diagBphi & (mag > downLeft) & (mag >= upRight)
        return [thinDiagF, thinDiagB, thinHoriz, thinVert]

    def get_4_bidirectional_matrices(self, phi):
        """determine which of the bidirectional groups to which a pixel belongs.
        note that I use the rare & , | symbols, which do boolean logic element-wise (bitwise)
        """
        phi = phi % math.pi  # take advantage of symmetry. You only need to analyze 0-pi
        pi = math.pi
        diagForward = (phi > 2 * pi / 16) & (phi < 6 * pi / 16)  # /
        diagBackward = (phi > 10 * pi / 16) & (phi < 14 * pi / 16)  # \
        horizontal = (phi <= 2 * pi / 16) | (phi >= 14 * pi / 16)  # _    horizontal is only one using the | operator because it's
                                                                                          # got two relevant portions
        vertical= (phi >= 6 * pi / 16) & (phi <= 10 * pi / 16)  # |
        return [diagForward, diagBackward, horizontal, vertical]

    def get_2d_gaussian_filter(self, k):
        horizontalG = scipy.signal.general_gaussian(k, 1, 0.8)
        verticalG = np.reshape(horizontalG, (k, 1))
        gaussian2d =  horizontalG * verticalG
        normalized = gaussian2d / gaussian2d.sum()  # so the net sum will equal 1
        return normalized

    def smooth_image(self, im):
##        gaussian = self.get_2d_gaussian_filter(5)
        gaussian = [2, 4, 5, 4, 2,
                        4, 9, 12, 9, 4,
                        5, 12, 15, 12, 5,
                        2, 4, 5, 4, 2,
                        4, 9, 12, 9, 4]
        gaussian = 1.0 / 159 * np.reshape(gaussian, (5,5))
        return scipy.signal.convolve(im, gaussian, mode='same')

    def normalize_magnitude(self, mag):
        """ scales magnitude matrix back to 0 - 255 values """
        offset = mag - mag.min()  # offset mag so that minimum value is always 0
        if offset.dtype == np.uint8:
            raise
        normalized = offset * 255 / offset.max()  # now.. if this image isn't float, you're screwed
        return offset * 255 / offset.max()

    def get_combined_thinned_image(self, mag, phi):
        thinDiagF, thinDiagB, thinVert, thinHoriz = self.get_4_thinned_bidirectional_edges(mag, phi)
        normalMag = self.normalize_magnitude(mag)
        thinNormalMag = np.array(normalMag * (thinDiagF + thinDiagB + thinVert + thinHoriz), dtype=np.uint8)  # convert to uint8 image format.
        return thinNormalMag

    def edge_tracking(self, weak, strong):
        """ hysteresis edge tracking: keeps weak pixels that are direct neighbors to strong pixels. Improves line detection.
        :param weak: an image thresholded by the lower threshold, such that it includes all weak and strong pixels
        :param strong: an image thresholded by the higher threshold, such that it includes only strong pixels
        """
        blurKernel = np.ones((3,3)) / 9
        strongSmeared = scipy.signal.convolve(strong, blurKernel, mode='same') > 0
        # keep nearby weak pixels
        return weak & strongSmeared  # keeps all the original strong 

    def double_threshold(self, im):
        """ obtain two thresholds for determining weak and strong pixels. return two images, weak and strong,
        where strong contains only strong pixels, and weak contains both weak and strong
        """
        otsu = OtsuThresholdMethod(im)
        highThresh = otsu.get_threshold_for_black_and_white()
        lowThresh = 0.5 * highThresh
        weakLines = im > lowThresh
        strongLines = im > highThresh
        return weakLines, strongLines

    def find_edges(self, im):
        """ returns boolean array represting lines. to convert to image just use edges * 255 """
        if im.ndim > 2 and im.shape[-1] > 1:  # aka if we have a full color picture
            im = im[:, :, 0]  # sorry, we can only deal with one channel. I hope you loaded it as greyscale!
        smoothed = self.smooth_image(im)
        mag, phi = self.get_gradient_magnitude_and_angle(smoothed)
        thinNormalMag = self.get_combined_thinned_image(mag, phi)
        weak, strong = self.double_threshold(thinNormalMag)
        cannyEdges = self.edge_tracking(weak, strong)
        return cannyEdges, thinNormalMag


if __name__ == '__main__':
##    filename = 'car.jpg'
##    imOriginal = cv2.imread(filename)
##
##    canny = CannyEdgeDetect()
##    blue = imOriginal[:, :, 0]
##
##    edges = canny.find_edges(blue)
##    cv2.imwrite('edges.jpg', edges * 255)

    import os
    canny = CannyEdgeDetect()
    cwd = os.getcwd()
    inputDir ='images/input'
    outputDir = 'images/output'
    os.chdir(inputDir)
    images = os.listdir('.')
    os.chdir(cwd)
    os.chdir(outputDir)
    for f in images:
        if '.jpg' not in f:  # it's some other file or folder
            continue
        print('reading', f)
        filepath = os.path.join(cwd, inputDir, f)
        im4canny = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        edgesFinal, uncanny = canny.find_edges(im4canny)
        cv2.imwrite(f, edgesFinal * 255)  # we are already in the outputDir
        cv2.imwrite(f.replace('.jpg', '_2.jpg'), uncanny)
    


##smoothed = canny.smooth_image(blue)
##y, x = canny.sobel_filter(smoothed)
##y, x = canny.scharr_filter(smoothed)
##x = canny.sobel_x(smoothed)
##y = canny.sobel_y(smoothed)
##phi = canny.sobel_phi(x, y)
##mag = canny.sobel_mag(x, y)  # of course... mag is scaled crazy high. We need to scale back down to 255

##normalMag = np.array(canny.normalize_magnitude(mag), dtype=np.uint8)

##otsu = OtsuThresholdMethod(normalMag)
##thresh = otsu.get_threshold_for_black_and_white()
##gradientBW = mag > thresh
##cv2.imwrite('gradientBW.jpg', gradientBW * 255)
##cv2.imwrite('strongLines.jpg', strongLines * 255)
##cv2.imwrite('weakLines.jpg', weakLines * 255)
##cv2.imwrite('cannyImage.jpg', cannyImage)
##cv2.imwrite('strongNeighbors.jpg', strongNeighbors * 255)




##realDiagF = thinDiagF * normalMag
##realDiagB = thinDiagB * normalMag
##realVert = thinVert * normalMag
##realHoriz = thinHoriz * normalMag
##
##cv2.imwrite('realVert.jpg', 255 * realVert)
##cv2.imwrite('realHoriz.jpg', 255 * realHoriz)
##cv2.imwrite('realDiagB.jpg', 255 * realDiagB)
##cv2.imwrite('realDiagF.jpg', 255 * realDiagF)

##def threshold_experiment(im):
##    for thresh in range(0, 20, 1):
##        test = im > thresh
##        cv2.imwrite('images/' + str(thresh) + '.jpg', 255 * test)

##cv2.imwrite('thinVert.jpg', 255 * thinVert)
##cv2.imwrite('thinHoriz.jpg', 255 * thinHoriz)
##cv2.imwrite('thinDiagB.jpg', 255 * thinDiagB)
##cv2.imwrite('thinDiagF.jpg', 255 * thinDiagF)

#cv2.imwrite('.jpg', 255 * )

##cv2.imwrite('diagForward.jpg', 255 * diagForward)  # multiply by 255 to convert to common image type
##cv2.imwrite('diagBackward.jpg', 255 * diagBackward)
##cv2.imwrite('horizontal.jpg', 255 * horizontal)
##cv2.imwrite('vertical.jpg', 255 * vertical)
