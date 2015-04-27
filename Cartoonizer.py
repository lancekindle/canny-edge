from EdgeDetector import EdgeDetector
import cv2
import scipy
import pylab
import math
import numpy as np

def get_best_threshold(im):
    # create a histogram of the grayscales. We want to find a grayscale that has a decent number of pixels
    channels = [0]
    images = [im]
    mask = None
    bins = [256]
    ranges = [0, 256]
    hist = cv2.calcHist(images, channels, mask, bins, ranges)
    h, w = im.shape[:2]
    numPixels = 1.0 * h * w
    binSize = numPixels / 256
    hist = hist.squeeze()  # remove extra 1 dimension.
    hist = hist / binSize  # "normalize" values of histrogram to the number of pixels. Helps with slope calculations
    difference = [-1, 1]
    histd = scipy.signal.convolve(hist, difference, mode='same')  # convolve to get a first-deritive of the histogram slope
    medianKernel = 3
    histdf = scipy.signal.medfilt(histd, medianKernel)  # median filter to remove any crazy swings in slope
    trimming = int(medianKernel / 2)  
    histdf = histdf[trimming:-trimming]  # trim to remove eccentric ends created by median filtering
    degrees = np.array([ 180 / math.pi * math.atan(diff) for diff in histdf])  # convert derivative to angle (in degrees)
    lowThresh = 60
    lowThresholded = degrees < lowThresh  # find where angle becomes less than threshold (50)
    lowIndex = list(lowThresholded).index(1) + trimming  # add trimming to offset the medianfiltering
    lowIndex -= 1  # offset by one so that you actually have the last angle that was > 50

    highThresh = 10
    highThresholded = degrees < highThresh  # find where angle becomes less than threshold (50)
    highIndex = list(highThresholded).index(1) + trimming  # add trimming to offset the medianfiltering
    highIndex -= 1  # offset by one so that you actually have the last angle that was > 50
    return lowIndex, highIndex

def get_median_filter_kernel_size(h, w):
    kernelArea = h * w / 8000  # we want to split the image into 6000 visual chunks
    kernelSize = int(math.sqrt(kernelArea))  # get kernel size that would approximate the area
    if kernelSize % 2 == 0:
        kernelSize += 1  # must make sure that kernel size is odd
    return max(1, kernelSize)  # kernel must be at least 1

def get_2d_gaussian_filter(k):
    horizontalG = scipy.signal.general_gaussian(k, 1, 0.8)
    verticalG = np.reshape(horizontalG, (k, 1))
    gaussian2d =  horizontalG * verticalG
    normalized = gaussian2d / gaussian2d.sum()  # so the net sum will equal 1
    return normalized

class CannyEdgeDetect:

    # because of how gradients are calculated, a gradient in the x direction = a vertical line.
    def sobel_x(self, im):
        Gx = [-1, 0, +1,
                 -2, 0, +2,
                 -1, 0, +1]
        Gx = np.reshape(Gx, (3,3))
        return scipy.signal.convolve(im, Gx)

    def sobel_y(self, im):
        Gy = [-1, -2, -1,
                  0,  0,  0,
                 +1, +2, +1]
        Gy = np.reshape(Gy, (3,3))
        return scipy.signal.convolve(im, Gy)

    def sobel_mag(self, sobelX, sobelY):
        return np.hypot(sobelX, sobelY)  # == np.sqrt(sobelX**2 + sobelY**2)

    def sobel_phi(self, sobelX, sobelY):
        phi = np.arctan2(sobelY, sobelX)
        phi += 2 * math.pi  # because all of phi is negative for some reason
        phi %= (2 * math.pi)  # ensure that angle values are only between 0 and 2pi
        return phi

    def get_4_thinned_bidirectional_edges(self, sobelMag, sobelPhi):
        """ only keep pixel if is strongest of nieghbors that point in the same direction.
        1 . compare to direction. There are 4 directions. Horizontal, Vertical, And DiagB \ and DiagF /
        2. compare to neighbors. Keep pixels that are stronger than both neighbors
        """
        shape = sobelMag.shape
        higher, lower = np.zeros(shape), np.zeros(shape)
        toLeft, toRight = np.zeros(shape), np.zeros(shape)
        downLeft, upRight = np.zeros(shape), np.zeros(shape)
        upLeft, downRight = np.zeros(shape), np.zeros(shape)
        # ------ vertical ------- #
        higher[:-1, :] = sobelMag[1:, :]  # shift rows up
        lower[1:, :] = sobelMag[:-1, :]  # shift rows down
        # ------ horizontal ------- #
        toLeft[:, :-1] = sobelMag[:, 1:]  # shift rows left
        toRight[:, 1:] = sobelMag[:, :-1]  # shift rows right
        # ------ diagForward ------- #  /
        downLeft[1:, :-1] = sobelMag[:-1, 1:]
        upRight[:-1, 1:] = sobelMag[1:, :-1]
        # ------ diagBackward ------- #  \
        downRight[1:, 1:] = sobelMag[:-1, :-1]
        upLeft[:-1, :-1] = sobelMag[1:, 1:]
        # -------------------------------
        diagFphi, diagBphi, horizPhi, vertPhi = self.get_4_bidirectional_matrices(sobelPhi)
        thinVert = vertPhi & (sobelMag > higher) & (sobelMag >= lower)
        thinHoriz = horizPhi & (sobelMag > toLeft) & (sobelMag >= toRight)
        thinDiagF = diagFphi & (sobelMag > downRight) & (sobelMag >= upLeft)  # why is the diagonal logic switched?
        thinDiagB = diagBphi & (sobelMag > downLeft) & (sobelMag >= upRight)
        return [thinDiagF, thinDiagB, thinHoriz, thinVert]

    def get_4_bidirectional_matrices(self, phi):
        """determine which of the bidirectional groups to which a pixel belongs.
        note that I use the rare & , | symbols, which do boolean logic element-wise (bitwise)
        """
        pi = math.pi
        diagForward = ((phi > 2 * pi / 16) & (phi < 6 * pi / 16)) | ((phi > 18 * pi / 16) & (phi < 22 * pi / 16))  # /
        diagBackward = ((phi > 10 * pi / 16) & (phi < 14 * pi / 16)) | ((phi > 26 * pi / 16) & (phi < 30 * pi / 16))  # \
        horizontal = ((phi >= 30 * pi / 16) & (phi <= 2 * pi / 16)) | ((phi >= 14 * pi / 16) & (phi <= 18 * pi / 16))  # _
        vertical= ((phi >= 6 * pi / 16) & (phi <= 10 * pi / 16)) | ((phi >= 22 * pi / 16) & (phi <= 26 * pi / 16))  # |
        return [diagForward, diagBackward, horizontal, vertical]

filename = 'images/final_project_input.png'
filename = 'images/blending_black.jpg'
imOriginal = cv2.imread(filename)

canny = CannyEdgeDetect()
blue = imOriginal[:, :, 0]
x = canny.sobel_x(blue)
y = canny.sobel_y(blue)
phi = canny.sobel_phi(x, y)
sobelMag = canny.sobel_mag(x, y)
cv2.imwrite('sobel_phi.jpg', phi)

thinDiagF, thinDiagB, thinVert, thinHoriz = canny.get_4_thinned_bidirectional_edges(sobelMag, phi)



##cv2.imwrite('thinVert.jpg', 255 * thinVert)
##cv2.imwrite('thinHoriz.jpg', 255 * thinHoriz)
##cv2.imwrite('thinDiagB.jpg', 255 * thinDiagB)
##cv2.imwrite('thinDiagF.jpg', 255 * thinDiagF)

#cv2.imwrite('.jpg', 255 * )

##cv2.imwrite('diagForward.jpg', 255 * diagForward)  # multiply by 255 to convert to common image type
##cv2.imwrite('diagBackward.jpg', 255 * diagBackward)
##cv2.imwrite('horizontal.jpg', 255 * horizontal)
##cv2.imwrite('vertical.jpg', 255 * vertical)


raise

edgedetector = EdgeDetector()

greyEdges = edgedetector.edge_detect_image_grayscale(filename)
##cv2.imwrite('edge_result.jpg', imEdges)

lowThresh, highThresh = get_best_threshold(greyEdges)
bwh = greyEdges >= highThresh
bwl = greyEdges >= lowThresh
blackEdges = 1 - bwl  # now all edges are black
imBlackEdges = np.zeros(imOriginal.shape)
h, w, channels = imOriginal.shape[:3]
for ch in range(channels):
    imBlackEdges[:, :, ch] = blackEdges
imLinesAccentuated = imOriginal * imBlackEdges

cv2.imwrite('lines.png', imLinesAccentuated)


























##
##imFiltered = np.zeros(imOriginal.shape)
##h, w, channels = imOriginal.shape[:3]
##medianKernel = get_median_filter_kernel_size(h, w)
##for ch in range(channels):
##    imFiltered[:, :, ch] = scipy.signal.medfilt(imOriginal[:, :, ch], medianKernel)
##
##cv2.imwrite('filtered.jpg', imFiltered)
##imOriginal = imFiltered
##
##filename = 'filtered.jpg'
