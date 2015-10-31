import cv2
import scipy
from scipy import signal
import pylab
import math
import numpy as np
from dynamicThreshold import OtsuThresholdMethod

class SimpleEdgeDetect:

    def smooth_image(self, im):
        gaussian = [2,  4,  5,  4, 2,
                    4,  9, 12,  9, 4,
                    5, 12, 15, 12, 5,
                    2,  4,  5,  4, 2,
                    4,  9, 12,  9, 4]
        gaussian = 1.0 / sum(gaussian) * np.reshape(gaussian, (5,5))
        return scipy.signal.convolve(im, gaussian, mode='same')

    def find_edges(self, im):
        smoothed = self.smooth_image(im)
        edges = im - smoothed
        return edges


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
              0,   0,  0,
             +3, +10, +3]
        x = [ -3, 0,  +3
             -10, 0, +10,
              -3, 0,  +3 ]
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
        gaussian = [2,  4,  5,  4, 2,
                    4,  9, 12,  9, 4,
                    5, 12, 15, 12, 5,
                    2,  4,  5,  4, 2,
                    4,  9, 12,  9, 4]
        gaussian = 1.0 / sum(gaussian) * np.reshape(gaussian, (5,5))
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
        weakOnly = weak - strong
        blurKernel = np.ones((3,3)) / 9
        strongSmeared = scipy.signal.convolve(strong, blurKernel, mode='same') > 0
        strongWithWeakNeighbors = weak & strongSmeared  # this is your normal result. trying for more will be expensive

        return strongWithWeakNeighbors

        
        weakNeighbors = strongWithWeakNeighbors ^ strong  #exclusive or
        # now here's where we track along the current valid pixel
        h, w = weak.shape[:2]
        pts = np.transpose(np.nonzero(weakNeighbors))  # coordinates of front of lines to begin tracking: y, x
        frontier = set([(y, x) for y, x in pts])
        frontierWave = set()  # searching in waves makes our search a breadth-first search
        explored = list()
        directions = [-1, 0, 1]
        jitter = []  # jitter = moving around center
        for dy in directions:
            for dx in directions:
                if dx == dy == 0:  # don't add center point
                    continue
                jitter.append((dy, dx))
        depth = 0
        while frontier or frontierWave:
            if not frontier:  # frontier is exhausted
                frontier = frontierWave
                frontierWave = set()  # start next wave
                depth += 1
                if depth >= min(h, w) / 2:  # if our line is bigger than a dimension in our image, then it's probably a runaway.
                    print('depth', depth)
                    break
            fy, fx = frontier.pop()
            explored.append((fy, fx))
            # explore around point, add neighbor
            for dy, dx in jitter:
                y, x = dy + fy, dx + fx
                if y == h or y == -1 or x == w or x == -1:  # skip pixels outside boundary
                    continue
                if weak[y, x] and (y, x) not in explored and (y, x) not in frontier:  # found an unexplored, connected weak pixel
                    frontierWave.add((y, x))  # nothing will change if this point already existed in frontier
        # now we've explored all the connected-to-strong lines. Next up, mark them on strongWithWeakNeighbors
        print(len(explored))
        ys = [y for y, x in explored]
        xs = [x for y, x in explored]
        strongWithWeakNeighbors[ys, xs] = True
            
        # keep nearby weak pixels
        return   strongWithWeakNeighbors # keeps all the original strong 

    def double_threshold(self, im):
        """ obtain two thresholds for determining weak and strong pixels. return two images, weak and strong,
        where strong contains only strong pixels, and weak contains both weak and strong
        """
        otsu = OtsuThresholdMethod(im, 4)  # speedup of 4 keeps things pretty accurate but much faster
        _, lowThresh, highThresh, tooHigh = otsu.calculate_n_thresholds(4)
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
        return cannyEdges, weak * 255


if __name__ == '__main__':
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
        if '.jpg' not in f:
            continue
        print('reading', f)
        filepath = os.path.join(cwd, inputDir, f)
        im4canny = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
        edgesFinal, uncanny = canny.find_edges(im4canny)
        cv2.imwrite(f.replace('.jpg', '_strong_only.jpg'), edgesFinal * 255)
        cv2.imwrite(f.replace('.jpg', '_weak_included.jpg'), uncanny)
