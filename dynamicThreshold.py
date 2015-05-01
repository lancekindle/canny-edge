import math
import cv2
import numpy as np

# otsu's method: http://web-ext.u-aizu.ac.jp/course/bmclass/documents/otsu1979.pdf
# https://en.wikipedia.org/wiki/Otsu's_method
# a good explaination
# http://www.labbookpages.co.uk/software/imgProc/otsuThreshold.html
# a paper that explains Otsu's method and helps explain n-levels of thresholding
# http://www.iis.sinica.edu.tw/page/jise/2001/200109_01.pdf

class ThresholdHunter(object):
    """ hunt around given thresholds in a small space to look for a better threshold
    """

    def __init__(self, omegas, mus, deviate=2):
        self.sigmaB = BetweenClassVariance(omegas, mus)
        self.bins = self.sigmaB.bins  # used to be called L
        self.deviate = deviate  # hunt 2 (or other amount) to either side of thresholds
    

    def find_best_thresholds_around_original(self, originalThresholds):
        """ this is the one you were last typing up. Given guesses for best threshold, explore to either side of the threshold
        and return the best result.
        """
        shape = [self.deviate * 2 + 1] * len(originalThresholds)
        sigmaSpace = np.zeros(shape)
        for thresholds, offsets in self._jitter_thresholds_and_offsets_generator(originalThresholds, 0, self.bins -  1):
            # even though we access from -2 to 2, our sigma space will not overwrite previous results.
            # just remember when getting coordinates to subtract 2 from each offset to get the true threshold offset
            #ARRRRRRRRRGGGGGHHHHH!!!!!!!!!!!!!!
            # this coordinate thing does not work well with offsets. OK, so if I do a -2 across the board when getting the
            # final results, that means that a best offset of 0 will suddenly look like -2. So that's not going to work properly
            # what WILL work is adding 2 to the offsets before putting it into the sigmaSpace. So that way, -2 WILL
            # return the offsets back to their original value
            offsets = offsets + self.deviate  # set offset range 0->5  (0 -> 2*offset + 1)
            sigmaSpace[tuple(offsets)] = self.sigmaB.get_total_variance(thresholds)
        bestSigmaSpace = sigmaSpace == sigmaSpace.max()
        bestOffsets = np.nonzero(bestSigmaSpace) - self.deviate  # actual offsets are sigmaSpace - deviate due to how we stored them.
        bestOffsets = np.transpose(bestOffsets)       # transpose to match shape....?
        bestThresholds = np.array(originalThresholds) + bestOffsets
        return list(bestThresholds)

    def _jitter_threshold_and_offsets_generator(self, thresholds, min_, max_):
        pastThresh = thresholds[0]
        if len(thresholds) == 1:
            for offset in range(-self.deviate, self.deviate + 1):  # -2 through +2
                thresh = pastThresh + offset
                if thresh < min_ or thresh > max_:
                    continue  # skip since we are conflicting with bounds
                yield [thresh], [offset]
        else:
            thresholds = thresholds[1:]  # new threshold without our threshold included
            m = len(thresholds)  # number of threshold left to generate in chain
            for offset in range(-self.deviate, self.deviate + 1):
                thresh = pastThresh + offset
                if thresh < min_ or thresh + m > max_:  # verify we don't use the same value as the previous threshold
                    continue                         # and also verify our current threshold will not push the last threshold past max
                for otherThresholds, otherOffsets in self.jitter_offsets_generator(thresholds, thresh + 1, max_):
                    yield [thresh] + otherThresholds, [offset] + others


class BetweenClassVariance(object):

    def __init__(self, omegas, mus):
        self.omegas = omegas
        self.mus = mus
        self.bins = len(mus)  # number of bins / luminosity choices
        self.muTotal = sum(mus)

    def get_total_variance(self, thresholds):
        """ function will pad the thresholds argument with minimum and maximum thresholds to calculate
        between class variance
        """
        thresholds = [0] + thresholds + [self.bins - 1]
        numClasses = len(thresholds) - 1
        sigma = 0
        for i in range(numClasses):
            k1 = thresholds[i]
            k2 = thresholds[i+1]
            sigma += self._between_thresholds_variance(k1, k2)
        return sigma

    def _between_thresholds_variance(self, k1, k2):  # to be used in calculating between class variances only!
        omega = self.omegas[k2] - self.omegas[k1]
        mu = self.mus[k2] - self.mus[k1]
        muT = self.muTotal
        return omega * ( (mu - muT)**2)


class OtsuMultithreshold(object):

    def fast_calculate_k_thresholds_better(self, k):
        start = self.get_starting_pyramid_index(k)
        self.bins = len(omegaPyramid[start])
        thresholds = [self.bins / 2 for i in range(k)]  # first-guess thresholds will be middle of road, allowing hunting
                    # algorithm full range of searching
        deviate = self.bins / 2
        for i in range(start, len(omegaPyramid)):
            omegas = self.omegaPyramid[i]
            mus = self.muPyramid[i]
            hunter = ThresholdHunter(omegas, mus, deviate)
            thresholds = hunter.find_best_thresholds_around_original(thresholds)
            threshPyramid.append(thresholds)
            # now we scale-up thresholds and set deviate for hunting in limited area. Logic / experiments suggest that you
            # only need to deviate by up to 2 when scaling up the previous thresholds by 2.
            deviate = 2
            thresholds = list(np.array(thresholds) * 2)
        return thresholds
    
    def get_starting_pyramid_index(k):
        """ given the number of thresholds, return the minium starting index
        of pyramid to use in calculating thresholds
        """
        return math.ceil( math.log(n + 1, 2) )


class OtsuMultithreshold_OLD(object):

    def calculate_thresholds_at_pyramid_level(self, i):
        shape = [5 for i in range(n)]  # 5 since that's the size of each iteration
        # instead of storing the actual threshold as the coordinate, we store the threshold offset as the coordinate
        # offset of -2 is the 0th index, +2 is the 4th index
        sigmaBspace = np.zeros(shape)
        thresholdGen = self.jitter_thresholds_generator(thresholds, self.L)
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

    def calculate_first_run_thresholds(self, n):
        """ n = number of thresholds . In order for this to work, you need to define several variables
        self.L = length of bins / histogram / omegas
        self.omegas = corresponding omegas from the omegaPyramid
        self.mus = corresponding mus from the muPyramid
        """
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

    

    def jitter_thresholds_generator(self, thresholds, jitter=2):
        """ given the current thresholds, will return threshold generator that "jitters" around by 2 integers to either side
        of the original threshold. This is part of the scaling up
        maxThresh should be the length of the current histogram. (or the length of the current omegas or mus)
        If finding the first thresholds, generate a list of [0, 0, 0...0] thresholds, and set jitter = maxThresh
        """
        maxThresh = self.L
        thresholds = np.array(thresholds)  # turn it into an array for quick addition and subtraction
        minThresholds = list(thresholds - jitter)
        maxThresholds = list(thresholds + jitter)
        # verify that first threshold starts >= 0, and proceeding thresholds are successively greater
        adjustedMin = -1
        for i in range(n):
            adjustedMin = max(minThresholds[i], adjustedMax + 1)
            minThresholds[i] = adjustedMin
        # verify that last max threshold <= maxThresh, and preceeding thresholds are successively smaller
        adjustedMax = maxThresh + 1
        for i in range(n - 1, -1, -1):
            adjustedMax = min(maxThresholds[i], adjustedMax - 1)
            maxThresholds[i] = adjustedMax
        return self.bounded_thresholds_generator(n, minimumThresholds, maximumThresholds)

    def bounded_thresholds_generator(self, n, minimumThresholds, maximumThresholds):
        # ok ok, I gotta use a freaking recursive algorithm here. If self.L >= 1024, this will fail. Otherwise it should work fine
        """ generates n thresholds in a chain (a list). Each threshold will be greater than the previous threshold, such that no
        threshold will be less than or equal to the chain's previous threshold. Note that we assume the function is passed in
        valid and nonconflicting minimum and maximum thresholds.
        """
        minThresh = minimumThresholds[0]
        maxThresh = maximumThresholds[0]
        if n == 1:
            for threshold in range(minThresh, maxThresh):
                yield [threshold]
        elif n > 1:
            minimumThresholds = minimumThresholds[1:]  # clip limiting threshold list so that next in line is available
            maximumThresholds = maximumThresholds[1:]  # for next threshold generator
            """ there should be a function called before this that ensures the max and mins do not conflict. """
            for threshold in range(minThresh, maxThresh):
                minimumThresholds[0] = max(minimumThresholds[0], threshold + 1)  # next threshold in list must be greater
                moreThresholds = self.dimensionless_thresholds_generator(n - 1, minimumThresholds, maximumThresholds)
                for otherThresholds in moreThresholds:
                    allThresholds = [threshold] + otherThresholds
                    yield allThresholds
        else:
            raise ValueError('# of dimensions should be > 0:' + str(n))


class OtsuFastThreshold(object):

    def load_image(self, im):
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
        hist = [int(h) for h in hist]
        histPyr, omegaPyr, muPyr = self.create_histogram_and_stats_pyramids(hist)
        self.histPyramid = histPyr
        self.omegaPyramid = omegaPyr
        self.muPyramid = muPyr
        
    def create_histogram_and_stats_pyramids(self, hist):
        """ expects hist to be a single list of numbers (no numpy array)
        """
        L = len(hist)
        reductions = int(math.log(L, 2))
        histPyramid = []
        omegaPyramid = []
        muPyramid = []
        for i in range(reductions):
            histPyramid.append(hist)
            reducedHist = [hist[i] + hist[i + 1] for i in range(0, L, 2)]
            hist = reducedHist  # collapse a list to half its size, combining the two collpased numbers into one
            L = L / 2  # update L to reflect the length of the new histogram
        for hist in histPyramid:
            omegas, mus, muT = self.calculate_omegas_and_mus_from_histogram(hist)
            omegaPyramid.append(omegas)
            muPyramid.append(mus)
        return histPyramid, omegaPyramid, muPyramid

    def calculate_omegas_and_mus_from_histogram(self, hist):
        probabilityLevels, meanLevels = self.calculate_histogram_pixel_stats(hist)
        L = len(probabilityLevels)
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

    def calculate_histogram_pixel_stats(self, hist):
        L = len(hist)  # L = number of intensity levels
        N = float(sum(hist))  # N = number of pixels in image
        probabilityLevels = [hist[i] / N for i in range(L)]  # percentage of pixels at each intensity level i
                # => P_i
        meanLevels = [i * probabilityLevels[i] for i in range(L)]  # mean level of pixels at intensity level i
        return probabilityLevels, meanLevels                            # => i * P_i

    def get(self):
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
            print('denom = 0')
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
    otsu2 = OtsuFastThreshold()
    otsu2.load_image(im)
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
    
