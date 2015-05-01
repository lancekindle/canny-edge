import math
import cv2
import numpy as np

# otsu's method: http://web-ext.u-aizu.ac.jp/course/bmclass/documents/otsu1979.pdf
# https://en.wikipedia.org/wiki/Otsu's_method
# a good explaination
# http://www.labbookpages.co.uk/software/imgProc/otsuThreshold.html
# a paper that explains Otsu's method and helps explain n-levels of thresholding
# http://www.iis.sinica.edu.tw/page/jise/2001/200109_01.pdf


class OtsuThresholdMethod(object):

    def __init__(self, im, speedup=1):
        """ initializes the Otsu method to argument image. Image is only analyzed as greyscale.
        since it assumes that image is greyscale, it will choose blue channel to analyze. MAKE SURE YOU PASS GREYSCALE
        choosing a bins # that's smaller than 256 will help speed up the image generation,
        BUT it will also mean a little more inaccurate tone-mapping.
        You'll have to rescale the passed thresholds up to 256 in order to accurately map colors
        """
        if not (im.max() <= 255 and im.min() >= 0):
            raise ValueError('image needs to be scaled 0-255, AND dtype=uint8')
        images = [im]
        channels = [0]
        mask = None
        bins = 256 / speedup
        self.speedup = speedup  # you are binning using speedup; remember to scale up threshold by speedup
        self.L = bins  # L = number of intensity levels
        bins = [bins]
        ranges = [0, 256]  # range of pixel values. I've tried setting this to im.min() and im.max() but I get errors...
        self.hist = cv2.calcHist(images, channels, mask, bins, ranges)
        self.N = float(sum(self.hist[:]))
        self.probabilityLevels = [self.hist[i] / self.N for i in range(self.L)]  # percentage of pixels at each intensity level i
                                                                                                               # => P_i
        s = 0.0
        self.omegas = []  # sum of probability levels up to k
        for i in range(self.L):
            s += float(self.probabilityLevels[i])
            self.omegas.append(s)
        self.meanLevels = [i * self.hist[i] / self.N for i in range(self.L)]  # mean level of pixels at intensity level i
                                                                                                          # => i * P_i
        s = 0.0
        self.mus = []
        for i in range(self.L):
            s += float(self.meanLevels[i])
            self.mus.append(s)
        self.muT = s
        self.totalMeanLevel = sum(self.meanLevels)
        self.classVariances = [self.variance_at_threshold(k) for k in range(self.L)]  # sigmaB for each threshold level 0- L

    def calculate_2_thresholds(self):
        sigmaB = np.zeros((self.L, self.L))  # 2d space representing all choices of k1, k2 thresholds
        for k1 in range(self.L - 1):  # 0 - 254
            for k2 in range(k1 + 1, self.L):  # 1 - 255. K2 > K1 (when doing thresholding. So for all ranges, only go up to (but not
                                                    # including) K. So that way our thresholds never overlap
                thresholds = [0, k1, k2, self.L - 1]  # num of classes = M - 1, M = len(thresholds)
                sigmaB[k1, k2] = self.between_classes_variance_given_thresholds(thresholds)
        best = sigmaB.max()
        bestSigmaSpace = sigmaB == best
        locationOfBestThresholds = np.nonzero(bestSigmaSpace)
        coordinates = np.transpose(locationOfBestThresholds)
        k1, k2 = coordinates[0] * self.speedup
        return k1, k2

    def calculate_n_thresholds(self, n):
        shape = [self.L for i in range(n)]
        sigmaBspace = np.zeros(shape)
        thresholdGen = self.dimensionless_thresholds_generator(n)
        for kThresholds in thresholdGen:
            thresholds = [0] + kThresholds + [self.L - 1]
            thresholdSpace = tuple(kThresholds)  # accessing a numpy array using the list gives us an array, rather than a point like we want
            sigmaBspace[thresholdSpace] = self.between_classes_variance_given_thresholds(thresholds)
        maxSigma = sigmaBspace.max()
        bestSigmaSpace = sigmaBspace == maxSigma
        locationOfBestThresholds = np.nonzero(bestSigmaSpace)
        coordinates = np.transpose(locationOfBestThresholds)
        print(list(coordinates[0]))
        return list(coordinates[0] * self.speedup)  # all thresholds right there!

    def dimensionless_thresholds_generator(self, n, minimumThreshold=0):
        # ok ok, I gotta use a freaking recursive algorithm here. If self.L >= 1024, this will fail. Otherwise it should work fine
        """ generates thresholds in a list """
        if n == 1:
            for threshold in range(minimumThreshold, self.L):
                yield [threshold]
        elif n > 1:
            m = n - 1  # number of additional thresholds
            for threshold in range(minimumThreshold, self.L - m):
                moreThresholds = self.dimensionless_thresholds_generator(n - 1, threshold + 1)
                for otherThresholds in moreThresholds:
                    allThresholds = [threshold] + otherThresholds
                    yield allThresholds
        else:
            raise ValueError('# of dimensions should be > 0:' + str(n))

    def between_classes_variance_given_thresholds(self, thresholds):
        numClasses = len(thresholds) - 1
        sigma = 0
        for i in range(numClasses):
            k1 = thresholds[i]
            k2 = thresholds[i+1]
            sigma += self.between_thresholds_variance(k1, k2)
        return sigma

    def between_thresholds_variance(self, k1, k2):  # to be used in calculating between class variances only!
        omega = self.omegas[k2] - self.omegas[k1]
        mu = self.mus[k2] - self.mus[k1]
        muT = self.muT
        return omega * ( (mu - muT)**2)

    def between_class_variance(self, k):
        """ calculate between-class variance for each threshold """
        omega = self.omegas[k]
        mu = self.mus[k]
        muT = self.totalMeanLevel
        if omega == 0 or omega == 1:  # result will be 0 if true
            return 0
        return omega * (1 - omega) * (mu / omega - (muT - mu) / (1 - omega) )**2

    def variance_at_threshold(self, k):
        """ works for a single threshold value k """
        omega = self.probability_at_threshold(k)  # omega(K)
        mu = self.mean_level_at_threshold(k)  # mu(k)
        numerator = (self.totalMeanLevel * omega - mu)**2
        denominator = omega * (1 - omega)
        if denominator == 0:
##            print('denom = 0')
            return 0
        return numerator / denominator

    def probability_at_threshold(self, k):
        """ return sum percentage of all pixels at and below threshold level k.
        == omega == w(k)
        """
        return sum(self.probabilityLevels[:k+1])

    def mean_level_at_threshold(self, k):
        """  """
        return sum(self.meanLevels[:k+1])

    def get_threshold_for_black_and_white(self):
        maxSigmaB = max(self.classVariances)  # maximized class variance.
        threshold = self.classVariances.index(maxSigmaB)
        return threshold


if __name__ == '__main__':
    filename = 'boat.jpg'
    dot = filename.index('.')
    prefix = filename[:dot]
    im = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
    otsu = OtsuThresholdMethod(im)
    blue  = im  # since we loaded in as greyscale

##    k1, k2 = otsu.calculate_2_thresholds()
##    grey = ((blue >= k1) & (blue < k2)) * 128
##    white = (blue >= k2) * 255
##    threeLevels = np.zeros(blue.shape, dtype=np.uint8)
##    threeLevels += grey
##    threeLevels += white
##    cv2.imwrite('car_3grey.jpg', threeLevels)
    
    for toneScale in [64, 32, 16, 8, 4, 2, 1]:  # 1 is the slowest (and most accurate) so we leave that one out
        n = 2  # means it'll be 4-tone image
        otsu = OtsuThresholdMethod(im, toneScale)
        thresholds = otsu.calculate_n_thresholds(n)
        thresholds = [t for t in thresholds]  # change it from a numpy array to a list
##        print(thresholds)
##        print(thresholds)
        clipThreshold = thresholds[1:] + [None]
        greyValues = [256 / n * (i + 1) for i in range(n)]
        nLevels = np.zeros(blue.shape, dtype=np.uint8)
        for i in range(len(thresholds)):
            k1 = thresholds[i]
            gval = greyValues[i]
            bw = (blue >= k1)
            k2 = clipThreshold[i]
            if k2:
                bw &= (blue < k2)
            grey = bw * gval
            nLevels += grey
        cv2.imwrite(prefix + '_' + str(n + 1) + 'grey' + '_speedup_' + str(toneScale) + '.jpg', nLevels)
    
