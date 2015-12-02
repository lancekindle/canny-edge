/* hold onto canny-edge finding related variables and functions
 */

Canny = {};

(function() {
"use strict";

Canny.calculate_edge_magnitude = function(x_edge, y_edge) {
    if (x_edge.length != y_edge.length) {
        console.log('uh oh. x_edge and y_edge are not same size for mag');
    }
    var magnitude = new Array(x_edge.length),
        length = x_edge.length,
        i, x, y,
        mag_squared;
    for (i = 0; i < length; i++) {
        x = x_edge[i];
        y = y_edge[i];
        mag_squared = Math.pow(x, 2) + Math.pow(y, 2);
        magnitude[i] = Math.sqrt(mag_squared);
     }
    return magnitude;
}

Canny.calculate_edge_angle = function(x_edge, y_edge) {
    /* calculate angle of edges, given edge strength in x and y. Returns angle
     * in degrees, 0 - 360.
     * Param x_edge: array representing gradient strength in X direction
     * Param y_edge: array representing gradient strength in Y direction
     * Return: array same length as x or y edge array, values 0-360
     */
    if (x_edge.length != y_edge.length) {
        console.log('uh oh. x_edge and y_edge are not same size for angle');
    }
    var angle = new Array(x_edge.length),
        radian_angle, degree_angle,
        length = x_edge.length,
        i, x, y;
    for (i = 0; i < length; i++) {
        x = x_edge[i];
        y = y_edge[i];
        radian_angle = Math.atan2(y, x); // -PI to PI
        degree_angle = (radian_angle + Math.PI) * 180 / Math.PI; // 0 to 360
        angle[i] = degree_angle;
     }
    return angle;
}

Canny.split_array_into_four_using_bidirectional_splitter = function(ref_img, array, splitter) {
    var NS = Canny.thin_img_array(ref_img, splitter.NS, splitter.NS_offset),
        WE = Canny.thin_img_array(ref_img, splitter.WE, splitter.WE_offset),
        NE_SW = Canny.thin_img_array(ref_img, splitter.NE_SW, splitter.NW_SW_offset),
        NW_SE = Canny.thin_img_array(ref_img, splitter.NW_SE, splitter.NW_SE_offset);
    var split_array = {
        NS: NS,
        WE: WE,
        NE_SW: NE_SW,
        NW_SE: NW_SE
    }
    return split_array;
}

Canny.get_array_xy_value = function(ref_img, array, x, y) {
    if ((x == -1) || (y == -1))
        return undefined;
    if ((x >= ref_img.width) || (y >= ref_img.height)) {
        return undefined;
    }
    return array[x + y * ref_img.height];
}

Canny.thin_img_array = function(ref_img, array, xy_offset) {
    var x_offset = xy_offset[0],
        y_offset = xy_offset[1],
        len = array.length,
        width = ref_img.width,
        height = ref_img.height,
        thinned = new Array(array.length),
        i, middle, x1, y1, x2, y2;
    thinned.fill(0);
    for (var y = 0; y < height; y++) {
        for (var x = 0; x < width; x++) {
            i = x + y * width;
            middle = array[i];
            x1 = x + x_offset;
            y1 = y + y_offset;
            x2 = x - x_offset;
            y2 = y - y_offset;
            pix_1 = Canny.get_array_xy_value(ref_img, array, x1, y1) || 0;
            pix_2 = Canny.get_array_xy_value(ref_img, array, x2, y2) || 0;
            if ((middle > pix1) && (middle >= pix2) {
                thinned[i] = middle;
            }
        }
    }
    return thinned;
}

Canny.get_bidirectional_splitter_from_angle = function(angle) {
    /*given an array of the angles in the image, categorize all angles as
     * corresponding to one of these four different bidirections: 
     * N-S, W-E, NE-SW, NW-SE. Angle values must be 0-360 or 0-180.
     * Return an object that holds the bidirectional indices as properties
     * named NS, WE, NE_SW, NW_SE
     */
    var degree,
        len = angle.length,
        NS = [],
        WE = [],
        NE_SW = [],
        NW_SE = [],
        BORDER = 45/2,
        NORTH_BORDER1 = 90 - BORDER,
        NORTH_BORDER2 = 90 + BORDER,
        WEST_BORDER = 180 - BORDER,
        EAST_BORDER = 0 + BORDER,
    for (var i = 0; i < len; i++) {
        degree = angle[i];
        degree %= 180;
        // subdivide angles
        if (degree > NORTH_BORDER1) {
            if (degree <= NORTH_BORDER2) {
                NS.push(i);
                continue;
            }
            if (degree > WEST_BORDER) {
                WE.push(i);
                continue;
            }
            NW_SE.push(i);
            continue;
        }
        if (degree <= EAST_BORDER) {
            WE.push(i);
            continue;
        }
        NE_SW.push(i);
        continue;
    }
    var angle_indices = {
        NS: NS,
        WE: WE,
        NE_SW: NE_SW,
        NW_SE: NW_SE,
        // offset = x, y direction (+ or -) in which these edges have neighbors
        NS_offset: [0, 1],
        WE_offset: [1, 0],
        NE_SW_offset: [1, 1],
        NW_SE_offset: [-1, 1]
    }
    return angle_indices;
}

Canny.scale_array_0_to_255 = function(array) {
    /*scale full array to have a minimum value of 0, and a max value of 255.
     * Generally useful to re-constrain an array to 0-255 for an image.
     */
    var minmax = Canny.find_min_and_max_values_of_array(array);
    var min = minmax[0],
        max = minmax[1] - min,
        val;
    for (var i = 0; i < array.length; i++){
        val = array[i];
        val -= min;
        val *= (255/max);
        array[i] = val;
    }
    return array;
}

Canny.find_min_and_max_values_of_array = function(array) {
    var val,
        min = 255,
        max = 0;
    for (var i = 0; i < array.length; i++) {
        val = array[i];
        if (val < min) {
            min = val;
        }
        if (val > max) {
            max = val;
        }
    }
    var minmax = {
        min: min,
        max: max,
        0: min,
        1: max
    }
    return minmax;
}

Canny.KERNEL = {

    sobel_y: [-1, -2, -1,
               0,  0,  0,
              +1, +2, +1],

    sobel_x: [-1, 0, +1,
              -2, 0, +2,
              -1, 0, +1],

    sobel_y_reverse: [+1, +2, +1,
                       0,  0,  0,
                      -1, -2, -1],

    sobel_x_reverse: [+1, 0, -1,
                      +2, 0, -2,
                      +1, 0, -1],

    gaussian: [2,  4,  5,  4, 2,
               4,  9, 12,  9, 4,
               5, 12, 15, 12, 5,
               2,  4,  5,  4, 2,
               4,  9, 12,  9, 4],
};

Canny.convolve = function(img_array, kernel, ref_img, normalize) {
    /* Convolve img_array (array representing an image) with kernel, producing
     * an output array of same length as img_array. Output values will be
     * automatically divided by the sum of the kernel, which keeps the average
     * value of the output array equal to the average value of the input array.
     * This means that the corresponding images to both arrays would have equal
     * brightness. The values in the output array can be positive and negative
     * integer and decimal values.
     *- 
      * Param img_array: input img array whose values each represent a different
     *   pixel value. You can get a compatible img_array by passing an image
     *   into CanvImg.create_arrays_from_image(img); You will get back a
     *   4-tuple of arrays, representing the colors Red, Green, Blue, and
     *   Alpha, respectively. Choose one of those arrays to pass into here.
     *-
     * Param kernel: kernel from Canny.KERNEL, a 3x3 or 5x5 kernel that'll be
     *   convolved with the input image
     *-
     * Param reference_img: used to get width & height of source image.
     *   Since the arrays are all one-dimensional, we need to know the
     *   dimensions of source image in order to correctly convolve image.
     *-
     * Param normalize: an optional parameter to use in diving each pixel,
     *   rather than the sum of the kernel. If normalize > sum(kernel), the
     *   output array will have smaller values (and it's corresponding image
     *   would be darker). If normalize < sum(kernel): bigger value & brighter
     *   image.
     */
    var width = ref_img.width,
        height = ref_img.height,
        output_array = new Array(width * height),
        ksqrt = Math.sqrt(kernel.length);
    if ((Math.round(ksqrt) != ksqrt) || (ksqrt % 2 == 0)) {
        console.log('kernel must be square, with odd-length sides like 3x3, 5x5');
    }
    if (normalize === undefined) {
        normalize = 0;
        kernel.forEach(function(num) {
            normalize += num;
        });
        // edge-finding kernels can have a net sum of 0, in which case we want
        // to divide by 1, not 0 (as zero would cause the output image to
         // effectively be Black and White, rather than the desired greyscale.
        if (normalize == 0) {
            normalize = 1;
        }
    }
    // neighbors == # depth of neighbors around kernel center. 3x3 = 1 neighbor
    var neighbors = (ksqrt - 1) / 2,
        k,
        xx, yy,
        p, pixel,
        out_of_y_bounds = [],
        out_of_x_bounds = [],
        out_of_bounds = false;

    // pre-calculate x and y indices that would be out of bounds
    for (var b = 0; b <= neighbors; b++) {
        out_of_x_bounds[-1 - b] = true;
        out_of_x_bounds[width + b] = true;
        out_of_y_bounds[-1 -b] = true;
        out_of_y_bounds[height + b] = true;
    }
    for (var y = 0; y < height; y++) {
        for (var x = 0; x < width; x++) {
            pixel = 0;
            k = -1;  // index of kernel
            for (var ny = -neighbors; ny <= neighbors; ny++) {
                yy = y + ny;
                out_of_bounds = out_of_y_bounds[yy];
                for (var nx = -neighbors; nx <= neighbors; nx++) {
                    xx = x + nx;
                    // if desired pixel is outside border of image, use pixel
                    // at center of kernel, instead. (probably not ideal)
                    if (out_of_bounds || out_of_x_bounds[xx]) {
                        p = img_array[x + y * width];
                    } else {
                        p = img_array[xx + yy * width];
                    }
                    pixel += p * kernel[++k];
                }
            }
            pixel /= normalize; //prevents over/undersaturation of img
            output_array[x + y * width] = pixel;
        }
    }
    return output_array;
}

})();

