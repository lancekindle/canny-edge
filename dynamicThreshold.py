import math
import cv2
import numpy as np

# otsu's method: http://web-ext.u-aizu.ac.jp/course/bmclass/documents/otsu1979.pdf
# https://en.wikipedia.org/wiki/Otsu's_method
# a good explaination
# http://www.labbookpages.co.uk/software/imgProc/otsuThreshold.html
# a paper that explains Otsu's method and helps explain n-levels of thresholding
# http://www.iis.sinica.edu.tw/page/jise/2001/200109_01.pdf

class OtsuFastThreshold(object):

    def __init__(self, im):
        self.im = im
        h, w = im.shape[:2]
        N = float(h * w)  # N = number of pixels in image
                # cast N as float, because we need float answers when dividing by N
        L = 256  # L = number of intensity levels
        images = [im]
        channels = [0]
        mask = None
        bins = [L]
        ranges = [0, L]  # range of pixel values. I've tried setting this to im.min() and im.max() but I get errors...
        hist = cv2.calcHist(images, channels, mask, bins, ranges)  # hist is a numpy array of arrays. So accessing hist[0]
                # gives us an array, which messes with calculating omega. So we convert np array to list of ints
        hist = [int(h) for h in hist]  # used to be floats. I don't think we need floats
        omegas, mus, self.muT = self.calculate_omegas_and_mus_from_histogram(hist)
        print(omegas)
        self.histPyramid = self.binary_reduce_pyramid(hist)
        self.omegaPyramid = self.binary_reduce_pyramid(omegas)
        self.muPyramid = self.binary_reduce_pyramid(mus)
##            for i in range(0, len(hist), 2):
##                print(i, len(hist))
##                reducedHist.append(hist[i] + hist[i+1])
            

    def calculate_omegas_and_mus_from_histogram(self, hist):
        L = len(hist)  # L = number of intensity levels
        N = float(sum(hist))  # N = number of pixels in image
                # cast N as float, because we need float answers when dividing by N
        probabilityLevels = [hist[i] / N for i in range(L)]  # percentage of pixels at each intensity level i
                                                                                                               # => P_i
        self.probabilityLevels = probabilityLevels
        meanLevels = [i * probabilityLevels[i] for i in range(L)]  # mean level of pixels at intensity level i
                                                                                                          # => i * P_i
        self.meanLevels = meanLevels
        # is meanLevels really mean? or is it a weighting of percentage of pixels....
        ptotal = 0.0
        omegas = []  # sum of probability levels up to k
        for i in range(L):
            ptotal += probabilityLevels[i]
            omegas.append(ptotal)
        mtotal = 0.0
        mus = []
        for i in range(L):
            mtotal += meanLevels[i]
            mus.append(mtotal)
        muT = float(mtotal)  # muT is the total mean levels.
        return omegas, mus, muT

    def binary_reduce_pyramid(self, data):
        """ from a list (data), creates a pyramid representing increasingly reduced versions of the data.
        at the end of the pyramid, the last element will be of length 2. To access an element of length N,
        simply access it at x, where x = -log(N, 2). Or, in other words, N = 2 ^ (-x)
        """
        L = len(data)
        reductions = int(math.log(L, 2))  # should be 8 (if we assume picture is 256 bins)
##        pyramid = np.array([None for i in range(reductions)])
        pyramid = []
        for i in range(reductions):  # generate reduced versions of histogram, omegas, and mus
            pyramid.append(data)
##            pyramid[i] = data
            binaryReducedData = [data[i] + data[i+1] for i in range(0, L, 2)]
            data = binaryReducedData
            L = L / 2  # update L to reflect the length of the new histogram, omegas, and mus
        return pyramid

    def binary_reduce_to_pyramid(self, hist, omegas, mus):
        L = len(hist)
        reductions = int(math.log(L, 2))
        histPyramid = []
        omegaPyramid = []
        muPyramid = []
        for i in range(reductions):
            self.histMatrix[i] = hist
            reducedHist = [hist[i] + hist[i + 1] for i in range(0, L, 2)]
            hist = reducedHist  # collapse a list to half its size, combining the two collpased numbers into one
            #
            self.omegaMatrix[i] = omegas
            reducedOmegas = [omegas[i + 1] for i in range(0, L, 2)]  # because omega represents the sum of pixel probabilities up to that level,
                    # we collapse by choosing the higher percentage
                    # could also write as  = omegas[1::2]
            omegas = reducedOmegas
            #
            self.muMatrix[i] = mus
            reducedMus = [mus[i] + mus[i + 1] for i in range(0, L, 2)]
            mus = reducedMus
            #
            L = L / 2  # update L to reflect the length of the new histogram, omegas, and mus

    def setup(self):
        pass



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
    filename = 'boat.jpg'
    dot = filename.index('.')
    prefix = filename[:dot]
    im = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
    otsu2 = OtsuFastThreshold(im)
    otsu = OtsuThresholdMethod(im)
    raise
##    threshold = otsu.get_threshold_for_black_and_white()
##    blue = im[:, :, 0]  # just choose single channel
    blue  = im  # since we loaded in as greyscale
##    bw = blue >= threshold  # boolean black and white
##    cv2.imwrite('bw_car.jpg', bw * 255)  # multiply by 255 to create valid image range of 0-255
    
##    k1, k2 = otsu.calculate_2_thresholds()
##    grey = ((blue >= k1) & (blue < k2)) * 128
##    white = (blue >= k2) * 255
##    threeLevels = np.zeros(blue.shape, dtype=np.uint8)
##    threeLevels += grey
##    threeLevels += white
##    cv2.imwrite('car_3grey.jpg', threeLevels)

    for toneScale in [64, 32, 16, 8, 4, 2, 1]:  # 1 is the slowest (and most accurate) so we leave that one out
        n = 3  # means it'll be 4-tone image
        otsu = OtsuThresholdMethod(im, toneScale)
        thresholds = otsu.calculate_n_thresholds(n)
        thresholds = [t for t in thresholds]  # change it from a numpy array to a list
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
    
