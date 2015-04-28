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

    def __init__(self, im):
        """ initializes the Otsu method to argument image. """
        if not (im.max() <= 255 and im.min() >= 0):
            raise ValueError('image needs to be scaled 0-255, AND dtype=uint8')
        images = [im]
        channels = [0]
        mask = None
        self.L = 256  # L = number of intensity levels
        bins = [self.L]
        ranges = [0, self.L]
        self.hist = cv2.calcHist(images, channels, mask, bins, ranges)
##        h, w = im.shape[:2]
##        self.N = float(h * w)  # N = total # of pixels. use float so that percentage calculations also become float
        # I don't want to weight the threshold by how many blacks there are. Therefore....
##        self.hist[0] = 1  # give black 1 pixel only
        self.N = float(sum(self.hist[:]))
        self.probabilityLevels = [self.hist[i] / self.N for i in range(self.L)]  # percentage of pixels at each intensity level i
                                                                                                               # => P_i
        s = 0.0
        self.omegas = []  # sum of probability levels up to k
        for i in range(self.L):
            s += float(self.probabilityLevels[i])
            self.omegas.append(s)
##        self.probabilityThreshold = [sum(self.probabilityLevels[:i]) for i in range(self.L)]  # probability of all pixels <= i
        self.meanLevels = [i * self.hist[i] / self.N for i in range(self.L)]  # mean level of pixels at intensity level i
                                                                                                          # => i * P_i
        s = 0.0
        self.mus = []
        for i in range(self.L):
            s += float(self.meanLevels[i])
            self.mus.append(s)
        self.muT = s
        
##        self.meanThreshold = [sum(self.meanLevels[:i]) for i in range(self.L)]  # mean of all pixels <= i
        self.totalMeanLevel = sum(self.meanLevels)
        self.classVariances = [self.variance_at_threshold(k) for k in range(self.L)]  # sigmaB for each threshold level 0- L
##        self.classVariances = [self.between_class_variance(k) for k in range(self.L)]  # between class variance
        # both class variance calculations are very similar

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
        k1, k2 = coordinates[0]
        print(k1, k2)
        k1, k2 = int(k1), int(k2)
        return k1, k2

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
            print('denom = 0')
            return 0
        return numerator / denominator

##    def variance_between_thresholds(self, k1, k2):
##        omega_K = self.probabilityThreshold[k2] - self.probabilityThreshold[k1]
##        mu_K = (self.meanThreshold[k2] - self.meanThreshold[k1]) / self.probabilityThreshold[k1]
##
##    def get_2_thresholds(self):
##        

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

##    def get_n_thresholds(self, n):
##        omegas = []
##        mus = []
##        for i in range(n):
##            omegas.append(


if __name__ == '__main__':
    filename = 'car.jpg'
    im = cv2.imread(filename)
    otsu = OtsuThresholdMethod(im)
    threshold = otsu.get_threshold_for_black_and_white()
    blue = im[:, :, 0]  # just choose single channel
    bw = blue >= threshold  # boolean black and white
    cv2.imwrite('bw_car.jpg', bw * 255)  # multiply by 255 to create valid image range of 0-255

