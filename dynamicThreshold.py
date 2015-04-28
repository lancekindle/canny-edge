import math
import cv2

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
        h, w = im.shape[:2]
        self.N = float(h * w)  # N = total # of pixels. use float so that percentage calculations also become float
        bins = [self.L]
        ranges = [0, self.L]
        self.hist = cv2.calcHist(images, channels, mask, bins, ranges)
        self.probabilityLevels = [self.hist[i] / self.N for i in range(self.L)]  # percentage of pixels at each intensity level i
                                                                                                               # => P_i
##        self.probabilityThreshold = [sum(self.probabilityLevels[:i]) for i in range(self.L)]  # probability of all pixels <= i
        self.meanLevels = [i * self.hist[i] / self.N for i in range(self.L)]  # mean level of pixels at intensity level i
                                                                                                          # => i * P_i
##        self.meanThreshold = [sum(self.meanLevels[:i]) for i in range(self.L)]  # mean of all pixels <= i
        self.totalMeanLevel = sum(self.meanLevels)
        self.classVariances = [self.variance_at_threshold(k) for k in range(self.L)]  # sigmaB for each threshold level 0- L

    def variance_at_threshold(self, k):
        """ works for a single threshold value k """
        omegaK = self.percentage_at_threshold(k)  # omega(K)
        muK = self.mean_level_at_threshold(k)  # mu(k)
        numerator = (self.totalMeanLevel * omegaK - muK)**2
        denominator = omegaK * (1 - omegaK)
        return numerator / denominator

##    def variance_between_thresholds(self, k1, k2):
##        omega_K = self.probabilityThreshold[k2] - self.probabilityThreshold[k1]
##        mu_K = (self.meanThreshold[k2] - self.meanThreshold[k1]) / self.probabilityThreshold[k1]
##
##    def get_2_thresholds(self):
##        

    def percentage_at_threshold(self, k):
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

