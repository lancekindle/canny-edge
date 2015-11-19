window.CanvImg = {};

/*call this function immediately. Attaches all the fxns below to CanvImg
 *object. Very similar to how RequireJS runs, but this emulates it closely
 *without requiring the library.
 */
(function(){
"use strict"; // causes all fxns defined herein to be optimized better

CanvImg.NUM_COLORS = 4;
CanvImg.ALPHA = 3;
CanvImg.BLANK = 0;
CanvImg.OPAQUE = 255;
CanvImg.KERNEL = {

    blur: [1, 1, 1,
           1, 1, 1,
           1, 1, 1],

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

//create, but do not add canvas to document. Keep it for creating a new image.
CanvImg._CANVAS = document.createElement('canvas');

CanvImg.new_image = function(im) {
    //create blank image with same dimensions as im
    var ctx = CanvImg._CANVAS.getContext('2d');
    var new_img = ctx.createImageData(im);
    return new_img;
}

CanvImg.draw_raw_img_on_canvas = function(canvas, raw_image) {
    /*This is used only once; to draw the img after being loaded from file.
     sizes canvas internally so that full image is displayed. However, the
     visual size of canvas within browser is not modified.
     */
    canvas.width = raw_image.width;
    canvas.height = raw_image.height;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(raw_image, 0, 0);

}

CanvImg.draw_img_on_canvas = function(canvas, image) {
    /*resizes canvas internally so that full image is displayed. However, the
     visual size of canvas within browser is not modified.
     use this fxn to draw any image that you've modified from the original.
     */
    canvas.width = image.width;
    canvas.height = image.height;
    var ctx = canvas.getContext('2d');
    ctx.putImageData(image, 0, 0);
}

CanvImg.get_canvas_img = function(canvas) {
    /*assumes that canvas.width & canvas.height have been set to dimensions of 
    loaded image. Will return the full image data
     */
    var ctx = canvas.getContext('2d');
    var w = canvas.width,
        h = canvas.height;
    return ctx.getImageData(0, 0, w, h);
}

CanvImg.copy_imgdata = function(src, dest) {
    // copy imgdata from src to dest by iterating over all indices
    var i;
    for (i=0; i < src.length; i++) {
        dest[i] = src[i];
    }
}

CanvImg.copy_image = function(img) {
    var copy = CanvImg.new_image(img);
    CanvImg.copy_imgdata(img.data, copy.data);
    return copy;
}

CanvImg.convolve = function(img, kernel, normalize) {
    /* convolve a kernel with an image, returning a new image with the same
     * dimensions post-convolution. Auto-normalizes values so that image is not
     * washed-out / faded. Overall resulting img should have ~ same luminosity
     * as original. However, if normalize parameter is defined, will divide all
     * pixel values by normalize, which can result in washed-out / faded
     * images.
     */
    var new_img = CanvImg.copy_image(img),
        ksqrt = Math.sqrt(kernel.length);
    if ((Math.round(ksqrt) != ksqrt) || (ksqrt % 2 == 0)) {
        console.log('kernel must be square, with odd-length sides like 3x3, 5x5');
    }
    if (normalize === undefined) {
        normalize = 0;
        kernel.forEach(function(num) {
            normalize += num;
        });
        // if normalize is auto-calculated as zero, then we reset to 1;
        // Otherwise normalize == 0 means image will become black & white
        if (normalize == 0) {
            normalize = 1;
        }
    }
    // neighbors == # depth of neighbors around kernel center. 3x3 = 1 neighbor
    var neighbors = (ksqrt - 1) / 2,
        k,
        x, y,
        nx, ny,
        xx, yy,
        p, pixel,
        b,
        out_of_y_bounds = [],
        out_of_x_bounds = [],
        out_of_bounds = false;
    // pre-calculate x and y indices that would be out of bounds
    for (b = 0; b <= neighbors; b++) {
        out_of_x_bounds[-1 - b] = true;
        out_of_x_bounds[img.width + b] = true;
        out_of_y_bounds[-1 -b] = true;
        out_of_y_bounds[img.height + b] = true;
    }
    for (x = 0; x < img.width; x++) {
        for (y = 0; y < img.height; y++) {
            pixel = 0;
            k = -1;  // index of kernel
            for (ny = -neighbors; ny <= neighbors; ny++) {
                yy = y + ny;
                out_of_bounds = out_of_y_bounds[yy];
                for (nx = -neighbors; nx <= neighbors; nx++) {
                    xx = x + nx;
                    if (out_of_bounds || out_of_x_bounds[xx]) {
                        p = CanvImg.get_pixel(img, x, y);
                    } else {
                        p = CanvImg.get_pixel(img, xx, yy);
                    }
                    pixel += p * kernel[++k];  //weight pixel value
                }
            }
            pixel /= normalize;  //prevents over/undersaturation of img
            CanvImg.set_pixel(new_img, x, y, pixel);
        }
    }
    return new_img;
}

CanvImg.get_pixel = function(img, x, y) {
    /* this assumes that img is now greyscale. Return Red component of pixel at
     * coordinates (x,y)
     */
    x *= CanvImg.NUM_COLORS;
    y *= CanvImg.NUM_COLORS * img.width;
    return img.data[x + y];
}

CanvImg.set_pixel = function(img, x, y, value) {
    // this assumes that img is now greyscale. Sets Red, Green, & Blue
    // components of pixel at coordinates (x,y) to value
    x *= CanvImg.NUM_COLORS;
    y *= CanvImg.NUM_COLORS * img.width;
    img.data[x + y] = value;
    img.data[x + 1 + y] = value;
    img.data[x + 2 + y] = value;
}

CanvImg.average_2_images = function(im1, im2) {
    /*average two images together into one image
     */
    var im = CanvImg.new_image(im1);
    var d1 = im1.data,
        d2 = im2.data,
        data = im.data,
        i;
    for (i = 0; i < data.length; i++) {
        data[i] = (d1[i] + d2[i]) / 2;
    }
    return im;
}

CanvImg.colorfly_combine_3_images = function(r, g, b) {
    /* combine 3 images together, using each image as a basis for colors r,g,b.
     * first image passed in will provide only red colors, second image provide
     * green colors, third image provides blue colors. It is assumed that the
     * passed in images are greyscale. If you pass in undefined as one of the
     * images, the corresponding color will not appear in the image.
     */
    var im;
    // create im from one of the undefined r, g, or b images
    if (r !== undefined) {
        im = CanvImg.new_image(r);
    } else if (g !== undefined) {
        im = CanvImg.new_image(g);
    } else {
        im = CanvImg.new_image(b);
    }
    CanvImg.strip_alpha_channel(im);
    // if any of the r, g, or b images are undefined, initialize them as an img
    if (r === undefined)
        r = CanvImg.new_image(im);
    if (g === undefined)
        g = CanvImg.new_image(im);
    if (b === undefined)
        b = CanvImg.new_image(im);
    var i;
    var pixel;
    for (i=0; i < im.data.length; i += CanvImg.NUM_COLORS) {
        if (r === undefined) {
            pixel = CanvImg.BLANK;
        } else {
            pixel = r.data[i];
        }
        im.data[i] = pixel;
        if (g === undefined) {
            pixel = CanvImg.BLANK;
        } else {
            pixel = g.data[i + 1];
        }
        im.data[i + 1] = pixel;
        if (b === undefined) {
            pixel = CanvImg.BLANK;
        } else {
            pixel = b.data[i + 2];
        }
        im.data[i + 2] = pixel;
    }
    return im;
}

CanvImg.set_pixel_color = function(img, x, y, color_indices, luminosity) {
    /* set a specific color-indices @ x, y to given luminosity. So [1], 255
     * would set the pixel at x,y to rgb values: (0, 255, 0).
     * [0,1], 128 would set the rbg values @x,y to (128, 128, 0)
     */
    x *= CanvImg.NUM_COLORS;
    y *= CanvImg.NUM_COLORS * img.width;
    color_indices.forEach(function(i) {
        if ((i == 0) || (i == 1) || (i ==2)) {
            img.data[x + y + i] = luminosity;
        } else {
            console.log('error: set_pixel_color accessed color outside rgb');
        }
    });
}

CanvImg.strip_alpha_channel = function(img) {
    // sets an image's alpha channel to opaque
    var i;
    for (i = CanvImg.ALPHA; i < img.data.length; i += CanvImg.NUM_COLORS) {
        img.data[i] = CanvImg.OPAQUE;
    }
}

CanvImg.get_greyscale = function(img) {
    // return a grayscaled copy of img
    var img = CanvImg.copy_image(img),
        data = img.data,
        scaling = [0.299, 0.587, 0.114],
        greyscale,
        r, g, b,
        i;
    for (i = 0; i < data.length; i += CanvImg.NUM_COLORS) {
         r = data[i + 0];
         g = data[i + 1];
         b = data[i + 2];
         greyscale = r * scaling[0] + g * scaling[1] + b * scaling[2];
         data[i + 0] = greyscale;
         data[i + 1] = greyscale;
         data[i + 2] = greyscale;
    }
    return img;
}

})();
